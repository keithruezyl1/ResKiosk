---
title: ResKiosk AAIH — Phased Development Plan (Remaining Work)
parent: ResKiosk AAIH Development Home
status: active
note: Deadlines/dates from the original sprint docs are intentionally omitted. The project is no longer time-boxed; phases are sequenced by dependency, not by calendar.
---

# ResKiosk AAIH — Phased Development Plan

This plan covers **all remaining work** to finish the AAIH product increment. It
reorganizes the original sprint/slice scope into **dependency-ordered phases**
(no dates). It is re-baselined to reflect that **Sprints 1, 2, and 3 are fully
delivered**, and starts from what actually remains. Every one of the 12 increment
goals is covered, including the two deferred items (safe caching,
feedback-ranking tuning) — nothing is dropped.

**Current baseline (delivered):** Phases 0, 1, **3** (now complete), and the bulk
of Phase 2 are delivered (canonical pipeline + logging skeleton +
taxonomy/filtering, clarify-first UX, trusted-publish validation gate, and hybrid
BM25+vector retrieval with RRF, including the Goal 9 bias-layer integration **and
the full lexical/vector/fusion contribution logging — RK-37**). The Goal 10
**structured query-log schema** is also done.

> **Re-baselined after the Sprint 1–3 merge.** Verified against the merged code:
> **RK-37 is DONE** (`hub/retrieval/search.py` builds the full lexical/vector/fusion
> breakdown; `hub/api/routes_query.py` writes `lexical_*`, `vector_*`,
> `fusion_*` + `bias_*` to `query_logs`). Phase 3 is now ✅ complete.

**Carried forward — still outstanding after the merge (Goal 10):**

- **RK-32 — "Log validation and publish audit events"** (Slice 3 / Goal 8 + Goal
  10, 3 pts) — **partially done.** The audit *tables* exist and are populated for
  reviews: `kb_publish_attempts`, `kb_validation_results` (per-rule firings),
  `kb_review_decisions` (with `reviewer_id` + reason code), `kb_item_validation_status`.
  **Remaining:** wire the `/admin/publish` endpoint to persist a `KBPublishAttempt`
  row + the per-rule `KBValidationResult` rows at gate time (it currently only
  `logger.info`s the gate outcome), and add audit tests. Tracked under **Phase 2**.
- **RK-55 — "Add failure and fallback outcome logging"** (Slice 6A / Goal 10,
  3 pts) — **outstanding.** `query_logs.fallback_reason` / `failed_stage` columns
  exist but are never populated by the query path. Part of **Phase 5**.

Both remaining items are on the critical path to Phase 5 (KPI computation needs
complete, trustworthy logs). **The next remaining feature work is Phase 4
(multi-path / compound retrieval)**; close RK-32 + RK-55 alongside Phases 2–5.

> **Ownership:** there is **no team / per-person split** — all work items are
> ours to do. Story points are retained from the sprint docs as relative size
> estimates only; the per-person "Person N" owner assignments in the sprint
> task-grouping docs are intentionally **not** carried into this plan.

Global constraints carried from the increment docs:

- **English at the retrieval boundary** (non-English handled upstream via NLLB-200).
- **No semantic chunking** this increment; the retrieval unit stays one `kb_articles` row.
- **Determinism + reproducibility**: for a fixed KB version + config + normalized
  query + filters, retrieval results and rankings must be reproducible.
- **Stable evidence IDs** tied to `kb_version`, attributable in logs, throughout.
- **Filter precedence is non-negotiable**: hard system rules > UI filters > inferred intent.
- **Canonical pipeline order** (Goal 12) is a product requirement enforced in every phase:
  `normalize → intent → optional clarification (hard gate) → constrained rewrite → retrieval`.

---

## Goal → Phase coverage map

