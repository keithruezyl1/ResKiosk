---
title: ResKiosk AAIH — Execution Plan (Index)
parent: ResKiosk AAIH Development Home
status: active
note: |
  Companion to development-plan.md. This is the buildable, code-against execution plan.
  No team/owner split — all work items are ours. Story points are size hints only.
  Deadlines/dates from the original sprint docs are intentionally ignored.
---

# ResKiosk AAIH — Execution Plan

This is the **developer-facing** plan: ordered, concrete, and grounded in the actual
repository. It expands every remaining phase of `development-plan.md` into execution steps,
per-work-item build specs (files/modules/endpoints/tables touched, acceptance criteria, tests),
dependencies, gating decisions, and a definition of done.

Per-phase detail lives in [`execution/`](execution/). This file holds the **overall execution
order**, the **decisions to settle before each phase**, and the **testing/verification strategy**.

## How to use this plan (per-story loop)

For every work item below, follow the agreed methodology:

1. **dev-research** *(only if the approach/decision is unresolved)* — produce a decision brief,
   resolve the gating D-number.
2. **Brainstorm** — confirm scope and acceptance criteria against this doc; update the story's
   `slicex_storyx_context.md` running context (per `suggested-workflow-for-user-stories.md`).
3. **Write failing tests first** (the "tests to write" list per item).
4. **Implement** to green; keep strictly in scope.
5. **Refactor**; re-run the full suite.
6. **Subagent code review** against the plan, then mark done.

## Repository map (authoritative references used throughout)

- **Hub (Python/FastAPI)** — `hub/`
  - Pipeline & retrieval: `hub/retrieval/` — `pipeline.py`, `search.py`, `intent.py`,
    `normalizer.py`, `rewriter.py`, `lexical.py`, `fusion.py`, `filter_policy.py`,
    `rlhf_bias.py`, `embedder.py`, `formatter.py`, `formatter_contract.py`, `translator.py`,
    `inventory.py`
  - Validation: `hub/validation/` — `metadata.py`, `review.py`
  - DB: `hub/db/` — `schema.py`, `migrate_schema.py` (idempotent ALTER), `init_db.py`,
    `session.py`, `seed.py`, `evac_sync.py`
  - API routers: `hub/api/` — `routes_query.py`, `routes_kb.py`, `routes_admin.py`,
    `routes_system.py`, `routes_emergency.py`, plus auth/cloud/lora/messages/network
  - Models: `hub/models/api_models.py`
  - Eval: `hub/eval/` — `exact_term_retrieval_eval.py`, `data/`
  - Tests: `hub/tests/` — `test_pipeline_order.py`, `test_filter_policy.py`, `test_fusion.py`,
    `test_hybrid_retrieval.py`, `test_metadata_validation.py`, `test_publish_gate.py`,
    `test_query_log_schema.py`, `test_exact_term_retrieval_eval.py`
  - Taxonomy data: `hub/taxonomy/taxonomy_v1.json`, `hub/taxonomy/legacy_category_map_v1.json`
- **Admin console (React/Vite)** — `console/`
  - Pages: `console/src/pages/*.jsx` (`KBViewer`, `LogsViewer`, `QueryTracker`,
    `ShelterConfig`, `FAQManager`, `Dashboard`, …)
  - API client: `console/src/api/hubClient.js`
- **Kiosk (Android/Kotlin, Jetpack Compose)** — `kiosk/`
  - Network: `kiosk/app/src/main/java/com/reskiosk/network/HubApiClient.kt`
  - UI: `kiosk/app/src/main/java/com/reskiosk/ui/MainKioskScreen.kt`, `ui/HubScreen.kt`
  - VM: `kiosk/app/src/main/java/com/reskiosk/viewmodel/KioskViewModel.kt`
  - Tests: `kiosk/app/src/test/java/com/reskiosk/...`
- **API contract** — `docs/openapi.yaml`

> There is **no `n8n/`** directory in this repo; ignore that reference. The web admin is
> `console/`, not `web/`.

