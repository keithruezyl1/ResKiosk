"""
hub/tests/test_latency_logging.py

Phase 5 S6A.2 + S6A.3 — per-stage latency breakdown + final-evidence stability.
"""

import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.models import api_models
from hub.api import routes_query
from hub.retrieval.pipeline import QueryPipeline, PipelineResult, STAGE_RETRIEVE


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())


def _req(**kw):
    base = dict(center_id="c1", kiosk_id="k1", transcript_original="where is food", language="en", kb_version=1)
    base.update(kw)
    return api_models.QueryRequest(**base)


class TestPipelineStageLatency(unittest.TestCase):
    def test_stage_latency_populated(self):
        nm = {"answer_type": "NO_MATCH", "confidence": 0.0}
        with patch("hub.retrieval.search.retrieve", return_value=nm), patch(
            "hub.retrieval.rewriter.maybe_rewrite", side_effect=lambda q, *a, **k: q
        ):
            res = QueryPipeline().run(MagicMock(), "hello", False)
        self.assertIn(STAGE_RETRIEVE, res.stage_latency)
        self.assertGreaterEqual(res.stage_latency[STAGE_RETRIEVE], 0.0)
        self.assertIn("clarification_gate", res.stage_latency)


class TestRouteLatencyAndEvidence(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()

    def tearDown(self):
        self.db.close()

    def _last(self):
        return self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.desc()).first()

    def _pipeline(self):
        return PipelineResult(
            normalized_text="where is food", intent="food", intent_confidence=0.6,
            pipeline_status="completed", stage_log=["normalize", "intent", "retrieve", "clarification_gate", "rewrite"],
            stage_latency={"retrieve": 4.5, "clarification_gate": 0.2, "rewrite": 1.1},
        )

    def _dm(self):
        return {"answer_type": "DIRECT_MATCH", "confidence": 0.9, "answer_text": "Food is in Hall A.",
                "source_id": 7, "article_data": {"answer": "Food is in Hall A."},
                "fusion_top_k_ids": [7, 3, 9]}

    def test_latency_and_final_evidence_logged(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="Food is in Hall A."):
            P.return_value.run.return_value = self._pipeline()
            _run(routes_query.submit_query(_req(), db=self.db))
        row = self._last()
        self.assertIsNotNone(row.retrieve_ms)           # route-measured retrieval time
        self.assertEqual(row.rewrite_ms, 1.1)           # from pipeline stage_latency
        self.assertEqual(row.clarification_ms, 0.2)
        fe = json.loads(row.final_evidence)
        self.assertEqual(fe["primary_source_id"], 7)
        self.assertEqual(fe["top_k_ids"], [7, 3, 9])

    def test_final_evidence_stable_across_runs(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="Food is in Hall A."):
            P.return_value.run.return_value = self._pipeline()
            _run(routes_query.submit_query(_req(), db=self.db))
            _run(routes_query.submit_query(_req(), db=self.db))
        rows = self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.asc()).all()
        self.assertEqual(rows[0].final_evidence, rows[1].final_evidence)


if __name__ == "__main__":
    unittest.main()
