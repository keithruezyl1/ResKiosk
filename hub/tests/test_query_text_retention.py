"""hub/tests/test_query_text_retention.py — Phase 5 D9c transcript retention purge."""

import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.db.retention import purge_old_query_text

DAY = 86400


def _log(created_at, **kw):
    base = dict(kiosk_id="k", language="en", answer_type="DIRECT_MATCH",
                transcript_original="i have a fever", raw_transcript="i have a fever",
                normalized_transcript="fever", transcript_english="i have a fever",
                intent_label="medical", kb_version=1, created_at=created_at)
    base.update(kw)
    return schema.QueryLog(**base)


class TestRetention(unittest.TestCase):
    def setUp(self):
        e = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(e)
        self.db = sessionmaker(bind=e)()
        self.now = 100 * DAY
        self.db.add(_log(self.now - 40 * DAY))   # old → should be scrubbed
        self.db.add(_log(self.now - 5 * DAY))    # recent → kept
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_purges_old_text_keeps_structured(self):
        scrubbed = purge_old_query_text(self.db, retention_days=30, now_ts=self.now)
        self.assertEqual(scrubbed, 1)
        rows = self.db.query(schema.QueryLog).order_by(schema.QueryLog.created_at.asc()).all()
        old, recent = rows[0], rows[1]
        # old: transcripts nulled, structured fields intact
        self.assertIsNone(old.transcript_original)
        self.assertIsNone(old.raw_transcript)
        self.assertIsNone(old.normalized_transcript)
        self.assertEqual(old.intent_label, "medical")
        self.assertEqual(old.kb_version, 1)
        # recent: untouched
        self.assertEqual(recent.transcript_original, "i have a fever")

    def test_disabled_when_window_non_positive(self):
        self.assertEqual(purge_old_query_text(self.db, retention_days=0, now_ts=self.now), 0)
        self.assertEqual(self.db.query(schema.QueryLog).first().transcript_original, "i have a fever")

    def test_idempotent(self):
        purge_old_query_text(self.db, retention_days=30, now_ts=self.now)
        self.assertEqual(purge_old_query_text(self.db, retention_days=30, now_ts=self.now), 0)


if __name__ == "__main__":
    unittest.main()
