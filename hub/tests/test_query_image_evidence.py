"""
hub/tests/test_query_image_evidence.py

Phase 9 / Slice 7C — /query returns image evidence alongside the text answer
(S7C.6), additive and fail-safe. search.retrieve_images is patched (no CLIP).
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
from hub.retrieval import response_cache
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
    base = dict(center_id="c1", kiosk_id="k1", transcript_original="show me the andres bonifacio building",
                language="en", kb_version=1)
    base.update(kw)
    return api_models.QueryRequest(**base)


class TestQueryImageEvidence(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        response_cache.invalidate_response_cache()

    def tearDown(self):
        self.db.close()
        response_cache.invalidate_response_cache()

    def _pipeline(self):
        return PipelineResult(normalized_text="show me the andres bonifacio building", intent="location",
                              intent_confidence=0.6, pipeline_status="completed",
                              stage_log=["normalize", "intent"], stage_latency={})

    def _dm(self):
        return {"answer_type": "DIRECT_MATCH", "confidence": 0.8, "answer_text": "It's near the gate.",
                "source_id": 1, "article_data": {"answer": "It's near the gate."}, "intent": "location",
                "fusion_top_k_ids": [1]}

    def test_image_evidence_attached(self):
        imgs = [{"source_id": 11, "image_asset_id": 5, "score": 0.41, "rank": 1,
                 "modality": "image", "render_ref": "/assets/5/display"}]
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="It's near the gate."), \
             patch("hub.api.routes_query.search.retrieve_images", return_value=imgs):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))

        self.assertIsNotNone(resp.image_evidence)
        self.assertEqual(resp.image_evidence[0].source_id, 11)
        self.assertEqual(resp.image_evidence[0].modality, "image")
        self.assertEqual(resp.image_evidence[0].render_ref, "/assets/5/display")
        # also captured in the query_logs final_evidence
        row = self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.desc()).first()
        self.assertIn("image_evidence", row.final_evidence)
        self.assertEqual(json.loads(row.final_evidence)["image_evidence"][0]["source_id"], 11)

    def test_image_primary_when_top_score_high(self):
        imgs = [{"source_id": 11, "image_asset_id": 5, "score": 0.42, "rank": 1,
                 "modality": "image", "render_ref": "/assets/5/display"}]
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.search.retrieve_images", return_value=imgs):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertTrue(resp.image_primary)  # 0.42 >= IMAGE_PRIMARY_FLOOR (0.30)

    def test_image_tentative_when_low_score(self):
        imgs = [{"source_id": 11, "image_asset_id": 5, "score": 0.27, "rank": 1,
                 "modality": "image", "render_ref": "/assets/5/display"}]
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.search.retrieve_images", return_value=imgs):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertIsNotNone(resp.image_evidence)   # shown...
        self.assertFalse(resp.image_primary)         # ...but not authoritative (0.27 < 0.30)

    def test_no_image_evidence_when_none(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.search.retrieve_images", return_value=[]):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertIsNone(resp.image_evidence)

    def test_image_failure_does_not_break_answer(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()), \
             patch("hub.api.routes_query.formatter.format_response", return_value="ok"), \
             patch("hub.api.routes_query.search.retrieve_images", side_effect=RuntimeError("clip down")):
            P.return_value.run.return_value = self._pipeline()
            resp = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertEqual(resp.answer_type, "DIRECT_MATCH")  # text answer intact
        self.assertIsNone(resp.image_evidence)


if __name__ == "__main__":
    unittest.main()
