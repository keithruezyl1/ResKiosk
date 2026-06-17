---
title: Execution — Carried-forward logging (RK-32, RK-37, RK-55)
parent: Execution Plan
---

# Carried-forward logging — RK-32, RK-37, RK-55

## Objective and scope

Close the three Sprint-3 logging stories that were not finished. All three are **Goal 10**,
3 pts each, and all are about making the structured logs **complete and trustworthy** so Phase 5
KPI computation runs over real data. Two of the three are largely **populate existing columns**
(the schema already exists in `query_logs`); RK-32 adds publish/validation audit logging.

Do these first — they are small and unblock Phase 5.

## Gating decisions

None. D6 (hybrid specifics) is resolved. RK-32 storage may reuse the existing audit approach in
`hub/validation/review.py`; if a dedicated table is wanted, align with D9 but a simple log table
or structured logger is acceptable for MVP.

## Ordered execution steps

1. RK-37 (retrieval contribution population) — smallest, in the hot path; do with/just before Phase 4.
2. RK-55 (failure/fallback population) — pipeline-wide; do alongside Phase 4 so multi-path inherits it.
3. RK-32 (publish/validation audit events) — independent; do anytime before Phase 5 KPIs.

---

## RK-37 — Add hybrid retrieval contribution logging (Goal 4 + Goal 10, 3 pts)

**What to implement.** Ensure every retrieval that runs hybrid fusion **populates** the per-item
contribution fields already defined on `query_logs`: `lexical_top_k_ids/scores/ranks`,
`vector_top_k_ids/scores/ranks`, `fusion_strategy`, `fusion_top_k_ids/scores/ranks`. The fusion
layer already computes these (`FusedCandidate` carries `vector_rank`, `lexical_rank`,
`vector_score`, `lexical_score`, `overlap_count`); wire them through to the log write.

**Files/modules touched.**
- `hub/retrieval/fusion.py` — confirm `FusionOutput`/`FusedCandidate` expose per-item lexical vs
  vector vs fused contribution (already present); add a small serializer helper if needed.
- `hub/retrieval/search.py` — ensure the retrieve result returns the fusion breakdown to the caller.
- `hub/api/routes_query.py` — at log-write time, serialize the breakdown into the existing
  `lexical_*`, `vector_*`, `fusion_*` columns (JSON arrays, top-5).
- `hub/db/schema.py` — **no change** (columns exist).

**Acceptance criteria.**
- For a hybrid query, the written `query_logs` row has non-null `lexical_top_k_*`,
  `vector_top_k_*`, `fusion_strategy="rrf"`, and `fusion_top_k_*`, each a JSON array of length
  ≤ `RESKIOSK_HYBRID_TOP_K`.
- IDs in `fusion_top_k_ids` reconcile with the returned evidence order.
- Vector-only path (no lexical) logs lexical fields as empty arrays, not null-crashes.

**Tests to write.**
- Extend `hub/tests/test_hybrid_retrieval.py`: assert contribution fields are populated and lengths
  bounded; assert each fused ID is traceable to a lexical and/or vector rank.
- Determinism: same query twice → identical `fusion_top_k_ids/scores/ranks`.

**Dependencies / DoD.** Depends on Phase 3 (done). **Done when** every hybrid query writes a
complete, bounded, reproducible contribution breakdown and tests pass.

---

## RK-55 — Add failure and fallback outcome logging (Goal 10, 3 pts)

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

## RK-32 — Log validation and publish audit events (Goal 8 + Goal 10, 3 pts)

**What to implement.** Emit auditable events for the validation/publish lifecycle: rule firings,
reviewer decisions (approve/reject/override), and the publish gate outcome — each traceable to
operator identity and KB version.

**Files/modules touched.**
- `hub/validation/metadata.py` — emit a structured audit event per rule firing (rule id, severity,
  item id, result).
- `hub/validation/review.py` — emit events on approve/reject/override with reviewer + reason code.
- `hub/api/routes_kb.py` / `hub/api/routes_admin.py` — on `/admin/publish` (gate outcome) emit a
  publish-audit event with KB version, pass/block/warn, and counts of approved/quarantined.
- Storage: prefer reusing existing audit storage in `review.py`; if a table is needed, add an
  idempotent migration in `hub/db/migrate_schema.py` + model in `hub/db/schema.py`
  (e.g., `validation_audit_events`). Keep aligned with D9 but do not block on it.
- Console (optional, read-only): surface events in `console/src/pages/LogsViewer.jsx` if cheap.

**Acceptance criteria.**
- Validating a KB snapshot writes one audit event per fired rule with stable rule IDs + severity.
- Each review decision and override writes an event with reviewer identity, reason code, KB version.
- `/admin/publish` writes a gate-outcome event (pass/block/warn + counts), tied to KB version.
- Events are queryable/joinable by KB version and item id.

**Tests to write.**
- Extend `hub/tests/test_metadata_validation.py` and `test_publish_gate.py`: assert audit events
  are emitted for rule firings and for the gate outcome.
- New `hub/tests/test_validation_audit.py`: approve/reject/override emit correct events with
  identity + reason + KB version.

**Dependencies / DoD.** Depends on Phase 2 core (done). **Done when** the full
validation→review→publish path is auditable from events and tests pass. Closing RK-32 flips
Phase 2 from ◐ to ✅.
