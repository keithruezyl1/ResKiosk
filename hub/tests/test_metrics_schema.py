"""
hub/tests/test_metrics_schema.py

Phase 5 / Slice 6A — verify the MVP metrics columns exist (nullable, additive)
on QueryLog and have ALTER entries in migrate_schema.py.
"""

import unittest
from pathlib import Path

from hub.db import schema

PHASE5_COLUMNS = {
    "retrieve_ms",
    "rewrite_ms",
    "clarification_ms",
    "final_evidence",
    "grounded_ratio",
    "unsupported_span_count",
    "grounding_method",
    "grounding_detail",
}


class TestMetricsSchema(unittest.TestCase):
    def setUp(self):
        self.columns = {c.name for c in schema.QueryLog.__table__.columns}

    def test_columns_present(self):
        missing = PHASE5_COLUMNS - self.columns
        self.assertFalse(missing, f"QueryLog missing Phase 5 metrics columns: {missing}")

    def test_columns_nullable(self):
        for name in PHASE5_COLUMNS:
            self.assertTrue(schema.QueryLog.__table__.columns[name].nullable, name)

    def test_migration_entries_present(self):
        src = (Path(schema.__file__).parent / "migrate_schema.py").read_text(encoding="utf-8")
        for name in PHASE5_COLUMNS:
            self.assertIn(f'"{name}":', src, f"no migration key for {name}")
            self.assertIn(f"ADD COLUMN {name}", src, f"no ALTER for {name}")


if __name__ == "__main__":
    unittest.main()
