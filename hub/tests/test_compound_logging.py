"""
hub/tests/test_compound_logging.py

Phase 4 S5.6 + S5.7 — compound query response outputs (secondary evidence,
SOS offer) and compound lifecycle logging on /query.
"""

import asyncio
import json
import unittest
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.models import api_models
from hub.api import routes_query
from hub.retrieval.pipeline import PipelineResult


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())


def _req(**kw):
    base = dict(center_id="c1", kiosk_id="k1", transcript_original="i have a fever, where is the clinic", language="en", kb_version=1)
    base.update(kw)
    return api_models.QueryRequest(**base)


class TestCompoundRouteIntegration(unittest.TestCase):
    def setUp(self):
        self.db = sessionmaker(bind=self._engine())()

    def _engine(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        return e

    def tearDown(self):
        self.db.close()

    def _last_log(self):
        return self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.desc()).first()

    def _pipeline(self):
        return PipelineResult(normalized_text="i have a fever where is the clinic", intent="medical",
                              intent_confidence=0.5, pipeline_status="completed",
                              stage_log=["normalize", "intent", "retrieve", "clarification_gate"])

    def _compound_result(self):
        return {
            "answer_type": "DIRECT_MATCH", "confidence": 0.8,
            "answer_text": "The medical station is in Hall A.",
            "source_id": 1, "article_data": {"answer": "The medical station is in Hall A."},
            "intent": "medical", "is_compound": True,
            "follow_up_intent": "location", "follow_up_prompt": "Do you also want directions?",
        }

    def test_compound_populates_secondary_evidence_and_log(self):
        compound_out = {
            "secondary_evidence": {"intent": "location", "source_id": 2, "answer_text": "Go to building B.", "confidence": 0.031},
            "sos_offered": False,
            "compound_paths": {"primary_intent": "medical", "secondary_intent": "location",
                               "paths": [{"intent": "medical", "priority": 90}, {"intent": "location", "priority": 10}],
                               "merged": [{"article_id": 1, "primary_intent": "medical", "priority": 90, "merged_rank": 1, "rrf_score": 0.016, "memberships": [{"intent": "medical", "path_rank": 1}]}]},
        }
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._compound_result()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="The medical station is in Hall A."), \
             patch("hub.api.routes_query.formatter.generate_follow_up_prompt", return_value="Do you also want directions?"), \
             patch("hub.api.routes_query.search.build_compound_outputs", return_value=compound_out):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))

        self.assertIsNotNone(resp.secondary_evidence)
        self.assertEqual(resp.secondary_evidence.source_id, 2)
        self.assertEqual(resp.secondary_evidence.intent, "location")
        self.assertFalse(resp.sos_offered)

        row = self._last_log()
        self.assertTrue(row.compound_detected)
        self.assertIn("merged", row.compound_paths)
        self.assertEqual(json.loads(row.compound_paths)["primary_intent"], "medical")

    def test_sos_offered_propagates(self):
        compound_out = {"secondary_evidence": None, "sos_offered": True, "compound_paths": {"paths": []}}
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._compound_result()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.formatter.generate_follow_up_prompt", return_value="more?"), \
             patch("hub.api.routes_query.search.build_compound_outputs", return_value=compound_out):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertTrue(resp.sos_offered)

    def test_non_compound_leaves_fields_null(self):
        non_compound = dict(self._compound_result(), is_compound=False, follow_up_intent=None, follow_up_prompt=None)
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=non_compound), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.search.build_compound_outputs") as bco:
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertIsNone(resp.secondary_evidence)
        self.assertFalse(resp.sos_offered)
        bco.assert_not_called()  # multi-path not invoked for non-compound
        row = self._last_log()
        self.assertFalse(row.compound_detected)


if __name__ == "__main__":
    unittest.main()