| Goal | Title | Delivered in |
|------|-------|--------------|
| 12 | Canonical pipeline order | ✅ Phase 0 (done); reinforced every phase |
| 10 | MVP metrics + logging | Skeleton ✅ Phase 0; query-log schema ✅ Phase 3; contribution logging ✅ (RK-37); **outstanding: RK-32 publish-audit wiring (Phase 2), RK-55 failure/fallback (Phase 5)**; KPI computation + reporting, **grounding-proxy review fields, and readable hub log formatting** remain in Phase 5 |
| 7 | Metadata schema + filtering policy | ✅ Phase 0 (done) |
| 6 | Clarification UX before rewriting | ✅ Phase 1 (Sprint 2) |
| 8 | Metadata validation gate | ◐ Phase 2 (Sprints 2–3) — core + review audit done; **RK-32 publish-attempt/rule-result persistence outstanding** |
| 4 | Hybrid retrieval (BM25 + vectors) | ✅ Phase 3 (Sprint 3) — retrieval/RRF + RK-37 contribution logging done |
| 9 | Retrieval quality without heavy reranking | Bias layer ✅ Phase 3; deferred **tuning remains** in Phase 9 |
| 5 | Multi-path / compound retrieval | Phase 4 (next remaining) |
| 11 | Safer caching (version + TTL + refresh) | Phase 6 (deferred); **image-artifact publish invalidation** in Phase 8 |
| 3 | KB schema rework for multimodal | Phase 7 |
| 2 | Image storage as first-class KB assets | Phase 8 — incl. **upload API, content hash, thumbnail + compressed rendition, 4-state model (D15 resolved), admin confirmation/status** |
| 1 | Semantic image search (CLIP/SigLIP) | Phase 9 (embeddings + ingest/publish readiness gate) + Phase 10 (kiosk render, image-first, load optimization, text-only fallback) |

---

## Phase 0 — Backbone & controlled scope (✅ COMPLETE — baseline)

*Original Slices 0 + 1, delivered in Sprint 1 (44 pts). Listed for context; no
remaining work.*

**Already in place:**

- `QueryPipeline` orchestrator (`hub/retrieval/pipeline.py`) enforcing canonical
  stage order with guards + `test_pipeline_order.py`.
- Pipeline stage logging skeleton (bounded payloads; text capped at 120 chars;
  article bodies never logged).
- `ClarificationContext` pause state + `pipeline_status` field; route early-returns
  when clarification is needed.
- Taxonomy v1 (`taxonomy_v1.json`, IDs `rk.tax.<category>.<subcategory>`;
  `taxonomy_nodes` / `taxonomy_edges` / `kb_item_taxonomy` tables; legacy map).
- `kb_articles` metadata columns: `authority`, `scope`, `center_id`, `hub_id`
  (idempotent migration + backfill defaults).
- Hard retrieval rules (exclude `enabled=false` and non-`published`) run before
  UI/inferred filters, with reason codes.
- Filter precedence enforced + logged (`hard` / `UI` / `inferred`); candidate
  counts and fallback reasons logged.

**Definition of done:** met — "Delivered fully," zero carryover.

---

## Phase 1 — Clarify-first UX (✅ COMPLETE — Sprint 2)

*Original Slice 2 (Goals 6, 12 gate, 10).*

**Delivered:** clarification trigger policy (low intent confidence / unclear +
low score / missing scope); taxonomy-backed 2–3 chip options with stable IDs
(`clarification_options: [{ id, label }]`); kiosk chip UI; retry contract
(`selected_taxonomy_node_id` + `original_session_id` + optional override) resuming
the pipeline deterministically; resolutions persisted to
`clarification_resolutions`; clarification lifecycle logging; max-loop cap +
safe fallback.

**Definition of done:** met. Clarification occurs **before** rewrite/retrieval
(verified in logs); resolutions persisted; loop cap + fallback verified.
*(Decisions D1, D2 — resolved during delivery.)*

---

## Phase 2 — Trusted KB publish (◐ NEARLY COMPLETE — Sprints 2–3)

*Original Slice 3 (Goals 8, 10).*

**✅ Delivered:** deterministic metadata validation rule engine (taxonomy
integrity, authority/scope enums, caption sanity, safety-critical checks);
validation status + audit storage (`approved | quarantined | needs_review |
rejected` with rule IDs, severity, reviewer/timestamp/reason); publish gating
(pass / block / warn); MVP human review workflow (approve / reject / override,
tied to KB version); quarantined metadata excluded from resident retrieval.
*(Optional offline LLM-judge assist remains available but non-blocking.)*

**▶ Outstanding (carried forward from Sprint 3 — partially done after merge):**

