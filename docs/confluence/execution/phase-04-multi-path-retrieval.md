---
title: Execution — Phase 4 — Multi-path / compound retrieval
parent: Execution Plan
---

# Phase 4 — Multi-path / compound retrieval (Goal 5, +4, 7, 12, 10)

## Objective and scope

Handle compound / multi-intent resident queries by decomposing into intent-scoped retrieval paths,
running retrieval per path, and merging deterministically with explicit priority rules
(safety/medical first), so multi-part asks surface complete primary + secondary evidence
(e.g. "high fever + nearest doctor"). Stay within deterministic top-2 pathing — **not** a planner
or agent. 63 pts equivalent (Slice 5 = 8 stories; Slice 6A observability folded into Phase 5 but
two of its logging stories are exercised here).

## Gating decisions (resolve first with dev-research)

- **D7 — decomposition rule:** top-2 intents only vs bounded top-3 when confidence is high.
  *Recommended default:* top-2 (matches docs); make the cap a config constant.
- **D8 — merge strategy + priority order + secondary-output contract:** strict priority-first vs
  RRF vs priority-bucket-then-RRF; finalize order (proposed: medical > safety > shelter ops >
  general); define how secondary guidance / SOS offer appears in the response payload.

## Dependencies

Phase 3 hybrid retrieval (done) — multi-path reuses it per path. Phase 0/1 (pipeline, filters,
clarification). **RK-37** (per-path/per-component contribution logging) is already done; pair this
with **RK-55** (so compound paths emit failure/fallback logging). Intent classification
(`hub/retrieval/intent.py`) must expose top-2 with confidences.

## Ordered execution steps

1. Expose top-2 intents + confidences from `intent.py`; add compound-detection threshold/flag.
2. Build per-intent path queries (normalized text + intent-specific constraints), respecting
   clarification selection and filter policy.
3. Run retrieval per path (reuse hybrid `search.retrieve`), capturing per-path top-k + scores +
   candidate counts; handle zero-result paths safely.
4. Implement deterministic merge (priority + dedupe + tie-breaks) per D8.
5. Shape primary/secondary response outputs in the response model + formatter.
6. Add evidence attribution (producing path/intent, per-path rank/score, merged rank/score).
7. Wire compound lifecycle + merge logging (uses existing `query_logs` JSON fields + new compound
   fields if needed).
8. Build compound evaluation scenarios in `hub/eval/`.

---

## Work items

### S5.1 — Detect compound queries using top-2 intents (5 pts)
- **Implement.** In `hub/retrieval/intent.py`, return ranked intents with confidences (≥2). Add
  `is_compound` detection: both top intents above a configured threshold
  (`RESKIOSK_COMPOUND_MIN_CONF`). Preserve single-path behavior otherwise. Set a compound flag on
  the pipeline context in `hub/retrieval/pipeline.py`.
- **Files.** `hub/retrieval/intent.py`, `hub/retrieval/pipeline.py`.
- **Gates.** D7.
- **Acceptance.** Compound query sets `is_compound=True` with both intents + confidences recorded;
  non-compound query leaves single-path flow untouched; threshold is config-driven.
- **Tests.** New `hub/tests/test_compound_detection.py` — compound vs non-compound fixtures;
  threshold boundary; determinism (same input → same intents/flag).

### S5.2 — Build intent-scoped retrieval path queries (5 pts)
- **Implement.** One path query per detected intent, carrying the normalized query + intent-specific
  enrichment/constraints; respect clarification resolution and hard/UI/inferred filter precedence.
- **Files.** `hub/retrieval/pipeline.py` (new helper, e.g. `build_path_queries`), `hub/retrieval/
  filter_policy.py` (reuse), possibly `hub/retrieval/rewriter.py` for per-path constrained rewrite.
- **Gates.** D7, D8 (constraint shape).
- **Acceptance.** Each path query has its intent, normalized text, and applied filters; filters
  obey precedence per path; logged.
- **Tests.** Extend `test_compound_detection.py` or new `test_path_queries.py` — correct number of
  paths, per-path filters applied, clarification respected.

### S5.3 — Run retrieval separately per compound path (8 pts)
- **Implement.** Execute `search.retrieve` (hybrid where available) independently per path; return
  per-path top-k evidence IDs, scores, ranks, candidate counts, and per-path latency; a zero-result
  path must not fail the whole request.
- **Files.** `hub/retrieval/search.py` (multi-path entry, e.g. `retrieve_multipath`),
  `hub/retrieval/pipeline.py`.
