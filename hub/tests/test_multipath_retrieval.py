"""
hub/tests/test_multipath_retrieval.py

Phase 4 S5.1–S5.3 — intent-scoped path queries + per-path retrieval orchestration.
"""

import unittest
from unittest.mock import patch, MagicMock

from hub.retrieval import search


class TestBuildPathQueries(unittest.TestCase):
    def test_two_distinct_intents_priority_ordered(self):
        paths = search.build_path_queries("i have a fever near building a", "location", "medical")
        # medical (priority 90) must come before location (priority 10)
        self.assertEqual([p[0] for p in paths], ["medical", "location"])
        self.assertEqual(paths[0][1], search._intent_priority("medical"))
        # each path query is the base query enriched toward its intent
        self.assertTrue(paths[0][2].startswith("i have a fever near building a"))
        self.assertIn(search.INTENT_ENRICHMENT["medical"].split()[0], paths[0][2])

    def test_dedupes_same_intent(self):
        paths = search.build_path_queries("q", "medical", "medical")
        self.assertEqual(len(paths), 1)

    def test_single_intent_when_secondary_none(self):
        paths = search.build_path_queries("q", "food", None)
        self.assertEqual([p[0] for p in paths], ["food"])


class TestRetrieveMultipath(unittest.TestCase):
    def _result(self, ids, scores):
        return {"fusion_top_k_ids": ids, "fusion_top_k_scores": scores, "answer_type": "DIRECT_MATCH"}

    def test_runs_each_path_and_merges_by_priority(self):
        # medical path returns doc 50 (score .4); location path returns doc 99 (score .9)
        def fake_retrieve(db, q, is_retry, **kw):
            if "medical" in q or search.INTENT_ENRICHMENT["medical"].split()[0] in q:
                return self._result([50], [0.4])
            return self._result([99], [0.9])

        with patch("hub.retrieval.search.retrieve", side_effect=fake_retrieve):
            out = search.retrieve_multipath(MagicMock(), "fever near clinic", "location", "medical")

        self.assertIn("medical", out["per_path"])
        self.assertIn("location", out["per_path"])
        merged_ids = [c.article_id for c in out["merged"].results]
        # medical (higher priority) bucketed ahead of location despite lower score
        self.assertEqual(merged_ids[0], 50)
        self.assertEqual(out["merged"].results[0].primary_intent, "medical")

    def test_path_failure_is_safe(self):
        def fake_retrieve(db, q, is_retry, **kw):
            if search.INTENT_ENRICHMENT["medical"].split()[0] in q:
                raise RuntimeError("boom")
            return self._result([99], [0.9])

        with patch("hub.retrieval.search.retrieve", side_effect=fake_retrieve):
            out = search.retrieve_multipath(MagicMock(), "q", "location", "medical")

        # medical path failed → still merged the surviving location path
        merged_ids = [c.article_id for c in out["merged"].results]
        self.assertEqual(merged_ids, [99])

    def test_candidates_fall_back_to_vector_fields(self):
        def fake_retrieve(db, q, is_retry, **kw):
            return {"vector_top_k_ids": [7], "vector_top_k_scores": [0.5]}

        with patch("hub.retrieval.search.retrieve", side_effect=fake_retrieve):
            out = search.retrieve_multipath(MagicMock(), "q", "food", None)
        self.assertEqual([c.article_id for c in out["merged"].results], [7])


if __name__ == "__main__":
    unittest.main()