### Schema reality check (already in place from Sprints 1–3)

`query_logs` (in `hub/db/schema.py`) **already contains** many fields later phases need —
`lexical_top_k_ids/scores/ranks`, `vector_top_k_ids/scores/ranks`, `fusion_strategy` +
`fusion_top_k_ids/scores/ranks`, `bias_enabled/bias_applied_count/bias_top1_changed/bias_detail`,
`fallback_reason`, `failed_stage`, `clarification_*`, taxonomy `ui_*`/`inferred_*`/`widening_*`,
`intent_label/intent_confidence`, `pipeline_stage_log`, `kb_version`, `latency_ms`.

**Implication:** several carried-forward/Phase-5 items are about **populating** these columns
correctly and consistently, not adding schema. Each item below states whether it is "populate"
vs "schema add."

---

## Recommended overall execution order

The dependency chain is mostly linear; one branch (caching) is optional/parallel.

```
[Post-merge status: RK-37 is DONE (contribution logging landed). Close the rest first.]
  RK-32 remainder (Phase 2 publish-attempt + per-rule result persistence) ─┐
  RK-55           (Phase 5 failure/fallback logging)                       ─┘→ trustworthy logs

Phase 4  Multi-path / compound retrieval
   │
Phase 5  Observability completion (RK-55 + KPIs + grounding-proxy + readable logs)
   │
   ├─ Phase 6  Safe caching            (OPTIONAL / can run in parallel after Phase 5)
   │
   └─ Phase 7  Multimodal schema
          │
        Phase 8  Image asset lifecycle
          │
        Phase 9  Image embeddings & retrieval  (+ deferred Goal 9 bias tuning)
          │
        Phase 10 Kiosk rendering & multimodal demo
          │
        Phase 11 Stabilization & release
```

Practical sequencing notes:

- **RK-37 is already done** (contribution logging landed in the Sprint 1–3 merge). Do **RK-55**
  before/with Phase 4 so multi-path emits complete failure logs from day one. Do the **RK-32
  remainder** (publish-attempt + per-rule result persistence) anytime before Phase 5 KPI work.
- Phase 5 KPIs must run over complete logs → the RK-32 remainder + RK-55 are true prerequisites.
- Phase 6 (caching) depends only on Phase 5 metrics being trustworthy; it is **not** a blocker for
  the multimodal track and may be deferred indefinitely without blocking Phases 7–10.
- The multimodal track is strictly ordered 7 → 8 → 9 → 10 (schema → assets → embeddings → kiosk).

---

## Decisions to settle before coding each phase

Resolve the gating decision(s) with the **dev-research** skill and record the choice in
`development-plan.md`'s decision register before starting the phase.

| Before… | Must resolve | Summary |
|---------|--------------|---------|
| RK-32 remainder, RK-55 | (none) | ✅ **DONE.** RK-37 done; RK-55 populates `fallback_reason`/`failed_stage` (incl. partial-row-on-error); RK-32 persists `KBPublishAttempt` + per-rule `KBValidationResult` at the gate. Also fixed: `routes_admin` dropped imports (app failed to boot). 95 tests green. |
| Phase 4 | ✅ DONE | Multi-path compound retrieval implemented: `multipath_merge.py` (priority-bucket-then-RRF), `search.retrieve_multipath`/`build_path_queries`/`build_compound_outputs`, `secondary_evidence`+`sos_offered` response, `query_logs.compound_detected`/`compound_paths`, eval scenarios. D7/D8 resolved. 115 tests. |
| Phase 5 | ✅ D9 resolved | extend `query_logs` (latency-breakdown + grounding columns) + KPIs computed on read; rule-based offline grounding proxy (`rule_v1`); structured-only exports + 30-day transcript retention purge |
| Phase 6 | **D10, D11** | Config-version signal for cache key; which intents are safety-critical; single-flight? |
| Phase 7 | **D12, D13** | `kb_articles` extend-in-place vs new item table; metadata columns vs JSON; evidence-log shape |
| Phase 8 | **D14** | Image binary storage (filesystem vs object store) + reference representation. *(D15 resolved: 4-state model + thumbnail+rendition.)* |
| Phase 9 | **D16, D17, D5** | CLIP vs SigLIP (+ version/preprocessing/license); similarity floor + top-N policy + image PII; bias state identifier / per-path vs per-merge |
| Phase 10 | **D17** | Confidence display policy (carried from Phase 9) |
| Phase 11 | (none) | Validation only |

