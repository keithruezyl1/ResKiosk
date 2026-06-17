---
title: Execution — Carried-forward logging (RK-32, RK-37, RK-55)
parent: Execution Plan
---

# Carried-forward logging — RK-32, RK-37, RK-55

## Objective and scope

Close the remaining carried-forward logging from Sprint 3 so structured logs are **complete and
trustworthy** for Phase 5 KPI computation. **Post-merge status:** RK-37 is **DONE**; RK-55 is
outstanding; RK-32 is **partially done** (audit tables + review-decision persistence exist; the
publish-gate persistence remains). Do the remaining two first — they are small and unblock Phase 5.

## Gating decisions

None. D6 (hybrid specifics) is resolved. RK-32's storage already exists as dedicated tables
(`kb_publish_attempts`, `kb_validation_results`, `kb_review_decisions`, `kb_item_validation_status`).

## Ordered execution steps

1. RK-55 (failure/fallback population) — pipeline-wide; do alongside Phase 4 so multi-path inherits it.
2. RK-32 remainder (publish-attempt + per-rule result persistence at the gate) — anytime before Phase 5 KPIs.

---

## RK-37 — Add hybrid retrieval contribution logging (Goal 4 + Goal 10, 3 pts) — ✅ DONE (verified in merge)

**Status.** Implemented and verified against the merged code; **no remaining work.**

- `hub/retrieval/search.py` builds the full `retrieval_metadata`: `lexical_top_k_ids/scores/ranks`,
  `vector_top_k_ids/scores/ranks`, `fusion_strategy`, `fusion_parameters`,
  `fusion_top_k_ids/scores/ranks`, `fusion_tie_breaks`, plus `bias_enabled/bias_applied_count/
  bias_top1_changed/bias_detail`.
- `hub/api/routes_query.py` writes all of these to `query_logs` (both the pause-state and final
  write paths).
- Existing coverage in `hub/tests/test_hybrid_retrieval.py` / `test_fusion.py`.

If hardening is wanted later, add an explicit determinism test (same query twice → identical
`fusion_top_k_ids/scores/ranks`) — optional, not required to close the story.

---

## RK-55 — Add failure and fallback outcome logging (Goal 10, 3 pts) — ▶ OUTSTANDING

**What to implement.** Populate `fallback_reason` and `failed_stage` (columns already exist) at
every pipeline exit that is not a clean answer, and preserve a **partial log** rather than dropping
the row on error. Use stable reason-code constants.

**Files/modules touched.**
- `hub/retrieval/pipeline.py` — surface the failed stage (reuse `STAGE_*` constants) and a
  fallback reason on the `PipelineResult` for each non-answer outcome (no results, low confidence,
  validation-blocked, retrieval error, rewrite error).
- `hub/api/routes_query.py` — write `failed_stage` + `fallback_reason` on every path including
  exception handlers; ensure a row is always written (partial on error).
- Define reason-code constants centrally (e.g., a small `hub/retrieval/outcomes.py` or constants in
  `pipeline.py`): `no_results | low_confidence | validation_blocked | retrieval_error |
  rewrite_error` (matches the schema comment).
- `hub/db/schema.py` — **no change** (columns exist).

**Acceptance criteria.**
- Each non-answer outcome writes the correct `fallback_reason`; exceptions set `failed_stage`
  to the stage that raised and still persist a row.
- Clean answers leave both fields null.
- Reason codes come from the shared constant set (no ad-hoc strings).

**Tests to write.**
- New `hub/tests/test_failure_logging.py`: simulate each failure path (empty KB, sub-threshold
  score, validation block, forced exception in retrieve/rewrite) → assert exact `fallback_reason`
  / `failed_stage` and that a row persisted.
- Integration via `TestClient` on `routes_query`: forced error still returns a safe response and
  logs a partial row.

**Dependencies / DoD.** Pairs with Phase 4 (so compound paths inherit it). **Done when** every
pipeline exit is attributable from logs and tests cover all reason codes.

---

## RK-32 — Log validation and publish audit events (Goal 8 + Goal 10, 3 pts) — ◐ PARTIALLY DONE

**Already in place (verified in merge).** The audit data model and the *review* half are done:
- Tables: `KBPublishAttempt` (`kb_publish_attempts`), `KBValidationResult` (`kb_validation_results`
  — one row per rule check: `rule_id`, `severity`, `passed`, `message`, `kb_version`,
  `publish_attempt_id`), `KBReviewDecision` (`kb_review_decisions` — `reviewer_id`, `decision`,
  `reason_code`, `notes`), `KBItemValidationStatus`.
- `hub/api/routes_admin.py::submit_metadata_review` → `hub/validation/review.py::
  apply_metadata_review` persists `kb_item_validation_status` + `kb_review_decisions` with the
  authenticated `reviewer_id` (operator identity) and reason code.
- `/admin/publish` runs the gate (`build_publish_gate_handoff`) and blocks under strict policy.

**Remaining to implement.** The *publish-time persistence* is the gap — `/admin/publish` currently
only `logger.info`s the gate outcome:
- On `/admin/publish`, create a `KBPublishAttempt` row (KB version, outcome pass/block/warn,
  counts of approved/quarantined, actor, timestamp).
- Persist the per-rule `KBValidationResult` rows produced by the gate run, linked to that
  `publish_attempt_id` (so rule firings at publish time are captured, not just at review time).
- Backfill `publish_attempt_id` linkage on the validation results / review decisions for that run.

**Files/modules touched.**
- `hub/api/routes_admin.py` — `publish_kb` (~line 441): write `KBPublishAttempt` + persist gate
  `KBValidationResult` rows.
- `hub/validation/metadata.py` — expose the per-rule results from the gate run for persistence
  (results are computed in `validate_metadata` / `build_publish_gate_handoff`).
- `hub/db/schema.py` / `hub/db/migrate_schema.py` — **no new tables** (all exist); add columns only
  if a field is missing.

**Acceptance criteria.**
- `/admin/publish` writes one `KBPublishAttempt` row per attempt (KB version, outcome, counts,
  actor, timestamp).
- The gate's per-rule results persist as `KBValidationResult` rows linked to that attempt.
- Review decisions/validation results are joinable to the publish attempt by `publish_attempt_id`.
- Strict-block and warn paths both record an attempt.

**Tests to write.**
- New `hub/tests/test_publish_audit.py`: publish (pass / block / warn) → assert a `KBPublishAttempt`
  row + linked `KBValidationResult` rows with correct rule IDs/severity, actor, KB version.
- Extend `hub/tests/test_publish_gate.py`: gate run persists results (currently it does not assert
  audit).

**Dependencies / DoD.** Depends on Phase 2 core + review audit (done). **Done when** every publish
attempt and its rule results are persisted (not just logged) and tests pass. Closing this flips
Phase 2 from ◐ to ✅.
