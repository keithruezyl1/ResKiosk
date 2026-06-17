"""
hub/retrieval/outcomes.py

Stable outcome / fallback reason codes for query pipeline logging (RK-55).

These constants are the single source of truth for the values written to
``query_logs.fallback_reason``. They match the enum documented in the schema:

    no_results | low_confidence | validation_blocked | retrieval_error | rewrite_error

A "fallback" is any pipeline exit that did not produce a clean, grounded answer.
A clean ``DIRECT_MATCH`` and a clarification pause (``NEEDS_CLARIFICATION``) are
NOT fallbacks — they leave ``fallback_reason`` null.
"""

from __future__ import annotations

from typing import Optional

# ── fallback_reason codes ────────────────────────────────────────────────────
FALLBACK_NO_RESULTS = "no_results"
FALLBACK_LOW_CONFIDENCE = "low_confidence"
FALLBACK_VALIDATION_BLOCKED = "validation_blocked"
FALLBACK_RETRIEVAL_ERROR = "retrieval_error"
FALLBACK_REWRITE_ERROR = "rewrite_error"

ALL_FALLBACK_REASONS = frozenset(
    {
        FALLBACK_NO_RESULTS,
        FALLBACK_LOW_CONFIDENCE,
        FALLBACK_VALIDATION_BLOCKED,
        FALLBACK_RETRIEVAL_ERROR,
        FALLBACK_REWRITE_ERROR,
    }
)

# Answer types that represent a clean (non-fallback) outcome.
_CLEAN_ANSWER_TYPES = frozenset({"DIRECT_MATCH", "NEEDS_CLARIFICATION"})


def classify_fallback_reason(result: Optional[dict]) -> Optional[str]:
    """Map a retrieval result dict to a fallback reason code.

    Returns ``None`` for a clean answer (direct match) or a clarification pause.
    For a non-match, distinguishes ``low_confidence`` (a candidate was scored but
    fell below threshold) from ``no_results`` (nothing to score).

    This does not classify exception-driven outcomes (``retrieval_error`` /
    ``rewrite_error``) — those are set explicitly by the caller that caught the
    exception, because a result dict alone cannot reveal that a stage raised.
    """
    if not result:
        return FALLBACK_NO_RESULTS

    answer_type = result.get("answer_type")
    if answer_type in _CLEAN_ANSWER_TYPES:
        return None

    # Non-clean outcome (e.g. NO_MATCH). Prefer the raw cosine score when present
    # so a below-threshold candidate is distinguishable from an empty candidate set.
    score = result.get("confidence_raw")
    if score is None:
        score = result.get("confidence")
    try:
        score = float(score) if score is not None else 0.0
    except (TypeError, ValueError):
        score = 0.0

    return FALLBACK_LOW_CONFIDENCE if score > 0.0 else FALLBACK_NO_RESULTS
