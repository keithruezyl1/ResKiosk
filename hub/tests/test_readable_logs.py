"""hub/tests/test_readable_logs.py — Phase 5 S6A.9 readable query trace."""

import unittest

from hub.core.logger_stream import format_query_trace


class TestReadableTrace(unittest.TestCase):
    def test_ordered_stages_outcome_and_ids(self):
        line = format_query_trace(
            ["normalize", "intent", "retrieve", "clarification_gate"],
            intent="medical", intent_confidence=0.83,
            answer_type="DIRECT_MATCH", source_id=42,
        )
        self.assertIn("stages=normalize>intent>retrieve>clarification_gate", line)
        self.assertIn("intent=medical(0.83)", line)
        self.assertIn("outcome=DIRECT_MATCH", line)
        self.assertIn("src=42", line)

    def test_compound_and_fallback(self):
        line = format_query_trace(
            ["normalize", "intent", "retrieve"],
            intent="safety", answer_type="NO_MATCH",
            fallback_reason="no_results", compound_detected=True, secondary_intent="facilities",
        )
        self.assertIn("compound+facilities", line)
        self.assertIn("fallback=no_results", line)

    def test_bounded_no_huge_payload(self):
        line = format_query_trace(["retrieve"], intent="x" * 500, answer_type="DIRECT_MATCH")
        # the oversized intent field is capped (truncation marker present), no 500-char dump
        self.assertNotIn("x" * 200, line)


if __name__ == "__main__":
    unittest.main()