- **Gates.** none beyond D7/D8.
- **Acceptance.** Both-path success, one-path-empty, and filter-removed-candidates all handled;
  per-path outputs captured with scores/ranks/counts/latency.
- **Tests.** Extend `hub/tests/test_hybrid_retrieval.py` + new `test_multipath_retrieval.py` —
  the three cases; determinism per path.

### S5.4 — Merge compound path results deterministically (8 pts)
- **Implement.** Merge strategy per D8: apply priority rules (medical/safety first), dedupe evidence
  across paths, stable tie-breaks (e.g. `(priority desc, merged_score desc, evidence_id asc)`),
  optional RRF within priority buckets. Reuse `fusion.py` helpers where sensible.
- **Files.** new `hub/retrieval/multipath_merge.py` (or extend `fusion.py`), `hub/retrieval/
  pipeline.py`.
- **Gates.** **D8.**
- **Acceptance.** Deterministic merged ordering for fixed KB/config/query; safety/medical never
  buried; duplicates collapsed with attribution preserved; near-tie handled by explicit tie-break.
- **Tests.** New `hub/tests/test_multipath_merge.py` — priority ordering, dedupe, tie-break,
  near-tie; **run-twice determinism**.

### S5.5 — Add evidence attribution for compound results (5 pts)
- **Implement.** Attach producing path/intent to each returned item; capture path rank, path score,
  merged rank, merged score; preserve info when an item appears in multiple paths; bound to top-k.
- **Files.** `hub/models/api_models.py` (evidence item fields), `hub/retrieval/multipath_merge.py`,
  `hub/retrieval/formatter.py`/`formatter_contract.py`.
- **Acceptance.** Every returned evidence item identifies its path/intent and both ranks/scores;
  multi-path duplicates retain all path memberships; response identifies primary vs secondary.
- **Tests.** Extend `test_multipath_merge.py` — attribution fields present and correct.

### S5.6 — Support primary and secondary compound response outputs (5 pts)
- **Implement.** Represent primary evidence/guidance and secondary evidence/guidance separately in
  the response payload + formatter; ensure urgent/safety content isn't buried; preserve single-intent
  behavior. Define the secondary/SOS contract per D8.
- **Files.** `hub/models/api_models.py`, `hub/retrieval/formatter.py`, `hub/api/routes_query.py`,
  `docs/openapi.yaml` (update response schema), kiosk consumer noted for Phase 10.
- **Gates.** **D8** (output contract).
- **Acceptance.** Compound answer returns structured primary + secondary; single-intent answer
  unchanged; openapi updated.
- **Tests.** Integration via `TestClient` on `routes_query` — compound request yields primary +
  secondary; non-compound unchanged.

### S5.7 — Log compound lifecycle and merge decisions (3 pts)
- **Implement.** Log compound trigger, top-2 intents, path queries, per-path evidence, merge
  strategy, dedupe behavior, final ordering. Reuse existing `query_logs` JSON fields; add compound-
  specific columns only if needed (idempotent migration).
- **Files.** `hub/api/routes_query.py`, possibly `hub/db/schema.py` + `hub/db/migrate_schema.py`
  (e.g. `compound_detected`, `compound_paths` JSON), `hub/retrieval/pipeline.py`.
- **Gates.** D9 (if new columns — align storage approach).
- **Acceptance.** A compound query's full lifecycle is reconstructable from one log row;
  bounded payloads; reason for non-compound is implicit (flag false).
- **Tests.** New `hub/tests/test_compound_logging.py` — fields populated, bounded, reproducible.

### S5.8 — Create compound retrieval evaluation scenarios (3 pts)
- **Implement.** 3–5 scenarios in `hub/eval/data/` (medical+location, safety+shelter-ops,
  basic-needs+schedule) with expected primary/secondary evidence; a runner comparing single-path vs
  multi-path; confirm deterministic final ranking for a fixed KB version/config.
- **Files.** `hub/eval/data/compound_eval.json` (or similar), `hub/eval/compound_eval.py`,
  `hub/tests/test_compound_eval.py`.
- **Acceptance.** Scenarios run offline against the fixed snapshot; expected primary/secondary met;
  determinism asserted.
- **Tests.** `test_compound_eval.py` runs the set and checks expectations + reproducibility.

---

## Phase 4 Definition of Done

A defined compound scenario (e.g. "high fever + nearest doctor") returns correct primary +
secondary outputs; logs show per-path evidence and the final merge decision; results are
deterministic for a fixed KB version/config/query; D7 and D8 recorded as resolved; all Phase 4
tests + the run-twice determinism checks pass; single-intent behavior unchanged; openapi updated.
