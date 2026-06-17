"""
hub/db/retention.py

Phase 5 / Slice 6A (D9c) — query-text retention purge.

Nulls the human-readable transcript columns on query_logs rows older than a
configurable window while keeping all structured metric fields (IDs, scores,
intent, latency, kb_version, etc.). KPIs never need the raw text, so this limits
long-term PII/health-text exposure without losing analytics.

Window: RESKIOSK_QUERY_TEXT_RETENTION_DAYS (default 30). Set <= 0 to disable
(keep transcripts indefinitely). Safe to run repeatedly (idempotent).
"""

from __future__ import annotations

import os
import time
from typing import Optional

from sqlalchemy.orm import Session

from hub.db import schema

# Transcript columns considered PII-bearing; structured fields are never touched.
_TEXT_COLUMNS = ("transcript_original", "transcript_english", "raw_transcript", "normalized_transcript")

DEFAULT_RETENTION_DAYS = 30


def get_retention_days() -> int:
    try:
        return int(os.environ.get("RESKIOSK_QUERY_TEXT_RETENTION_DAYS", DEFAULT_RETENTION_DAYS))
    except (TypeError, ValueError):
        return DEFAULT_RETENTION_DAYS


def purge_old_query_text(
    db: Session,
    retention_days: Optional[int] = None,
    now_ts: Optional[int] = None,
) -> int:
    """Null transcript columns for query_logs rows older than the retention window.

    Returns the number of rows scrubbed. now_ts is injectable for deterministic
    tests. Window <= 0 disables purging (returns 0).
    """
    days = retention_days if retention_days is not None else get_retention_days()
    if days <= 0:
        return 0

    now = now_ts if now_ts is not None else int(time.time())
    cutoff = now - days * 86400

    rows = (
        db.query(schema.QueryLog)
        .filter(schema.QueryLog.created_at < cutoff)
        .all()
    )
    scrubbed = 0
    for row in rows:
        if any(getattr(row, col, None) for col in _TEXT_COLUMNS):
            for col in _TEXT_COLUMNS:
                setattr(row, col, None)
            scrubbed += 1
    if scrubbed:
        db.commit()
    return scrubbed
