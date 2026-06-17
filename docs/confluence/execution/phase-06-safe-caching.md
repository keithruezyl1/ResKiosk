---
title: Execution — Phase 6 — Safe caching
parent: Execution Plan
---

# Phase 6 — Safe caching (Goal 11) — ✅ COMPLETE

> **STATUS: COMPLETE** (D10/D11 resolved). `hub/retrieval/response_cache.py`:
> config-aware, in-memory, TTL (300s default) + LRU response cache. Key =
> normalized_query | intent | language | ui_filter | exclude_ids | kb_version |
> config_signature (D10 — hash of retrieval-affecting config + policy files).
> Safety-critical intents (safety/emergency/medical/children/special_needs)
> **bypass** (D11). /query checks after the pipeline and before retrieval+LLM
> formatting; caches only clean non-safety DIRECT_MATCH; hits still write an
> attributable query_logs row (cache_status hit|miss|bypass). /admin/publish
> calls invalidate_response_cache(). KPI report surfaces hit/miss/bypass + hit rate.
> 156-test suite green; app boots. **Deferred:** safety re-validation, single-flight,
> cross-worker shared cache.

## Objective and scope

Add response-level caching for performance **only after** Phase 5 metrics show stable, correct
behavior — without ever serving stale answers across a KB/config version boundary. Optional /
parallelizable; **not** a blocker for the multimodal track (Phases 7–10).

## Gating decisions

- **D10 — config-version signal:** existing version table vs hash of relevant config.
- **D11 — cache safety scope:** which intents are safety-critical (re-validation before serving);
  whether to add single-flight/coalescing this increment.

## Dependencies

Phase 5 (metrics trustworthy, so caching can't hide regressions) + Phase 0 pipeline. Reuses
`kb_version` authority (`system_version`/publish path) and config env (`RESKIOSK_RRF_K`,
`RESKIOSK_HYBRID_TOP_K`, bias state).

## Ordered execution steps

1. Define the version-aware cache key structure (fail-closed on missing components).
2. Implement response-level cache storage with the key.
3. Add TTL policy + bypass rules.
4. Invalidate on KB publish.
5. Invalidate on config update.
6. Log hit/miss/bypass decisions.
7. (Optional) safety re-validation for high-stakes intents.
8. Cache behavior tests.

---

## Work items (Slice 6B backlog — 44 pts)

### S6B.1 — Define version-aware cache key structure (5 pts)
- **Implement.** Key = `normalized_query` + `resolved_intent` (+ compound structure) +
  `applied_filters` (UI/inferred/hard) + `kb_version` + `config_version/hash`. Store a hashed key;
  keep decomposed components for logging. **Fail closed** (bypass) if any component is missing.
- **Files.** new `hub/services/response_cache.py` (key builder), `hub/retrieval/pipeline.py` (inputs).
- **Gates.** D10.
- **Acceptance.** Identical requests → identical key; any version/filter change → different key;
  missing component → bypass (no key).
- **Tests.** New `hub/tests/test_cache_key.py` — stability, sensitivity to each component, fail-closed.

### S6B.2 — Implement response-level cache storage (8 pts)
- **Implement.** Store/retrieve the formatted response keyed by S6B.1. In-process store (or SQLite
  table `response_cache` via `migrate_schema.py`) — choose smallest viable; must be deterministic and
  observable.
- **Files.** `hub/services/response_cache.py`, optional `hub/db/schema.py` + `migrate_schema.py`,
  `hub/api/routes_query.py` (lookup before pipeline, store after).
- **Acceptance.** Cache hit returns the stored response without re-running retrieval; miss runs the
  pipeline and stores.
- **Tests.** New `hub/tests/test_response_cache.py` — hit/miss roundtrip; stored == fresh response.

### S6B.3 — Add TTL policy and cache bypass rules (5 pts)
- **Implement.** Short TTL (minutes) with optional per-intent overrides; explicit bypass rules
  (e.g., clarification-needed responses are never cached). Version change still invalidates regardless
  of TTL.
- **Files.** `hub/services/response_cache.py`, config env (`RESKIOSK_CACHE_TTL_S`).
- **Gates.** D11 (per-intent overrides).
- **Acceptance.** Expired entries are not served; non-cacheable responses bypass; TTL configurable.
- **Tests.** Extend `test_response_cache.py` — TTL expiry, bypass categories.

### S6B.4 — Invalidate cache on KB publish (5 pts)
- **Implement.** On `/admin/publish`, bump `kb_version` and invalidate entries for older versions.
- **Files.** `hub/api/routes_kb.py`/`routes_admin.py` (publish hook), `hub/services/response_cache.py`.
- **Acceptance.** After publish, no entry from the prior KB version is served.
- **Tests.** Extend `test_response_cache.py` — publish invalidates older-version entries.

### S6B.5 — Invalidate cache on config update (5 pts)
- **Implement.** On relevant config change, bump config version/hash and invalidate prior-config
  entries.
- **Files.** `hub/services/response_cache.py`, config-update path (`hub/api/routes_system.py`).
- **Gates.** D10.
- **Acceptance.** Config change invalidates prior-config entries; no stale answers post-change.
- **Tests.** Extend `test_response_cache.py` — config bump invalidates.

### S6B.6 — Log cache hit, miss, and bypass decisions (3 pts)
- **Implement.** Log hit/miss/bypass + reason, TTL used, invalidation trigger/scope, latency saved;
  store hashed key + decomposed components.
- **Files.** `hub/api/routes_query.py`, `hub/db/schema.py` (+ migration) for cache log fields or reuse
  `query_logs`.
- **Acceptance.** Every request records cache decision; bypass reasons explicit; cache never hides a
  version change.
- **Tests.** Extend `test_response_cache.py` — decisions logged with reasons.

### S6B.7 — Add safety re-validation for cached high-stakes responses (8 pts)
- **Implement.** For safety-critical intents, run a lightweight retrieval check before serving cache;
  compare top evidence IDs vs cached; bypass if mismatch exceeds a threshold; log the decision.
- **Files.** `hub/services/response_cache.py`, `hub/retrieval/search.py` (light check).
- **Gates.** **D11** (which intents).
- **Acceptance.** High-stakes cached answer is re-validated; mismatch → bypass + fresh retrieval +
  log.
- **Tests.** Extend `test_response_cache.py` — re-validation bypass on mismatch.

### S6B.8 — Add cache behavior tests (5 pts)
- **Implement.** Consolidated behavioral suite: correctness, version boundaries, TTL, bypass,
  observability, re-validation.
- **Files.** `hub/tests/test_response_cache.py` (comprehensive).
- **Acceptance.** Suite proves no stale answers across version boundaries and full observability.
- **Tests.** This item *is* the test consolidation.

---

## Phase 6 Definition of Done

Cache invalidates on publish/config update with no stale answers after a version change;
hit/miss/bypass + key fields always logged; cache does not hide regressions; D10/D11 recorded; all
cache tests pass. Phase is optional — may be skipped without blocking Phases 7–11.
