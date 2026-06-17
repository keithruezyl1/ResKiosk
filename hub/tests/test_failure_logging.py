"""
hub/tests/test_failure_logging.py

RK-55 — failure and fallback outcome logging (Goal 10).

Verifies that:
  - outcomes.classify_fallback_reason maps results to the correct reason codes.
  - QueryPipeline surfaces failed_stage + fallback_reason on retrieval/rewrite errors
    and classifies clean / no-match outcomes.
  - /query persists fallback_reason + failed_stage for every non-clarification path,
    including a partial row written from the outer exception handler.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.models import api_models
from hub.api import routes_query
from hub.retrieval import outcomes
from hub.retrieval.pipeline import QueryPipeline, PipelineResult


def _make_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _req(**kw):
    base = dict(
        center_id="c1",
        kiosk_id="k1",
        transcript_original="hello",
        language="en",
        kb_version=1,
    )
    base.update(kw)
    return api_models.QueryRequest(**base)


def _run(coro):
    # Use a dedicated loop and leave a fresh, open loop installed afterwards.
    # asyncio.run() would close the loop and leave no current loop, which breaks
    # sibling tests that still use asyncio.get_event_loop().
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())


# ---------------------------------------------------------------------------
# Unit — classify_fallback_reason
# ---------------------------------------------------------------------------


class TestClassifyFallbackReason(unittest.TestCase):
    def test_direct_match_is_clean(self):
        self.assertIsNone(outcomes.classify_fallback_reason({"answer_type": "DIRECT_MATCH", "confidence": 0.9}))

    def test_clarification_is_clean(self):
        self.assertIsNone(
            outcomes.classify_fallback_reason({"answer_type": "NEEDS_CLARIFICATION", "confidence": 0.1})
        )

    def test_no_match_zero_score_is_no_results(self):
        self.assertEqual(
            outcomes.classify_fallback_reason({"answer_type": "NO_MATCH", "confidence": 0.0}),
            outcomes.FALLBACK_NO_RESULTS,
        )

    def test_no_match_with_score_is_low_confidence(self):
        self.assertEqual(
            outcomes.classify_fallback_reason({"answer_type": "NO_MATCH", "confidence": 0.42}),
            outcomes.FALLBACK_LOW_CONFIDENCE,
        )

    def test_confidence_raw_preferred(self):
        self.assertEqual(
            outcomes.classify_fallback_reason(
                {"answer_type": "NO_MATCH", "confidence": 0.0, "confidence_raw": 0.6}
            ),
            outcomes.FALLBACK_LOW_CONFIDENCE,
        )

    def test_empty_result_is_no_results(self):
        self.assertEqual(outcomes.classify_fallback_reason(None), outcomes.FALLBACK_NO_RESULTS)
        self.assertEqual(outcomes.classify_fallback_reason({}), outcomes.FALLBACK_NO_RESULTS)


# ---------------------------------------------------------------------------
# Pipeline — failed_stage / fallback_reason surfacing
# ---------------------------------------------------------------------------


class TestPipelineFailureSurfacing(unittest.TestCase):
    def test_retrieval_error_sets_retrieve_stage(self):
        with patch("hub.retrieval.search.retrieve", side_effect=RuntimeError("boom")), patch(
            "hub.retrieval.rewriter.maybe_rewrite", side_effect=lambda q, *a, **k: q
        ):
            res = QueryPipeline().run(MagicMock(), "hello", False)
        self.assertEqual(res.failed_stage, "retrieve")
        self.assertEqual(res.fallback_reason, outcomes.FALLBACK_RETRIEVAL_ERROR)

    def test_rewrite_retry_error_sets_retry_stage(self):
        first = {"answer_type": "DIRECT_MATCH", "confidence": 0.9, "intent": "food", "source_id": 1}
        with patch("hub.retrieval.search.retrieve", side_effect=[first, RuntimeError("boom")]), patch(
            "hub.retrieval.rewriter.maybe_rewrite", return_value="a different query"
        ):
            res = QueryPipeline().run(MagicMock(), "hello", False)
        self.assertEqual(res.failed_stage, "retrieve_retry")
        self.assertEqual(res.fallback_reason, outcomes.FALLBACK_REWRITE_ERROR)

    def test_clean_no_match_classifies_no_results(self):
        nm = {"answer_type": "NO_MATCH", "confidence": 0.0}
        with patch("hub.retrieval.search.retrieve", return_value=nm), patch(
            "hub.retrieval.rewriter.maybe_rewrite", side_effect=lambda q, *a, **k: q
        ):
            res = QueryPipeline().run(MagicMock(), "hello", False)
        self.assertIsNone(res.failed_stage)
        self.assertEqual(res.fallback_reason, outcomes.FALLBACK_NO_RESULTS)


# ---------------------------------------------------------------------------
# Route — /query persists the fields + always writes a row
# ---------------------------------------------------------------------------


class TestQueryRouteFailureLogging(unittest.TestCase):
    def setUp(self):
        self.db = _make_db()

    def tearDown(self):
        self.db.close()

    def _last_log(self):
        return self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.desc()).first()

    def _completed_pipeline(self):
        return PipelineResult(
            normalized_text="hello",
            intent="food",
            intent_confidence=0.5,
            pipeline_status="completed",
            stage_log=["normalize", "intent", "retrieve", "clarification_gate"],
        )

    def test_retrieval_error_logs_retrieval_error(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, patch(
            "hub.api.routes_query.search.retrieve", side_effect=RuntimeError("boom")
        ):
            P.return_value.run.return_value = self._completed_pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertEqual(resp.answer_type, "NO_MATCH")
        row = self._last_log()
        self.assertIsNotNone(row)
        self.assertEqual(row.fallback_reason, outcomes.FALLBACK_RETRIEVAL_ERROR)
        self.assertEqual(row.failed_stage, "retrieve")

    def test_no_match_logs_no_results(self):
        nm = {"answer_type": "NO_MATCH", "confidence": 0.0, "answer_text": "no", "source_id": None}
        with patch("hub.api.routes_query.QueryPipeline") as P, patch(
            "hub.api.routes_query.search.retrieve", return_value=nm
        ):
            P.return_value.run.return_value = self._completed_pipeline()
            _run(routes_query.submit_query(_req(), db=self.db))
        row = self._last_log()
        self.assertEqual(row.fallback_reason, outcomes.FALLBACK_NO_RESULTS)
        self.assertIsNone(row.failed_stage)

    def test_direct_match_logs_no_fallback(self):
        dm = {
            "answer_type": "DIRECT_MATCH",
            "confidence": 0.92,
            "answer_text": "Registration is at the front desk.",
            "source_id": 1,
            "article_data": {"answer": "Registration is at the front desk."},
        }
        with patch("hub.api.routes_query.QueryPipeline") as P, patch(
            "hub.api.routes_query.search.retrieve", return_value=dm
        ), patch("hub.api.routes_query.formatter.format_response", return_value="Registration is at the front desk."):
            P.return_value.run.return_value = self._completed_pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertEqual(resp.answer_type, "DIRECT_MATCH")
        row = self._last_log()
        self.assertIsNone(row.fallback_reason)
        self.assertIsNone(row.failed_stage)

    def test_outer_exception_writes_partial_row(self):
        with patch("hub.api.routes_query.QueryPipeline") as P:
            P.return_value.run.side_effect = RuntimeError("pipeline exploded")
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertEqual(resp.answer_type, "NO_MATCH")
        row = self._last_log()
        self.assertIsNotNone(row, "a partial row must be written even on hard failure")
        self.assertEqual(row.failed_stage, "unknown")
        self.assertEqual(row.fallback_reason, outcomes.FALLBACK_RETRIEVAL_ERROR)


if __name__ == "__main__":
    unittest.main()