- **RK-32 — Story 6: "Log validation and publish audit events"** (Goal 8 + Goal
  10, 3 pts). **Already in place:** audit tables `kb_publish_attempts`,
  `kb_validation_results` (per-rule firings: `rule_id`, `severity`, `passed`),
  `kb_review_decisions` (`reviewer_id`, `decision`, `reason_code`, `notes`), and
  `kb_item_validation_status`; the review endpoint persists decisions with operator
  identity. **Remaining:** the `/admin/publish` endpoint runs the gate but only
  `logger.info`s the outcome — wire it to persist a `KBPublishAttempt` row + the
  per-rule `KBValidationResult` rows at gate time, link review decisions/validation
  results to that attempt, and add audit tests.

**Definition of done:** validation correctness is met; **Phase 2 is not fully done
until the publish-attempt + rule-result persistence (RK-32 remainder) is wired and
tested** so every publish/validation decision is captured, not just logged.
*(Decisions D3, D4 — resolved during delivery.)*

---

## Phase 3 — Deterministic retrieval core (✅ COMPLETE — Sprint 3)

*Original Slice 4 (Goals 4, 9 bias layer, 7, 10).*

**✅ Delivered:** BM25-like lexical index over `kb_articles.question` + `tags`
(version-aware, deterministic tokenization); deterministic lexical scoring;
lexical+vector fusion via **RRF** with tie-break `(fused_score desc,
kb_articles.id asc)`; filter policy enforced on both paths; the **Goal 9
feedback-adjusted bias layer integration** (bounded, capped, logged baseline vs
post-bias); exact-term evaluation set; **RK-37 hybrid retrieval contribution
logging** — `hub/retrieval/search.py` emits per-item lexical/vector/fused ids +
scores + ranks + fusion strategy/params/tie-breaks + bias detail, and
`hub/api/routes_query.py` writes them all to `query_logs`.

**Definition of done:** met. Retrieval accuracy/determinism achieved (exact-term
set improved; rankings stable for fixed KB version/config/query; bias layer
respects caps, hard rules, filters); per-component contributions are observable in
the logs. *(Decisions D5, D6 — resolved during
delivery. Cross-encoder reranking remains explicitly out of scope. Goal 9 bias
**tuning** is still deferred — see Phase 9.)*

---

## Phase 4 — Compound correctness / multi-path retrieval (Goal 5, Goal 4, Goal 7, Goal 12, Goal 10) — ▶ NEXT REMAINING

*Original Slice 5.*

**Objective.** Handle compound queries by decomposing into intent-scoped retrieval
paths and merging with explicit, deterministic priority rules so multi-part asks
surface complete evidence (e.g., "high fever + nearest doctor").

**Work items:**

1. **Decomposition** — minimum viable: use the top-2 intents from intent
   classification to form two path queries (post-intent, pre-rewrite, after any
   clarification).
2. **Per-path retrieval** — normalized + intent-specific constrained rewrite, then
   vector or hybrid retrieval, capturing top-k with scores/IDs.
3. **Deterministic merge** — priority-first (medical > safety > shelter ops >
   general; finalize order), dedupe, optional RRF within priority buckets;
   tie-break e.g. `(priority desc, merged_score desc, evidence_id asc)`.
4. **Per-path filtering** — filters applied consistently on each path.
5. **Evidence attribution** — every returned item records producing path/intent,
   its per-path rank/score, and (if fused) merged score/position.
6. **Bounded fanout** — cap number of paths; log truncation when more intents
   detected.
7. **Secondary-output UX contract** — define how secondary results / SOS offers
   are represented to the kiosk.

**Dependencies / rationale.** Depends on Phase 3 (hybrid per-path), Phases 0–1,
and Phase 1 where the scenario needs clarification first.

**Definition of done.** A defined compound scenario returns correct primary +
secondary outputs; logs show per-path evidence and the final merge decision;
results deterministic for fixed KB version/config/query.

**Decisions needed before starting:** see D7, D8.

---

## Phase 5 — Observability & trust completion (Goal 10) — ◐ IN PROGRESS

*Original Slice 6A. The structured-logging schema portion was delivered in Sprint
3; KPI computation + reporting remain.*

**Objective.** Make system quality measurable end-to-end and validate stability
before introducing caching state or multimodal evidence.

**✅ Done (Sprint 3):**

