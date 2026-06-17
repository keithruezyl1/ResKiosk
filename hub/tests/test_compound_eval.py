"""
hub/tests/test_compound_eval.py

Phase 4 S5.8 — compound retrieval evaluation scenarios run against the fixed
bundle and assert expected primary/secondary evidence + determinism.
"""

import unittest

from hub.eval.compound_eval import load_bundle, run_eval, run_scenario


class TestCompoundEval(unittest.TestCase):
    def setUp(self):
        self.bundle = load_bundle()

    def test_all_scenarios_pass(self):
        report = run_eval(self.bundle)
        self.assertEqual(report["metrics"]["primary_accuracy"], 1.0, report["per_scenario"])
        self.assertEqual(report["metrics"]["secondary_accuracy"], 1.0, report["per_scenario"])
        self.assertTrue(report["metrics"]["deterministic_all"])
        self.assertTrue(report["metrics"]["passed_all"])

    def test_safety_not_buried_below_higher_scoring_general(self):
        scn = next(s for s in self.bundle["scenarios"] if s["id"] == "safety_plus_facilities")
        r = run_scenario(scn)
        # safety (priority 100) leads despite facilities scoring 0.95 vs 0.50
        self.assertEqual(r["primary_intent"], "safety")
        self.assertEqual(r["merged_order"][0], 30)

    def test_same_tier_tie_broken_by_article_id(self):
        scn = next(s for s in self.bundle["scenarios"] if s["id"] == "food_plus_hours_same_tier")
        r = run_scenario(scn)
        self.assertEqual(r["primary_article_id"], 50)
        self.assertEqual(r["secondary_article_id"], 60)

    def test_determinism_per_scenario(self):
        for scn in self.bundle["scenarios"]:
            self.assertTrue(run_scenario(scn)["deterministic"], scn["id"])


if __name__ == "__main__":
    unittest.main()
