---
title: Execution — Phase 5 — Observability & trust completion
parent: Execution Plan
---

# Phase 5 — Observability & trust completion (Goal 10) — ✅ COMPLETE

> **STATUS: COMPLETE** (D9 resolved). Delivered: RK-55 (failure logging, earlier);
> S6A.2 per-stage latency (`pipeline.stage_latency` → `retrieve_ms`/`rewrite_ms`/
> `clarification_ms`); S6A.3 `final_evidence` stability anchor; S6A.5 rule_v1
> grounding proxy (`hub/eval/grounding.py` + grounding columns); S6A.4/S6A.7
> metrics export + KPI report by KB version (`hub/eval/kpi_report.py`, structured-only);
> S6A.6 fixed eval set (`hub/eval/mvp_eval.py` + `data/mvp_eval_set.json`); S6A.9
> readable trace (`logger_stream.format_query_trace`); plus D9c retention purge
> (`hub/db/retention.py`, 30-day default). 141-test suite green.
>
> **Honest scope notes:** (1) Per D9b, grounding is an **eval-time / human-review**
> metric, not auto-populated on production rows — `query_logs` doesn't store the
> generated answer text (privacy + LLM non-determinism), so `grounded_ratio` is
> filled by the eval set (recorded answers) or manual review, and the KPI report
> reads it where present. (2) No console review UI / separate grounding_review
> table was built — the grounding columns + `grounding_method="human"` support
> review without new tables (deferred if a UI is wanted). (3) `retrieve_ms` is the
> route-measured retrieval of the answer; `rewrite_ms`/`clarification_ms` come from
> pipeline stage timing.

## Objective and scope

Make system quality measurable end-to-end and validate stability before caching or multimodal.
The structured query-log **schema** is already shipped (Sprint 3). Remaining: finish failure
logging (RK-55), add latency-breakdown + evidence-stability capture, grounding-proxy review fields,
readable hub-log formatting, the fixed evaluation set, and a KPI report by KB version.

## Gating decisions

- **D9 — metrics storage + proxy representation + retention:** extend `query_logs` (preferred for
  MVP) vs a related table keyed by `query_logs.id`; how the hallucination/grounding proxy is
  represented (store spans vs compute offline); privacy/retention for normalized query text.

## Dependencies

Phase 0 logging backbone (done) + the structured schema (done) + RK-37 (done). **The RK-32
remainder (publish-attempt persistence) and RK-55 must be closed first** — KPIs must run over
complete logs. Benefits from Phases 1–4; KPI reporting should reflect Phase 4 multi-path output.

## Ordered execution steps

1. Close RK-55 (see carried-forward doc) — failure/fallback population.
2. Add latency-breakdown logging (per stage).
3. Capture final evidence list + stability fields.
4. Add grounding-proxy review fields.
5. Implement readable hub-log formatting.
6. Create the fixed evaluation query set.
7. Generate the KPI report by KB version (consumes 1–6).

---

## Work items