1. **Structured query-log schema** — normalized query, intent label(s) +
   confidence(s), clarification (trigger/options/selection/resolved intent),
   constrained rewrite (constraints + output/hash + fallback reason), evidence IDs
   + ranks + scores, candidate counts pre/post filter, hybrid/multi-path
   attribution, applied filters/widening/fallback reasons, per-stage latency.

**▶ Remaining work items:**

2. **RK-55 — Story 8: "Add failure and fallback outcome logging"** (Goal 10,
   3 pts; carried forward from Sprint 3) — reason codes + failed stage; preserve
   partial logs.
3. **MVP KPI computation** — grounded-answer rate, hallucination proxy
   (unsupported spans vs retrieved evidence), evidence match/stability, latency
   p50/p95 (overall + retrieval + per-stage).
4. **Minimum viable export/reporting** — generate a metrics report per KB version
   / intent / modality (manual queries acceptable). Includes a **fixed evaluation
   query set** (Sprint 5 Slice 6A Story 6, 3 pts) and a **KPI report grouped by KB
   version** (Sprint 5 Slice 6A Story 7, 5 pts).
5. **Grounding-proxy review fields** (Sprint 4 Slice 6A Story 5, 3 pts) — concrete
   review mechanism for the grounding/hallucination proxy: evidence links, manual
   supported/unsupported labels, and reviewer notes, so grounding can be reviewed
   manually or on a sample.
6. **Readable hub log formatting** (Sprint 4 Slice 6A Story 9, 3 pts) — format
   live hub logs with stable IDs, clear stage labels, clear outcomes, and bounded
   payloads, so logs are legible during development, demos, and field operation.
   This is operational legibility, distinct from the structured-log schema (item 1).

> Note: **RK-37 is done** (contribution logging landed in the Sprint 1–3 merge).
> The remaining carried-forward logging items — **RK-32 remainder** (Phase 2
> publish-attempt/rule-result persistence) and **RK-55** (above) — should be closed
> before KPI computation (items 3–4), or the metrics will be computed over
> incomplete logs.
>
> Also: as multi-path lands in Phase 4, confirm the existing schema already
> captures per-path attribution for compound queries (it was specified to); extend
> only if a gap is found.

**Dependencies / rationale.** Schema depends on Phase 0; KPI/reporting depend on
the remaining carried-forward logging items (RK-32 remainder + RK-55) and benefit
strongly from Phases 1–4 (and should reflect Phase 4 multi-path output). Metrics
must be complete **before** multimodal so image evidence is measurable, and before
caching so caching cannot hide regressions.

**Definition of done.** RK-55 closed; grounding-proxy review fields present and
populated for sampled queries; hub logs legible per the readable-log format; a
basic metrics report (over the fixed evaluation set) can be generated per KB
version; logs are sufficient to replay/debug any query decision from stable IDs.

**Decisions still needed:** see D9.

---

## Phase 6 — Safe caching (Goal 11) — *deferred item (44 pts)*

*Original Slice 6B. Deferred in the original plan; included here for completeness.*

**Objective.** Add response-level caching for performance **only after** metrics
demonstrate stable, correct behavior, without ever serving stale answers across a
KB/config version boundary.

**Work items:**

1. **Version-aware cache key** — normalized query + resolved intent (+ compound
   structure) + applied filters (UI/inferred/hard) + `kb_version` +
   config_version/hash; fail closed (bypass) on any missing key component.
2. **TTL** — short (minutes) with optional per-intent overrides; version changes
   still invalidate.
3. **Invalidation hooks** — KB publish bumps version and invalidates older
   entries; config update bumps version/hash and invalidates prior entries.
4. **Observability** — log hit / miss / bypass + reason, TTL used, invalidation
   trigger/scope, latency saved; store hashed key + decomposed components.
5. *(Optional)* **safety re-validation for high-stakes intents** — lightweight
   retrieval check before serving cached output; bypass if top-evidence mismatch
   exceeds threshold; log decision.

**Dependencies / rationale.** Depends on Phase 5 (metrics completion) and Phase 0.
Not a strict blocker for multimodal — can run in parallel with Phases 7–10 if
desired, but correctness/observability come first.

**Definition of done.** Cache invalidates on publish/config update with no stale
answers after a version change; hit/miss/bypass + key fields always logged; cache
does not hide regressions.

**Decisions needed before starting:** see D10, D11.

---

## Phase 7 — Multimodal schema (Goal 3, Goal 10, Goal 7)

