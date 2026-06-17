"""
hub/tests/test_kpi_report.py

Phase 5 S6A.4 + S6A.7 — MVP metrics export + KPI report by KB version.
Seeds known query_logs rows and asserts exact computed KPIs; verifies the
export carries no transcript text (D9c).
"""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.eval.kpi_report import build_kpi_report, export_metrics_rows, _percentile


def _log(**kw):
    base = dict(kiosk_id="k", language="en", answer_type="DIRECT_MATCH", created_at=0)
    base.update(kw)
    return schema.QueryLog(**base)


class TestPercentile(unittest.TestCase):
    def test_nearest_rank(self):
        self.assertEqual(_percentile([100, 200, 300], 50), 200.0)
        self.assertEqual(_percentile([100, 200, 300], 95), 300.0)
        self.assertIsNone(_percentile([], 50))


class TestKpiReport(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        rows = [
            _log(kb_version=1, latency_ms=100, retrieve_ms=40, grounded_ratio=1.0,
                 normalized_transcript="where food", final_evidence="E1"),
            _log(kb_version=1, latency_ms=200, retrieve_ms=60, grounded_ratio=0.5,
                 fallback_reason="low_confidence", normalized_transcript="where food", final_evidence="E1"),
            _log(kb_version=1, latency_ms=300, retrieve_ms=80, clarification_triggered=True,
                 compound_detected=True, normalized_transcript="med help", final_evidence="E2"),
            _log(kb_version=2, latency_ms=50, normalized_transcript="hi", final_evidence="E9"),
        ]
        for r in rows:
            self.db.add(r)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_kpis_exact(self):
        rep = build_kpi_report(self.db)
        self.assertEqual(rep["total_rows"], 4)
        k1 = rep["kb_versions"]["1"]
        self.assertEqual(k1["query_count"], 3)
        self.assertEqual(k1["latency_ms_p50"], 200.0)
        self.assertEqual(k1["latency_ms_p95"], 300.0)
        self.assertEqual(k1["retrieve_ms_p50"], 60.0)
        self.assertEqual(k1["fallback_count"], 1)
        self.assertEqual(k1["fallback_by_reason"], {"low_confidence": 1})
        self.assertEqual(k1["clarification_count"], 1)
        self.assertEqual(k1["compound_count"], 1)
        self.assertEqual(k1["grounded_answer_rate"], 0.75)
        self.assertEqual(k1["fully_grounded_count"], 1)
        self.assertEqual(k1["grounded_sampled"], 2)
        self.assertEqual(k1["evidence_stability"], {"repeated_query_groups": 1, "stable_groups": 1})

    def test_kb2_isolated(self):
        rep = build_kpi_report(self.db)
        self.assertEqual(rep["kb_versions"]["2"]["query_count"], 1)
        self.assertIsNone(rep["kb_versions"]["2"]["grounded_answer_rate"])

    def test_export_has_no_transcript_text(self):
        rows = export_metrics_rows(self.db, kb_version=1)
        self.assertEqual(len(rows), 3)
        for r in rows:
            for forbidden in ("transcript_original", "transcript_english", "raw_transcript", "normalized_transcript"):
                self.assertNotIn(forbidden, r)
            self.assertIn("kb_version", r)
            self.assertIn("grounded_ratio", r)

    def test_deterministic(self):
        self.assertEqual(build_kpi_report(self.db), build_kpi_report(self.db))


if __name__ == "__main__":
    unittest.main()
