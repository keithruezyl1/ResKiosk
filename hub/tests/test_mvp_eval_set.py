"""hub/tests/test_mvp_eval_set.py — Phase 5 S6A.6 fixed eval query set."""

import unittest

from hub.eval.mvp_eval import load_eval_set, coverage


class TestMvpEvalSet(unittest.TestCase):
    def test_loads_and_well_formed(self):
        b = load_eval_set()
        self.assertGreaterEqual(len(b["scenarios"]), 4)
        for s in b["scenarios"]:
            self.assertIn("id", s)
            self.assertIn("type", s)
            self.assertIn("query", s)

    def test_covers_required_case_types(self):
        cov = coverage()
        self.assertTrue(cov["complete"], f"missing case types: {cov['missing']}")
        for t in ("exact_term", "compound", "clarification", "safety_medical"):
            self.assertGreaterEqual(cov["counts"][t], 1)

    def test_deterministic(self):
        self.assertEqual(coverage(), coverage())


if __name__ == "__main__":
    unittest.main()
