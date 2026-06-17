"""
hub/tests/test_publish_audit.py

RK-32 (remainder) — publish-time audit persistence.

Verifies /admin/publish persists:
  - one KBPublishAttempt row per attempt (pass / blocked / warn), with the
    intended kb_version, mapped status, counts, and actor; and
  - the failed per-rule KBValidationResult rows produced by the gate run,
    linked to that attempt via publish_attempt_id.

Uses a real in-memory SQLite DB and a real publish-gate handoff; only the
validation *inputs* (validate_metadata result) and embedding side-effects are
controlled.
"""

import asyncio
import unittest
from unittest.mock import patch, MagicMock

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from hub.db.session import Base
from hub.db import schema
from hub.api import routes_admin
from hub.validation.metadata import (
    MetadataRuleResult,
    MetadataItemValidationResult,
    MetadataValidationSummary,
    MetadataValidationRunResult,
    RULE_TAXONOMY_PRIMARY_ASSIGNMENT_MISSING,
    RULE_METADATA_AUTHORITY_MISSING,
    SEVERITY_ERROR,
    SEVERITY_WARNING,
    STATUS_APPROVED,
    STATUS_NEEDS_REVIEW,
    STATUS_QUARANTINED,
    PUBLISH_STATUS_PASS,
    PUBLISH_STATUS_WARNING,
    PUBLISH_STATUS_BLOCKED,
)


def _run(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
        asyncio.set_event_loop(asyncio.new_event_loop())


def _rr_blocked():
    item = MetadataItemValidationResult(
        article_id=1,
        status=STATUS_QUARANTINED,
        rule_results=(
            MetadataRuleResult(RULE_TAXONOMY_PRIMARY_ASSIGNMENT_MISSING, SEVERITY_ERROR, False, "missing taxonomy"),
        ),
    )
    summary = MetadataValidationSummary(1, 0, 0, 1, 1, PUBLISH_STATUS_BLOCKED)
    return MetadataValidationRunResult(items=(item,), summary=summary)


def _rr_warning():
    item = MetadataItemValidationResult(
        article_id=2,
        status=STATUS_NEEDS_REVIEW,
        rule_results=(
            MetadataRuleResult(RULE_METADATA_AUTHORITY_MISSING, SEVERITY_WARNING, False, "authority missing"),
        ),
    )
    summary = MetadataValidationSummary(1, 0, 1, 0, 1, PUBLISH_STATUS_WARNING)
    return MetadataValidationRunResult(items=(item,), summary=summary)


def _rr_pass():
    item = MetadataItemValidationResult(article_id=3, status=STATUS_APPROVED, rule_results=())
    summary = MetadataValidationSummary(1, 1, 0, 0, 0, PUBLISH_STATUS_PASS)
    return MetadataValidationRunResult(items=(item,), summary=summary)


class TestPublishAudit(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.db.add(schema.SystemVersion(kb_version=5))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _publish(self, policy, run_result):
        with (
            patch.object(routes_admin, "_get_structured_config_value", return_value=policy),
            patch.object(routes_admin, "load_validation_targets", return_value=()),
            patch.object(routes_admin, "load_taxonomy_reference", return_value=(frozenset(), frozenset())),
            patch.object(routes_admin, "validate_metadata", return_value=run_result),
            patch.object(routes_admin, "load_embedder", return_value=MagicMock(embed_text=MagicMock(return_value=[0.1] * 8))),
            patch.object(routes_admin, "serialize_embedding", return_value=b"vec"),
            patch.object(routes_admin, "get_embeddable_text", return_value="text"),
            patch.object(routes_admin, "invalidate_corpus_cache"),
            patch.object(routes_admin, "invalidate_lexical_index"),
        ):
            try:
                return _run(routes_admin.publish_kb(db=self.db)), None
            except HTTPException as exc:
                return None, exc

    def _attempts(self):
        return self.db.query(schema.KBPublishAttempt).all()

    def _results(self):
        return self.db.query(schema.KBValidationResult).all()

    # -- blocked (strict) -----------------------------------------------------

    def test_strict_block_records_attempt_and_rule(self):
        _, exc = self._publish("strict", _rr_blocked())
        self.assertIsNotNone(exc)
        self.assertEqual(exc.status_code, 422)

        attempts = self._attempts()
        self.assertEqual(len(attempts), 1)
        a = attempts[0]
        self.assertEqual(a.status, "blocked")
        self.assertEqual(a.kb_version, 6)            # intended = current(5) + 1
        self.assertEqual(a.quarantined_count, 1)

        results = self._results()
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r.rule_id, RULE_TAXONOMY_PRIMARY_ASSIGNMENT_MISSING)
        self.assertEqual(r.severity, SEVERITY_ERROR)
        self.assertFalse(r.passed)
        self.assertEqual(r.publish_attempt_id, a.id)

    # -- pass -----------------------------------------------------------------

    def test_pass_records_attempt_no_rules(self):
        result, exc = self._publish("strict", _rr_pass())
        self.assertIsNone(exc)
        self.assertEqual(result["status"], "published")

        attempts = self._attempts()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, "pass")
        self.assertEqual(attempts[0].approved_count, 1)
        self.assertEqual(len(self._results()), 0)
        # attempt id surfaced in the response gate payload
        self.assertEqual(result["validation_gate"]["publish_attempt_id"], attempts[0].id)

    # -- warning (needs_review, strict proceeds) ------------------------------

    def test_warning_records_partial_attempt_and_rule(self):
        result, exc = self._publish("strict", _rr_warning())
        self.assertIsNone(exc)
        self.assertEqual(result["status"], "published")

        attempts = self._attempts()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, "partial")

        results = self._results()
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].severity, SEVERITY_WARNING)

    # -- warn_only past a blocked handoff -------------------------------------

    def test_warn_only_blocked_records_partial(self):
        result, exc = self._publish("warn_only", _rr_blocked())
        self.assertIsNone(exc)
        self.assertEqual(result["status"], "published")
        attempts = self._attempts()
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0].status, "partial")


if __name__ == "__main__":
    unittest.main()
