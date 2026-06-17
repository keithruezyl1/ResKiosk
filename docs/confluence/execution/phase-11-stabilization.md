---
title: Execution — Phase 11 — Stabilization & release
parent: Execution Plan
---

# Phase 11 — Stabilization & release (formerly Sprint 8; dates removed)

## Objective and scope

End-to-end validation, benchmarking, and regression of the whole increment with **no new feature
development** — only critical/blocking bug fixes. This is the verification capstone for the
determinism/reproducibility constraint. (We are out of the competition, so the original
"submission package / freeze / demo rehearsal" tasks are optional housekeeping, not deliverables.)

## Gating decisions

None. Validation only.

## Dependencies

All feature phases (4–10). Phase 6 (caching) validated here too if delivered. Reuses the fixed KB
snapshot fixture + `hub/eval/` sets from Phases 4, 5, 10.

## Ordered execution steps

1. Assemble the fixed test build + pinned KB snapshot + config.
2. Run E2E suites (text, clarification, hybrid, compound, multimodal).
3. Run benchmarks (latency, retrieval, image retrieval, kiosk image load).
4. Run regression vs the fixed snapshot; generate final KPI report.
5. Validate eval/regression sets; verify log readability.
6. Fix critical/blocking bugs only; re-run.

---

## Work items (tasks/bugs/test-tasks — 0 feature pts)

### E2E testing
- **Text-query E2E** — query → response → logs; expected evidence; no disabled/unpublished evidence.
- **Clarification E2E** — ambiguous query → chips → selection → resume → resolution logged; rewrite/
  retrieval did not run before resolution.
- **Hybrid retrieval E2E** — exact-term query → vector+lexical+fusion logged → filters applied →
  expected final evidence.
- **Compound query E2E** — top-2 detection → per-path retrieval → deterministic merge → primary +
  secondary correct.
- **Multimodal E2E** — upload → thumbnail/rendition → embedding → text→image retrieval → kiosk
  display → image-first; fallback when image fails.
- **Files.** `hub/tests/` integration tests via `TestClient`; kiosk Kotlin tests; manual kiosk
  checklist for visual E2E.

### Benchmarking
- **Query latency** (p50/p95 overall + per stage), **hybrid + multi-path retrieval** (quality +
  stability), **image retrieval** (embedding time, retrieval latency, top-k accuracy, fixed-config
  stability), **kiosk image loading** (thumbnail/rendition load).
- **Files.** `hub/eval/kpi_report.py`, new `hub/eval/benchmarks.py`; results recorded under
  `hub/eval/data/` or `docs/`.

### Regression + reporting
- **Regression vs fixed KB snapshot** — text, clarification, hybrid, compound, image retrieval,
  kiosk rendering all produce expected + deterministic outcomes.
- **Final KPI report by KB version** — from `hub/eval/kpi_report.py`.
- **Verify hub logs readable** during the demo flow (S6A.9 format).
- **Validate image retrieval + multimodal regression sets** (Phase 9/10 eval sets).
- **Files.** `hub/eval/*`, `hub/tests/test_*_eval.py`.

### Release hygiene (optional, non-competition)
- **Fix critical/blocking bugs only**; classify the rest as deferred. Record final commit/tag if
  desired. (Submission package / freeze / demo rehearsal are optional now.)

---

## Determinism & reproducibility gate (the central acceptance bar)

For the pinned KB snapshot + config (fixed `kb_version`, `RESKIOSK_RRF_K`, `RESKIOSK_HYBRID_TOP_K`,
bias state, image model version):

- Every eval set (exact-term, compound, MVP, multimodal) runs **twice → identical** ordered evidence
  IDs, scores, ranks, and tie-break outcomes.
- KPI report numbers reconcile with the underlying `query_logs` rows.
- No stale answers across version boundaries (if caching delivered).

## Phase 11 Definition of Done

All E2E suites pass; benchmarks recorded; regression sets pass deterministically against the fixed
snapshot; final KPI report generated and reviewed; hub logs verified readable; no known critical
bugs; docs reflect final state. (Optional: codebase tagged.)