*Original Slice 7A. Start of the multimodal track.*

**Objective.** Introduce the minimum schema + evidence-contract changes to
represent both text and image evidence without breaking existing text-only KB
behavior.

**Work items:**

1. **Modality field** (`text | image`, extensible) on KB items; modality-aware
   evidence response shape.
2. **Stable evidence identifiers** for both text and image evidence (continue
   integer IDs / current `kb_articles.id` convention).
3. **Image asset reference fields / link structure** prepared for Phase 8.
4. **Forward-compatible segmentation fields** (`parent_article_id`,
   `segment_index`) stored but **not** used to change the retrieval unit.
5. **Backward-compatible migration** — additive; backfill modality default for
   existing text rows; existing reads/writes unaffected.
6. **Modality-aware evidence logging** support (Goal 10 integration).

**Dependencies / rationale.** Depends on Phases 0, 1, 2 (trusted publish), and 5
(observability). Schema must exist before assets and embeddings.

**Definition of done.** Existing text-only content remains retrievable; evidence
objects can carry modality; image evidence can reference asset records once Phase 8
exists; evidence IDs stable and loggable; migration additive/backward-compatible.

**Decisions needed before starting:** see D12, D13.

---

## Phase 8 — Image asset lifecycle (Goal 2, Goal 11 integration, Goal 10)

*Original Slice 7B.*

**Objective.** Store KB images as durable first-class assets with stable identity,
thumbnails, content hashes, and KB-version linkage so visual evidence can be
displayed, audited, and invalidated safely.

**Work items:**

1. **Durable image asset records** with stable asset IDs — original ref,
   thumbnail ref, content hash (dedupe + integrity), MIME type, size, timestamps,
   minimal audit fields.
2. **Dedicated image upload API for KB assets** (Sprint 5 Slice 7B Story 2, 5 pts)
   — accept supported image uploads, validate file size + MIME type, store original
   reference; log upload failures.
3. **Content-hash generation** (Sprint 5 Slice 7B Story 3, 3 pts) — deterministic
   hashes for identity, dedupe, and integrity.
4. **Deterministic thumbnail generation** (Sprint 5 Slice 7B Story 4, 8 pts) —
   same input → same output (fixed parameters).
5. **Compressed display-size rendition** (Sprint 6 Slice 7B Story 10, 5 pts) —
   generate at least one kiosk-ready compressed rendition with deterministic
   settings; preserve original for audit/detail; preserve aspect ratio; no unsafe
   cropping; store rendition reference + output size/dimensions/format/derivative
   hash. Define which reference the kiosk should prefer (thumbnail vs rendition vs
   original). *No AI enhancement/upscaling.*
6. **4-state image asset processing model** (Sprint 6 Slice 7B Story 5, 5 pts) —
   states `pending | ready | failed | rejected`; only `ready` assets are
   resident-facing; publish never references partially processed assets; failure
   reason codes recorded. *(Resolves decision D15 — see register.)*
7. **KB-version linkage** (Sprint 6 Slice 7B Story 6, 5 pts) — link asset records
   and derived artifacts to the KB version used at publish; query logs can identify
   the KB version that produced image evidence.
8. **Publish-time invalidation/refresh** of image-derived artifacts (Sprint 6
   Slice 7B Story 7, 5 pts) — new KB version uses current artifacts; include KB
   version + content hash in artifact keys; fail closed / bypass affected artifacts
   if invalidation fails (Goal 11 integration).
9. **Broken/missing asset guard** — such assets are never returned as valid
   evidence.
10. **Admin asset confirmation view** (Sprint 6 Slice 7B Story 8, 5 pts) — show
    upload status, original/thumbnail preview, content hash/identity, processing
    errors; allow admin to confirm an asset is ready for KB use; distinguish
    publish-eligible from not-ready; show KB item / taxonomy linkage where
    available. *(Console asset-status display is tracked in Phase 10 work item 6;
    they share asset fields.)*
11. **Asset lifecycle logging** (Sprint 6 Slice 7B Story 9, 3 pts; Goal 10) —
    upload, thumbnail/rendition generation, processing transitions, readiness
    failures, and invalidation events, joinable by asset ID and KB version.

> Scope note: this is asset readiness + debugging support, **not** a polished
> digital-asset-management platform.

