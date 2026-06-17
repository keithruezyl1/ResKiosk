"""
hub/tests/test_grounding_proxy.py

Phase 5 / Slice 6A — rule_v1 grounding proxy (deterministic, offline).
"""

import unittest

from hub.eval.grounding import grounding_score, GROUNDING_METHOD_RULE_V1


EVIDENCE = [
    "The medical station is located in Hall A near the main entrance. "
    "A nurse is available from 8am to 8pm for first aid and medicine.",
]


class TestGroundingProxy(unittest.TestCase):
    def test_supported_answer_high_ratio(self):
        answer = "The medical station is in Hall A. A nurse is available for first aid."
        r = grounding_score(answer, EVIDENCE)
        self.assertEqual(r["grounding_method"], GROUNDING_METHOD_RULE_V1)
        self.assertEqual(r["unsupported_span_count"], 0)
        self.assertEqual(r["grounded_ratio"], 1.0)

    def test_fabricated_answer_flagged(self):
        answer = "The helicopter departs at midnight from the rooftop casino."
        r = grounding_score(answer, EVIDENCE)
        self.assertGreater(r["unsupported_span_count"], 0)
        self.assertLess(r["grounded_ratio"], 1.0)

    def test_mixed_answer_partial(self):
        answer = "The medical station is in Hall A. Free yachts are parked outside."
        r = grounding_score(answer, EVIDENCE)
        self.assertEqual(r["unsupported_span_count"], 1)
        self.assertAlmostEqual(r["grounded_ratio"], 0.5)

    def test_no_content_sentence_is_trivially_supported(self):
        r = grounding_score("Okay. Thanks.", EVIDENCE)
        self.assertEqual(r["unsupported_span_count"], 0)

    def test_empty_answer(self):
        r = grounding_score("", EVIDENCE)
        self.assertIsNone(r["grounded_ratio"])
        self.assertEqual(r["unsupported_span_count"], 0)

    def test_deterministic(self):
        answer = "The medical station is in Hall A. Free yachts are parked outside."
        self.assertEqual(grounding_score(answer, EVIDENCE), grounding_score(answer, EVIDENCE))


if __name__ == "__main__":
    unittest.main()