Already resolved: **D1–D4, D6** (Sprints 1–3), **D15** (4-state asset model), **D7, D8** (Phase 4), **D9** (Phase 5 — dev-research, see register).

---

## Testing & verification strategy

The increment's defining constraint is **determinism/reproducibility for a fixed KB version +
config + normalized query + filters**. Tests are organized in four tiers.

### 1. Unit tests (`hub/tests/`, pytest)
Pure-function and module-level. Extend existing files where possible (`test_fusion.py`,
`test_filter_policy.py`, `test_metadata_validation.py`, …). New modules get new `test_*.py`.
Keep tests offline and DB-light (use an in-memory or temp SQLite via `RESKIOSK_DB_PATH`).

### 2. Integration tests
Exercise the pipeline (`hub/retrieval/pipeline.py`) and routers (`hub/api/routes_query.py`,
`routes_kb.py`, `routes_admin.py`) against a seeded temp DB. Use FastAPI `TestClient`. Verify
stage order, filter precedence, validation gating, multi-path merge, and that logs are written.

### 3. Determinism / reproducibility checks (cross-cutting — required every phase)
For each retrieval-affecting item, add a **"run twice, assert identical"** test:
- Fix `kb_version` + config (env: `RESKIOSK_RRF_K`, `RESKIOSK_HYBRID_TOP_K`, bias state, model
  version) and a fixed seeded KB snapshot.
- Run the same normalized query/filters twice; assert identical ordered evidence IDs, scores,
  ranks, and tie-break outcomes.
- Assert tie-breaks are explicit and stable (e.g. fusion `(fusion_score desc, article_id asc)`;
  image `(score desc, evidence_id asc)`).
- Snapshot the structured log row and diff: same inputs → same logged decision fields.
Maintain a small **fixed KB snapshot fixture** + the `hub/eval/` evaluation sets as the golden
corpus; reuse for regression in Phase 11.

### 4. End-to-end (Phase 10/11)
Hub + console + kiosk. Text-query E2E, clarification E2E, hybrid E2E, compound E2E, multimodal
E2E; plus benchmarking (latency p50/p95, retrieval stability, image retrieval, kiosk image load)
and regression against the fixed KB snapshot. Kiosk-side: Kotlin unit tests under
`kiosk/app/src/test/...` for rendering/fallback logic.

### Per-item discipline
Every work item lists **"tests to write"**. Write them **first** (red), implement to green, then
add the determinism check if the item affects retrieval/ranking/logging output.

---

## Per-phase documents

- [Carried-forward logging — RK-32, RK-37, RK-55](execution/00-carried-forward-rk32-rk37-rk55.md)
- [Phase 4 — Multi-path / compound retrieval](execution/phase-04-multi-path-retrieval.md)
- [Phase 5 — Observability & trust completion](execution/phase-05-observability.md)
- [Phase 6 — Safe caching](execution/phase-06-safe-caching.md)
- [Phase 7 — Multimodal schema](execution/phase-07-multimodal-schema.md)
- [Phase 8 — Image asset lifecycle](execution/phase-08-image-asset-lifecycle.md)
- [Phase 9 — Image embeddings & semantic retrieval (+ bias tuning)](execution/phase-09-image-embeddings-retrieval.md)
- [Phase 10 — Kiosk image rendering & multimodal demo](execution/phase-10-kiosk-rendering-demo.md)
- [Phase 11 — Stabilization & release](execution/phase-11-stabilization.md)