### RK-55 — Failure/fallback logging (3 pts)
See [carried-forward doc](00-carried-forward-rk32-rk37-rk55.md#rk-55--add-failure-and-fallback-outcome-logging-goal-10-3-pts). Prerequisite for KPI accuracy.

### S6A.2 — Add latency breakdown logging (5 pts)
- **Implement.** Capture per-stage timings (normalize, intent, clarify, rewrite, retrieve, respond)
  + overall + retrieval latency; persist as structured fields. `latency_ms` (overall) exists; add a
  `stage_latency` JSON field if per-stage isn't yet stored.
- **Files.** `hub/retrieval/pipeline.py` (time each stage on `PipelineResult`), `hub/api/
  routes_query.py` (write), `hub/db/schema.py` + `migrate_schema.py` if adding `stage_latency`.
- **Gates.** D9 (storage form).
- **Acceptance.** Each query logs overall + retrieval + per-stage latency; bounded; present for both
  single and compound paths.
- **Tests.** New `hub/tests/test_latency_logging.py` — fields present, plausible, reproducible shape.

### S6A.3 — Capture final evidence list and stability fields (5 pts)
- **Implement.** Store final evidence IDs, scores, ranks, modality (where available), and path
  attribution for the answer actually returned (distinct from per-component lexical/vector lists).
- **Files.** `hub/api/routes_query.py`, `hub/db/schema.py` (+ migration) for a `final_evidence`
  JSON field if not derivable; `hub/retrieval/pipeline.py`.
- **Gates.** D9.
- **Acceptance.** Evidence-stability metric is computable: same normalized query + KB version +
  config → identical final evidence IDs across runs.
- **Tests.** New `hub/tests/test_evidence_stability.py` — run-twice identical final evidence;
  fields populated.

### S6A.5 — Create grounding-proxy review fields (3 pts)
- **Implement.** Concrete review mechanism for the grounding/hallucination proxy: evidence links,
  manual supported/unsupported labels, and reviewer notes — so grounding can be reviewed manually or
  on a sample. (Represent per D9: spans stored vs offline computation.)
- **Files.** `hub/db/schema.py` + `migrate_schema.py` (e.g. `grounding_review` table or fields:
  `grounded_label`, `reviewer_note`, evidence links), optional `console/src/pages/QueryTracker.jsx`
  or `LogsViewer.jsx` for manual labeling.
- **Gates.** **D9.**
- **Acceptance.** A reviewer can attach supported/unsupported + note to a logged answer with its
  evidence links; fields feed the grounded-answer-rate KPI.
- **Tests.** New `hub/tests/test_grounding_review.py` — write/read review fields; KPI counts pick
  them up.

### S6A.9 — Format hub query logs for readable operational observability (3 pts)
- **Implement.** Human-readable live hub log lines: stable IDs, clear stage labels, clear outcomes,
  bounded payloads — for development, demos, and field ops. Distinct from the structured schema.
- **Files.** `hub/core/logger_stream.py` (formatting), `hub/retrieval/pipeline.py` (stage labels),
  `hub/api/routes_query.py`.
- **Acceptance.** A single query produces a legible, ordered log trace (stages + outcome + key IDs)
  without dumping raw article bodies; payloads bounded (≤120 chars text, matching existing rule).
- **Tests.** New `hub/tests/test_readable_logs.py` — captured log contains ordered stage labels +
  outcome + stable IDs; no oversized payloads.

### S6A.4 — Implement MVP metrics export workflow (5 pts)
- **Implement.** A minimum-viable export/query workflow that pulls the logged metrics out for review
  (CSV/JSON export or a simple query endpoint). This is the plumbing the KPI report (S6A.7) and
  Phase 11 benchmarking consume; keep it MVP, not a dashboard.
- **Files.** `hub/eval/kpi_report.py` (export helpers), optional `hub/api/routes_system.py` endpoint
  (`/admin/metrics/export`), optional `console/src/pages/LogsViewer.jsx`.
- **Gates.** D9 (storage form).
- **Acceptance.** Metrics can be exported/queried for a KB version without manual DB spelunking;
  output is stable for fixed inputs.
- **Tests.** New `hub/tests/test_metrics_export.py` — export over seeded logs returns expected rows;
  deterministic.

### S6A.6 — Create fixed evaluation query set (3 pts)
- **Implement.** A fixed set covering exact-term, compound, clarification, and safety/medical cases,
  with expected evidence IDs/behavior where feasible; pinned to a fixed KB snapshot.
- **Files.** `hub/eval/data/mvp_eval_set.json`, `hub/eval/mvp_eval.py`,
  `hub/tests/test_mvp_eval_set.py`.
- **Acceptance.** Set runs offline against the fixed snapshot deterministically; reused by Phase 11
  regression.
- **Tests.** `test_mvp_eval_set.py` — set loads, runs, expectations met, reproducible.

### S6A.7 — Generate basic KPI report by KB version (5 pts)
- **Implement.** A report grouped by KB version: query count, latency p50/p95 (overall + retrieval +
  per-stage), fallback/no-result counts, clarification counts, evidence stability, grounded-answer
  rate (from S6A.5), modality where available. Manual query/export acceptable for MVP.
- **Files.** new `hub/eval/kpi_report.py` (read `query_logs`), optional endpoint in
  `hub/api/routes_system.py` (`/admin/metrics` or `/admin/kpi`), optional
  `console/src/pages/LogsViewer.jsx` view.
- **Gates.** D9.
- **Acceptance.** Running the report over a seeded log set yields all KPIs grouped by KB version;
  numbers reconcile with the underlying rows; deterministic for fixed inputs.
- **Tests.** New `hub/tests/test_kpi_report.py` — seed known logs → assert computed KPIs exact.

---

## Phase 5 Definition of Done

RK-55 closed; latency breakdown + final-evidence-stability captured; grounding-proxy review fields
present and feeding the grounded-answer KPI; hub logs legible per the readable format; fixed eval
set in place; KPI report generates per KB version with reconciling numbers; D9 recorded; all Phase 5
tests + determinism checks pass; logs sufficient to replay/debug any query from stable IDs.
