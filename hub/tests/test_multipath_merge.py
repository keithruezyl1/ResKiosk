"""
hub/tests/test_multipath_merge.py

Phase 4 S5.4 + S5.5 — deterministic priority-bucket-then-RRF merge.
"""

import unittest

from hub.retrieval.multipath_merge import PathInput, merge_paths


# Priority values mirror search.INTENT_PRIORITY (safety/medical high, general low).
P_MEDICAL = 90
P_SAFETY = 100
P_GENERAL = 10


class TestMultipathMerge(unittest.TestCase):
    def test_safety_medical_never_buried_below_general(self):
        # General path's top doc has a *better* per-path rank than the medical doc,
        # but priority bucketing must still place the medical doc first.
        medical = PathInput("medical", P_MEDICAL, ((50, 0.40),))
        general = PathInput("general_info", P_GENERAL, ((99, 0.99),))
        out = merge_paths([general, medical])
        self.assertEqual([c.article_id for c in out.results], [50, 99])
        self.assertEqual(out.results[0].primary_intent, "medical")
        self.assertEqual(out.results[0].priority, P_MEDICAL)

    def test_within_tier_ordered_by_rrf(self):
        # Two docs in the same (medical) tier: the one appearing in more/earlier
        # paths gets the higher RRF score.
        path_a = PathInput("medical", P_MEDICAL, ((1, 0.9), (2, 0.8)))
        path_b = PathInput("medical", P_MEDICAL, ((1, 0.7),))  # doc 1 again → higher RRF
        out = merge_paths([path_a, path_b])
        self.assertEqual(out.results[0].article_id, 1)
        self.assertGreater(out.results[0].rrf_score, out.results[1].rrf_score)

    def test_dedupe_preserves_all_memberships(self):
        path_a = PathInput("medical", P_MEDICAL, ((7, 0.9),))
        path_b = PathInput("location", 10, ((7, 0.6),))
        out = merge_paths([path_a, path_b])
        # one merged entry for doc 7, with both path memberships retained
        sevens = [c for c in out.results if c.article_id == 7]
        self.assertEqual(len(sevens), 1)
        intents = {m.intent for m in sevens[0].memberships}
        self.assertEqual(intents, {"medical", "location"})
        # priority = the higher of the two (medical)
        self.assertEqual(sevens[0].priority, P_MEDICAL)
        self.assertEqual(sevens[0].primary_intent, "medical")

    def test_deterministic_run_twice(self):
        paths = [
            PathInput("safety", P_SAFETY, ((3, 0.5), (4, 0.5))),
            PathInput("medical", P_MEDICAL, ((4, 0.5), (5, 0.5))),
            PathInput("food", P_GENERAL, ((6, 0.5),)),
        ]
        a = merge_paths(paths)
        b = merge_paths(paths)
        self.assertEqual(
            [(c.article_id, c.merged_rank, c.priority) for c in a.results],
            [(c.article_id, c.merged_rank, c.priority) for c in b.results],
        )

    def test_tie_break_by_article_id(self):
        # identical priority + identical rrf (same rank, single path each) → article_id asc
        path = PathInput("food", P_GENERAL, ((20, 0.5), (10, 0.5)))  # both rank-distinct
        # force a true tie: two separate single-candidate paths at rank 1
        p1 = PathInput("food", P_GENERAL, ((20, 0.5),))
        p2 = PathInput("food", P_GENERAL, ((10, 0.5),))
        out = merge_paths([p1, p2])
        self.assertEqual([c.article_id for c in out.results], [10, 20])

    def test_top_k_limit(self):
        path = PathInput("food", P_GENERAL, tuple((i, 1.0 / i) for i in range(1, 11)))
        out = merge_paths([path], top_k=3)
        self.assertEqual(len(out.results), 3)
        self.assertEqual(out.strategy, "priority_bucket_rrf")

    def test_empty_paths_safe(self):
        empty = PathInput("medical", P_MEDICAL, ())
        out = merge_paths([empty])
        self.assertEqual(out.results, [])


if __name__ == "__main__":
    unittest.main()
