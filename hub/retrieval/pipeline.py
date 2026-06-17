"""
hub/retrieval/pipeline.py

Canonical query pipeline for the ResKiosk hub.

Enforced stage order:
  1. normalize
  2. intent classification
  3. retrieve (first pass)
  4. clarification gate — STOP here if NEEDS_CLARIFICATION
  5. rewrite (only if clarification not needed)
  6. retrieve (second pass, only if rewrite produced a different query)

The pipeline returns a PipelineResult. The route handler is responsible for
translation (pre/post pipeline), LLM response formatting, logging, and
session history — none of that belongs here.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from hub.retrieval.normalizer import normalize_query
from hub.retrieval import search
from hub.retrieval import rewriter as query_rewriter
from hub.retrieval import outcomes

logger = logging.getLogger(__name__)

# Sentinel used by tests to verify stage log entries.
STAGE_NORMALIZE = "normalize"
STAGE_INTENT = "intent"
STAGE_RETRIEVE = "retrieve"
STAGE_CLARIFICATION_GATE = "clarification_gate"
STAGE_REWRITE = "rewrite"
STAGE_RETRIEVE_RETRY = "retrieve_retry"


@dataclass
class PipelineResult:
    """
    Carries all outputs produced by the pipeline run.

    stage_log is an ordered list of stage name constants that were executed.
    Consumers (and tests) can inspect this list to assert that stages ran in
    the correct order and that prohibited stages were skipped.
    """

    # The normalized English query text sent to the first retrieval pass.
    normalized_text: str = ""

    # Intent classification results.
    intent: str = "unclear"
    intent_confidence: float = 0.0

    # The retrieval result dict (from search.retrieve).
    retrieve_result: dict = field(default_factory=dict)

    # Rewrite state.
    rewrite_happened: bool = False
    rewritten_text: Optional[str] = None

    # Ordered record of pipeline stages that executed.
    stage_log: List[str] = field(default_factory=list)

    # Pipeline status: "completed" for normal flow, "paused" when clarification needed.
    pipeline_status: str = "completed"

    # Clarification gate outputs — populated regardless of whether clarification fired.
    clarification_triggered: bool = False
    clarification_trigger_reason: str = "not_triggered"

    # Failure / fallback outcome logging (RK-55). Both null on a clean answer or
    # a clarification pause. fallback_reason uses hub.retrieval.outcomes constants;
    # failed_stage names the stage that raised (a STAGE_* constant) when one did.
    fallback_reason: Optional[str] = None
    failed_stage: Optional[str] = None

    # Phase 5 / Slice 6A — per-stage latency breakdown in milliseconds.
    # Keys are STAGE_* constants; only stages that ran are present.
    stage_latency: dict = field(default_factory=dict)


class QueryPipeline:
    """
    Orchestrates the canonical hub query processing pipeline.

    Usage:
        pipeline = QueryPipeline()
        result = pipeline.run(db, text_en, is_retry, selected_category, exclude_source_ids, query_language)
    """

    def run(
        self,
        db: Session,
        text_en: str,
        is_retry: bool,
        selected_category: Optional[str] = None,
        exclude_source_ids: Optional[List[int]] = None,
        query_language: str = "en",
    ) -> PipelineResult:
        """
        Run the canonical pipeline and return a PipelineResult.

        Stage order is strictly:
          normalize → intent → retrieve → clarification_gate → rewrite → retrieve_retry
        """
        result = PipelineResult()

        # ── Stage 1: Normalize ────────────────────────────────────────────────
        result.stage_log.append(STAGE_NORMALIZE)
        normalized = normalize_query(text_en, query_language)
        result.normalized_text = normalized
        logger.info(f"[Pipeline] {STAGE_NORMALIZE}: normalized='{normalized[:120]}'")

        # ── Stage 2: Intent ───────────────────────────────────────────────────
        # Intent classification is surfaced here so it can be logged and tested
        # independently of the retrieval internals.  search.retrieve() will
        # also run intent internally (it has its own classifier reference),
        # which is intentional — we do not strip intent from retrieve() this
        # increment to keep the scope bounded.
        result.stage_log.append(STAGE_INTENT)
        intent, intent_confidence = self._classify_intent(normalized)
        result.intent = intent
        result.intent_confidence = intent_confidence
        logger.info(
            f"[Pipeline] {STAGE_INTENT}: intent={intent} confidence={intent_confidence:.4f}"
        )

        # ── Stage 3: Retrieve (first pass) ───────────────────────────────────
        result.stage_log.append(STAGE_RETRIEVE)
        _t_retrieve = time.perf_counter()
        try:
            retrieve_result = search.retrieve(
                db,
                normalized,
                is_retry,
                selected_category=selected_category,
                exclude_source_ids=exclude_source_ids,
                query_language=query_language,
            )
        except Exception as e:
            logger.error(f"[Pipeline] Retrieval error: {e}")
            retrieve_result = _fallback_no_match(intent, intent_confidence)
            result.failed_stage = STAGE_RETRIEVE
            result.fallback_reason = outcomes.FALLBACK_RETRIEVAL_ERROR
        result.stage_latency[STAGE_RETRIEVE] = round((time.perf_counter() - _t_retrieve) * 1000, 3)
        result.retrieve_result = retrieve_result
        logger.info(
            f"[Pipeline] {STAGE_RETRIEVE}: answer_type={retrieve_result.get('answer_type')} "
            f"source_id={retrieve_result.get('source_id')} "
            f"confidence={retrieve_result.get('confidence', 0.0):.4f}"
        )

        # ── Stage 4: Clarification gate ───────────────────────────────────────
        # If retrieval determined clarification is needed, we stop here.
        # Rewrite MUST NOT run, and no second retrieval pass occurs.
        result.stage_log.append(STAGE_CLARIFICATION_GATE)
        _t_gate = time.perf_counter()
        trigger_reason = retrieve_result.get("clarification_trigger_reason", "not_triggered")
        if retrieve_result.get("answer_type") == "NEEDS_CLARIFICATION":
            result.pipeline_status = "paused"
            result.clarification_triggered = True
            result.clarification_trigger_reason = trigger_reason
            result.stage_latency[STAGE_CLARIFICATION_GATE] = round((time.perf_counter() - _t_gate) * 1000, 3)
            logger.info(
                f"[Pipeline] {STAGE_CLARIFICATION_GATE}: clarification_triggered=True "
                f"trigger_reason={trigger_reason} pipeline_status=paused "
                f"categories={retrieve_result.get('categories')}"
            )
            return result
        result.clarification_triggered = False
        result.clarification_trigger_reason = trigger_reason
        result.stage_latency[STAGE_CLARIFICATION_GATE] = round((time.perf_counter() - _t_gate) * 1000, 3)
        logger.info(
            f"[Pipeline] {STAGE_CLARIFICATION_GATE}: clarification_triggered=False "
            f"trigger_reason={trigger_reason}"
        )

        # ── Stage 5: Rewrite (only if clarification not needed) ──────────────
        result.stage_log.append(STAGE_REWRITE)
        _t_rewrite = time.perf_counter()
        candidate = query_rewriter.maybe_rewrite(
            normalized,
            retrieve_result.get("intent", intent),
            retrieve_result.get("confidence", 0.0),
        )
        result.stage_latency[STAGE_REWRITE] = round((time.perf_counter() - _t_rewrite) * 1000, 3)
        rewrite_happened = candidate != normalized
        result.rewritten_text = candidate if rewrite_happened else None
        result.rewrite_happened = rewrite_happened
        logger.info(
            f"[Pipeline] {STAGE_REWRITE}: rewrite_applied={rewrite_happened}"
            + (f" rewritten='{candidate[:120]}'" if rewrite_happened else "")
        )

        # ── Stage 6: Retrieve (retry after rewrite) ───────────────────────────
        if rewrite_happened:
            result.stage_log.append(STAGE_RETRIEVE_RETRY)
            try:
                retry_result = search.retrieve(
                    db,
                    candidate,
                    False,
                    selected_category=None,
                    exclude_source_ids=exclude_source_ids,
                    query_language=query_language,
                )
                logger.info(
                    f"[Pipeline] {STAGE_RETRIEVE_RETRY}: answer_type={retry_result.get('answer_type')} "
                    f"source_id={retry_result.get('source_id')} "
                    f"confidence={retry_result.get('confidence', 0.0):.4f}"
                )
                result.retrieve_result = retry_result
            except Exception as e:
                logger.warning(f"[Pipeline] Rewrite retry failed: {e}")
                # Keep the original retrieve_result on failure.
                result.failed_stage = STAGE_RETRIEVE_RETRY
                result.fallback_reason = outcomes.FALLBACK_REWRITE_ERROR

        # Classify the non-error outcome (no_results / low_confidence / clean) for
        # logging. An error reason set above takes precedence and is preserved.
        if result.fallback_reason is None:
            result.fallback_reason = outcomes.classify_fallback_reason(result.retrieve_result)

        return result

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _classify_intent(normalized_query: str):
        """
        Attempt intent classification using the search module's singleton
        classifier. Returns (intent, confidence). Degrades gracefully when
        no classifier is loaded.
        """
        classifier = search._intent_classifier  # type: ignore[attr-defined]
        if classifier is None:
            return "unclear", 0.0
        try:
            if hasattr(classifier, "classify_top2"):
                intent, conf, _, _ = classifier.classify_top2(normalized_query)
            else:
                intent, conf = classifier.classify(normalized_query)
            return intent, float(conf)
        except Exception as e:
            logger.warning(f"[Pipeline] Intent classification failed: {e}")
            return "unclear", 0.0


def _fallback_no_match(intent: str, intent_confidence: float) -> dict:
    return {
        "answer_text": (
            "I am here to answer questions about registration, food, medical help, "
            "sleeping areas, transportation, safety, and other services in this shelter. "
            "Please ask about one of these topics or see a volunteer for more help."
        ),
        "answer_type": "NO_MATCH",
        "confidence": 0.0,
        "source_id": None,
        "categories": None,
        "article_data": None,
        "intent": intent,
        "intent_confidence": intent_confidence,
    }