**Dependencies / rationale.** Depends on Phase 7 (multimodal schema). Assets must
exist (and be `ready`) before embeddings can be generated reliably (Phase 9). The
upload API + admin confirmation are prerequisites for the embedding-readiness gate
in Phase 9.

**Definition of done.** Assets stored with original ref + thumbnail + compressed
rendition + content hash + KB-version linkage; thumbnails/renditions deterministic;
4-state model enforced (only `ready` assets resident-facing); upload API validates
and stores; admin can confirm asset status; broken assets excluded; KB publish
invalidates/refreshes safely; lifecycle events logged.

**Decisions needed before starting:** see D14. (D15 is now resolved — see register.)

---

## Phase 9 — Image embeddings & semantic retrieval (Goal 1, Goal 10, Goal 7, Goal 8) + feedback-ranking tuning (Goal 9) — *deferred item (5 pts)*

*Original Slice 7C, plus the deferred Goal 9 tuning work.*

**Objective.** Enable text→image semantic retrieval using a locally hosted
vision-language model, fully subject to filtering and validation gating. Also
complete the deferred feedback-ranking **tuning** now that hybrid + multi-path +
metrics exist to measure its effect.

**Work items (image retrieval):**

1. **Select + configure** the CLIP/SigLIP-style image embedding model;
   local/offline loading path; deterministic image preprocessing rules. *(Model
   selection is front-loaded — Sprint 5 Slice 7C Story 1, 5 pts.)*
2. **Image embedding generation service** (Sprint 7 Slice 7C Story 2, 8 pts) — load
   the model, accept a `ready` image asset, apply preprocessing, return a vector of
   known dimension; handle model-load failure safely; smoke test.
3. **Persist embeddings** (Sprint 7 Slice 7C Story 3, 8 pts) with stable image
   evidence/asset ID, KB-version, and model name/version; invalidate/regenerate
   when model or KB version changes.
4. **Embedding generation gated to the ingest/publish step with readiness gating**
   (Sprint 7 Slice 7C Story 4, 5 pts) — trigger generation during the selected
   ingest/publish step; process **only eligible `ready` image assets** (depends on
   the Phase 8 4-state model); **publish must not expose image evidence until its
   embeddings are ready or the evidence is safely marked unavailable**; use stable
   failure reason codes.
5. **Text→image retrieval path** (Sprint 7 Slice 7C Story 5, 8 pts) returning image
   evidence IDs, scores, ranks, and render references; **similarity floor** +
   deterministic tie-break `(score desc, evidence_id asc)` (Story 8, 3 pts);
   low-confidence labeled "possible matches"; safe no-result handling.
6. **Merge image evidence with the text evidence response structure** (Sprint 7
   Slice 7C Story 6, 5 pts) — deterministic mixed-evidence ordering; preserve
   text-only behavior.
7. **Filtering + validation enforcement** for image evidence (Sprint 7 Slice 7C
   Story 7, 5 pts) — exclude disabled / unpublished / quarantined / rejected /
   non-`ready` image evidence; apply UI + inferred filters where metadata exists.
8. **Image retrieval logging** (Sprint 7 Slice 7C Story 9, 3 pts) — model/version,
   evidence IDs, scores, thresholds, latency, display/suppression.

**Work items (deferred Goal 9 tuning, 5 pts):**

9. **Tune the feedback-adjusted bias layer** — calibrate alpha/scale and caps
   using Phase 5 metrics; confirm bias state identifier for reproducibility; verify
   bias never bypasses hard rules, filters, or clarification.

**Dependencies / rationale.** Image work depends on Phases 7, 8 (especially the
4-state `ready` model, which the publish-time readiness gate consumes), 1
(filtering), and 2 (validation). The Goal 9 tuning depends on Phase 3 (bias layer
exists) and Phase 5 (metrics to measure against) — grouped here since it is small
and benefits from a stable, measurable system.

**Definition of done.** English text queries retrieve relevant image evidence with
stable IDs/scores/ranks/render refs; embeddings are generated during ingest/publish
and **no image evidence is exposed until its embeddings are ready or it is marked
unavailable**; disabled/unpublished/quarantined/non-`ready` image evidence never
returned; retrieval deterministic for fixed KB/model/config/query; image decisions
logged. Bias tuning shows a measured effect with caps respected.

