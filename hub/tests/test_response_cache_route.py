"""hub/tests/test_response_cache_route.py — Phase 6 cache wiring in /query."""

import asyncio
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


def _req(intent_q="where is food", **kw):
    base = dict(center_id="c1", kiosk_id="k1", transcript_original=intent_q, language="en", kb_version=1)
    base.update(kw)
    return api_models.QueryRequest(**base)


class TestRouteCache(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        response_cache.invalidate_response_cache()

    def tearDown(self):
        self.db.close()
        response_cache.invalidate_response_cache()

    def _pipeline(self, intent="food"):
        return PipelineResult(normalized_text="where is food", intent=intent, intent_confidence=0.7,
                              pipeline_status="completed", stage_log=["normalize", "intent"], stage_latency={})

    def _dm(self):
        return {"answer_type": "DIRECT_MATCH", "confidence": 0.9, "answer_text": "Food is in Hall A.",
                "source_id": 7, "article_data": {"answer": "Food is in Hall A."}, "intent": "food",
                "fusion_top_k_ids": [7]}

    def _statuses(self):
        return [r.cache_status for r in self.db.query(schema.QueryLog).order_by(schema.QueryLog.id.asc()).all()]

    def test_miss_then_hit_skips_retrieval(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()) as retr, \
             patch("hub.api.routes_query.formatter.format_response", return_value="Food is in Hall A."):
            P.return_value.run.return_value = self._pipeline()
            r1 = _run(routes_query.submit_query(_req(), db=self.db))
            r2 = _run(routes_query.submit_query(_req(), db=self.db))
        self.assertEqual(r1.answer_text_en, "Food is in Hall A.")
        self.assertEqual(r2.answer_text_en, "Food is in Hall A.")
        self.assertEqual(retr.call_count, 1)  # second served from cache, retrieval skipped
        self.assertEqual(self._statuses(), ["miss", "hit"])

    def test_safety_intent_bypasses(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=dict(self._dm(), intent="medical")) as retr, \
             patch("hub.api.routes_query.formatter.format_response", return_value="See the nurse in Hall A."):
            P.return_value.run.return_value = self._pipeline(intent="medical")
            _run(routes_query.submit_query(_req("i need a doctor"), db=self.db))
            _run(routes_query.submit_query(_req("i need a doctor"), db=self.db))
        # both bypass → retrieval runs both times, nothing cached
        self.assertEqual(retr.call_count, 2)
        self.assertEqual(self._statuses(), ["bypass", "bypass"])

    def test_retry_not_cached(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()) as retr, \
             patch("hub.api.routes_query.formatter.format_response", return_value="Food is in Hall A."):
            P.return_value.run.return_value = self._pipeline()
            _run(routes_query.submit_query(_req(is_retry=True), db=self.db))
            _run(routes_query.submit_query(_req(is_retry=True), db=self.db))
        self.assertEqual(retr.call_count, 2)  # retries never cache → both retrieve
        self.assertEqual(self._statuses(), [None, None])

    def test_publish_invalidation_forces_miss(self):
        with patch("hub.api.routes_query.QueryPipeline") as P, \
             patch("hub.api.routes_query.search.retrieve", return_value=self._dm()) as retr, \
             patch("hub.api.routes_query.formatter.format_response", return_value="Food is in Hall A."):
            P.return_value.run.return_value = self._pipeline()
            _run(routes_query.submit_query(_req(), db=self.db))   # miss + store
            response_cache.invalidate_response_cache()            # simulates publish
            _run(routes_query.submit_query(_req(), db=self.db))   # miss again
        self.assertEqual(retr.call_count, 2)
        self.assertEqual(self._statuses(), ["miss", "miss"])


if __name__ == "__main__":
    unittest.main()
