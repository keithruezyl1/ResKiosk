"""
hub/eval/kpi_report.py

Phase 5 / Slice 6A — MVP metrics export (S6A.4) + KPI report by KB version (S6A.7).

Reads query_logs and computes KPIs grouped by kb_version:
  - query count, latency p50/p95 (overall + retrieve)
  - fallback / no-result counts (by reason), clarification + compound counts
  - grounded-answer rate (mean grounded_ratio + fully-grounded fraction, rule_v1)
  - evidence stability (same normalized query + KB version → identical final_evidence)

D9c privacy: the EXPORTED rows and the report contain only structured fields —
never transcript text. Stability grouping reads normalized text internally but
emits only aggregate counts, never the text itself. Deterministic for fixed input.

Run:
  python -m hub.eval.kpi_report
  python -m hub.eval.kpi_report --json-out kpis.json
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Any, Optional

from sqlalchemy.orm import Session

from hub.db import schema
from hub.db.session import SessionLocal

# Structured columns safe to export (NO transcript_* / raw text).
EXPORT_FIELDS = [
    "id", "kb_version", "intent_label", "answer_type", "source_id", "retrieval_score",
    "latency_ms", "retrieve_ms", "rewrite_ms", "clarification_ms",
    "fallback_reason", "failed_stage", "clarification_triggered", "compound_detected",
    "grounded_ratio", "unsupported_span_count", "grounding_method", "final_evidence",
    "created_at",
]


def _percentile(values: list[float], pct: float) -> Optional[float]:
    """Nearest-rank percentile (deterministic). Returns None for empty input."""
    vals = sorted(v for v in values if v is not None)
    if not vals:
        return None
    rank = max(1, math.ceil(pct / 100.0 * len(vals)))
    return round(float(vals[rank - 1]), 3)


def export_metrics_rows(db: Session, kb_version: Optional[int] = None) -> list[dict]:
    """Return structured-only metric rows (no transcript text), oldest first."""
    q = db.query(schema.QueryLog)
    if kb_version is not None:
        q = q.filter(schema.QueryLog.kb_version == kb_version)
    q = q.order_by(schema.QueryLog.id.asc())
    return [{f: getattr(row, f, None) for f in EXPORT_FIELDS} for row in q.all()]


def _kpis_for_rows(rows: list[dict], normalized_by_id: dict[int, str]) -> dict[str, Any]:
    n = len(rows)
    overall = [r["latency_ms"] for r in rows]
    retrieve = [r["retrieve_ms"] for r in rows]

    fallback_by_reason: dict[str, int] = {}
    for r in rows:
        if r["fallback_reason"]:
            fallback_by_reason[r["fallback_reason"]] = fallback_by_reason.get(r["fallback_reason"], 0) + 1

    grounded_vals = [r["grounded_ratio"] for r in rows if r["grounded_ratio"] is not None]
    fully_grounded = sum(1 for v in grounded_vals if v >= 1.0)

    # Evidence stability: group rows sharing the same normalized query text within
    # this KB version; a repeated query is "stable" if every occurrence produced the
    # same final_evidence. Only aggregate counts are emitted (never the text).
    groups: dict[str, list] = {}
    for r in rows:
        key = normalized_by_id.get(r["id"]) or ""
        if key:
            groups.setdefault(key, []).append(r["final_evidence"])
    repeated = {k: evs for k, evs in groups.items() if len(evs) > 1}
    stable = sum(1 for evs in repeated.values() if len(set(evs)) == 1)

    return {
        "query_count": n,
        "latency_ms_p50": _percentile(overall, 50),
        "latency_ms_p95": _percentile(overall, 95),
        "retrieve_ms_p50": _percentile(retrieve, 50),
        "retrieve_ms_p95": _percentile(retrieve, 95),
        "fallback_count": sum(fallback_by_reason.values()),
        "fallback_by_reason": dict(sorted(fallback_by_reason.items())),
        "clarification_count": sum(1 for r in rows if r["clarification_triggered"]),
        "compound_count": sum(1 for r in rows if r["compound_detected"]),
        "grounded_answer_rate": round(sum(grounded_vals) / len(grounded_vals), 6) if grounded_vals else None,
        "fully_grounded_count": fully_grounded,
        "grounded_sampled": len(grounded_vals),
        "evidence_stability": {
            "repeated_query_groups": len(repeated),
            "stable_groups": stable,
        },
    }


def build_kpi_report(db: Session) -> dict[str, Any]:
    all_rows = export_metrics_rows(db)
    # Internal-only map of id -> normalized text for stability grouping (never exported).
    normalized_by_id = {
        row.id: row.normalized_transcript
        for row in db.query(schema.QueryLog).all()
    }
    by_version: dict[int, list[dict]] = {}
    for r in all_rows:
        by_version.setdefault(r["kb_version"], []).append(r)

    return {
        "total_rows": len(all_rows),
        "kb_versions": {
            str(v): _kpis_for_rows(rows, normalized_by_id)
            for v, rows in sorted(by_version.items(), key=lambda kv: (kv[0] is None, kv[0]))
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the MVP KPI report by KB version.")
    parser.add_argument("--json-out", type=str, default=None)
    args = parser.parse_args()
    db = SessionLocal()
    try:
        report = build_kpi_report(db)
    finally:
        db.close()
    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        from pathlib import Path
        Path(args.json_out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