**Decisions needed before starting:** see D16, D17, D5 (bias state).

---

## Phase 10 — Kiosk image rendering & multimodal demo (Goal 1, Goal 2, Goal 10)

*Original Slice 7D. Final feature phase.*

**Objective.** Integrate image evidence into the resident-facing kiosk experience
and prove visual guidance works for navigation, landmarks, and first-aid use cases.

**Work items:**

1. **Hub→kiosk image evidence payload support** (Sprint 5 Slice 7D Story 2, 5 pts)
   — kiosk response model carries evidence ID, modality, score/rank, and render
   reference; preserve compatibility with text-only responses. *(Front-loaded in
   Sprint 5 so retrieval/rendering can integrate.)*
2. **Kiosk rendering** for image evidence returned by the hub (Sprint 7 Slice 7D
   Story 1, 8 pts) — **thumbnail/display-rendition-first** display; preserve aspect
   ratio; no unsafe cropping; no generative enhancement.
3. **Image-first response behavior** for visual questions (Sprint 7 Slice 7D Story
   3, 5 pts) — hub can mark image evidence as primary; minimal text framing;
   low-confidence matches never presented as authoritative.
4. **Kiosk image-loading optimization** (Sprint 6 Slice 7D Story 11, 5 pts) —
   prefer thumbnail / compressed display rendition over original; efficient
   offline/local-network loading using hub-generated renditions.
5. **Handle image loading failures + placeholders** (Sprint 6 Slice 7D Story 4,
   3 pts) — safe placeholder or hide image block on missing reference; broken
   images never crash/freeze the kiosk; keep text answer visible; report load
   errors where feasible.
6. **Explicit text-only fallback validation** (Sprint 6 Slice 7D Story 10, 3 pts)
   — verify the text answer still works when no image evidence is returned or image
   evidence is unavailable (validated behavior, not just incidental).
7. **Console/admin image asset status display** (Sprint 6 Slice 7D Story 6, 5 pts)
   — display pending/ready/failed/rejected states in the console; shares asset
   fields with the Phase 8 admin confirmation view.
8. **Multimodal demo scenarios** (Sprint 5 Slice 7D Story 7, 3 pts) **+ regression
   test set** — landmark/building, wayfinding, and first-aid visual scenarios;
   deterministic for a fixed KB snapshot.

> Scope note: kiosk display is faithful and lightweight — **no AI image
> enhancement, upscaling, or hallucinated detail**, especially for medical / map /
> sign visuals.

**Dependencies / rationale.** Depends on Phases 8 and 9 (stable image evidence
payloads + render refs, compressed renditions, ready-state assets). Last because it
consumes everything upstream. Items 1 and 8 are front-loaded in Sprint 5 but
land/validate here.

**Definition of done.** Kiosk displays returned image evidence offline/local using
thumbnail/compressed renditions; broken/missing references handled safely with text
preserved; **text-only fallback validated** when image evidence is unavailable;
image-first behavior works; console shows asset status; text-only answers still
render; "show me [building]" and "how do I bandage a wound?" return correct visual
evidence; demo/regression set deterministic.

---

## Phase 11 — Stabilization & release (formerly Sprint 8, dates removed)

**Objective.** End-to-end validation of the whole increment with no new feature
development.

**Work items:**

1. **End-to-end testing** across the canonical pipeline (text + image paths).
2. **Benchmarking** against the MVP KPIs from Phase 5 (grounding, evidence
   stability, latency p50/p95).
3. **Regression run** of the exact-term set (Phase 3) and multimodal set
   (Phase 10).
4. **Critical bug fixes** only.
5. **Final documentation pass** — update post-sprint write-ups / decision records.

**Dependencies / rationale.** Runs after all feature phases. (Caching, Phase 6,
should be validated here too if delivered.)

**Definition of done.** All KPI reports generated and reviewed; regression sets
pass deterministically; no known critical bugs; docs reflect final state.

---

## Open design decisions register (resolve before dependent work starts)

Each decision **gates** the phase(s) noted. Resolve and record the choice + rationale
before starting that phase.

| ID | Decision | Options / notes | Gates |
|----|----------|-----------------|-------|
| D1 | Clarification trigger thresholds | ✅ resolved during delivery | (was Phase 1 — done, Sprint 2) |
| D2 | Clarification option identity model | ✅ resolved — taxonomy-backed IDs | (was Phase 1 — done, Sprint 2) |
| D3 | Validation artifact storage | ✅ resolved during delivery | (was Phase 2 — done, Sprints 2–3) |
| D4 | Gate semantics + medical/safety rule set | ✅ resolved during delivery | (was Phase 2 — done, Sprints 2–3) |
| D5 | Feedback-bias state identifier | ◐ base layer resolved (Phase 3); per-path vs per-merge application still open for tuning | Phase 9 |
| D6 | Hybrid retrieval specifics | ✅ resolved — index type, fields, RRF fusion + `k` | (was Phase 3 — done, Sprint 3) |
| D7 | Multi-path decomposition rule | Top-2 only vs bounded top-3 when confidence high | Phase 4 |
| D8 | Multi-path merge strategy | Strict priority-first vs RRF vs hybrid (priority bucket + RRF within); final priority order; SOS/secondary-output UX contract | Phase 4 |
| D9 | Metrics logging location | Extend `query_logs` vs related table keyed by `query_logs.id`; hallucination-proxy representation; query-text retention/privacy policy | Phase 5 |
| D10 | Config-version signal for cache | Existing version table vs hash of relevant config | Phase 6 |
| D11 | Cache safety scope | Which intents are safety-critical for re-validation; single-flight/coalescing this increment? | Phase 6 |
| D12 | KB table strategy | Extend `kb_articles` in place vs new generalized KB item table + compatibility view | Phase 7 |
| D13 | Metadata storage form | Dedicated columns vs JSON blob (queryability/determinism vs flexibility); evidence-log shape for multimodal/top-k | Phase 7 |
| D14 | Image binary storage | Filesystem vs object storage; how refs are represented (path vs content-addressed ID vs DB row) — must align across Phases 7–8 | Phases 7, 8 |
| D15 | Thumbnail + asset-state policy | ✅ **resolved** — 4-state model `pending / ready / failed / rejected` adopted (only `ready` is resident-facing); thumbnail + one compressed display rendition with deterministic params. *(Remaining open sub-question: global vs per-KB-version dedup of identical content hashes — fold into D14.)* | Phase 8 (resolved) |
| D16 | Image model choice | **CLIP vs SigLIP** given offline deployment constraints + licensing; model versioning + preprocessing | Phase 9 |
| D17 | Image confidence policy | Similarity floor value; top-1 vs top-N for image-first queries and a kiosk-safe N; PII policy for stored images | Phases 9, 10 |

---

## Dependency summary (linear critical path)

```
Phase 0 (DONE), Phase 1 (DONE), Phase 3 (DONE — incl. RK-37)
Phase 2 (◐ core+review-audit done; RK-32 publish-attempt persistence open) ┐
                                                                           ├─→ Phase 4 (multi-path)
   [RK-32 remainder, RK-55] ───────────────────────────────────────────── ┴──→ Phase 5 (RK-55 + KPI/reporting)
                                                                                  ├─→ Phase 6 (caching, optional/parallel)
                                                                                  └─→ Phase 7 → Phase 8 → Phase 9 → Phase 10
                                                                                                                       ↓
                                                                                                                  Phase 11 (stabilize)
```

- **Backbone → scope/safety → accuracy → observability → performance → multimodal**,
  exactly as the increment intended.
- Delivered so far: **Phase 0** (backbone + scope), **Phase 1** (clarify-first),
  **Phase 3** (hybrid retrieval + bias layer + RK-37 contribution logging), the
  core + review-audit of **Phase 2** (trusted publish), and the **Phase 5 logging
  schema**.
- **Carried-forward logging after the merge (Goal 10, 3 pts each):** RK-37 ✅ done;
  **RK-32 remainder** (Phase 2 publish-attempt/rule-result persistence) and **RK-55**
  (Phase 5 failure/fallback) still open — **on the critical path to Phase 5**, close
  both before Phase 5 items 3–4.
- **Remaining:** RK-32 remainder + RK-55 (close anytime; needed by Phase 5) · Phase 4
  (multi-path) · Phase 5 (RK-55 + KPI/reporting) · {Phase 6 caching ∥ Phases 7–10
  multimodal} · Phase 11.
- Phase 6 (caching) is the only optional/parallelizable branch; everything else is
  a strict chain because each phase produces the contract the next consumes.
