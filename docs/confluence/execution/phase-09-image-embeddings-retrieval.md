---
title: Execution — Phase 9 — Image embeddings & semantic retrieval (+ bias tuning)
parent: Execution Plan
---

# Phase 9 — Image embeddings & semantic retrieval (Goal 1, +10, 7, 8) + deferred Goal 9 bias tuning (5 pts) — ✅ Slice 7C COMPLETE (S9.tune deferred)

> **STATUS: Slice 7C COMPLETE** (D16/D17 resolved). `hub/retrieval/image_embedder.py`
> — CLIP ViT-B/32 via sentence-transformers (Apache-2.0, CPU, bundled to
> `hub_models/clip` via `bundle_models.py`); same offline load pattern as the text
> embedder. Image embeddings persisted on `image_assets` (embedding / embedding_model
> / embedding_kb_version), generated at publish, **readiness-gated** + model-version
> invalidated, encoder loaded only when there's work. `search.retrieve_images()` =
> text→image path: CLIP-text query vs image vectors, `RESKIOSK_IMAGE_SIM_THRESHOLD`
> (~0.26, calibrate) + `RESKIOSK_IMAGE_TOP_N` (3) + deterministic `(score desc,
> source_id asc)` tie-break; gates exclude disabled/quarantined/rejected/non-ready/
> stale-model/missing-embedding. `GET /assets/search?q=` (kiosk) + additive
> `image_evidence` on `/query` (fail-safe, skipped on retry, [] fast with no image
> KB) recorded in `final_evidence`; image-search logs carry model+floor+top_n.
> 212-test suite green (CLIP stubbed throughout); app boots.
>
> **Deferred:** **S9.tune** (feedback-bias tuning) — gated on **D5** (bias state /
> per-path vs per-merge), still open; revisit with metrics. S7C.6 "merge" is
> implemented as an additive `image_evidence` list alongside text (not interleaved
> into one ranked list) — sufficient for Goal 1; revisit if a unified ranking is wanted.

## Objective and scope

Enable text→image semantic retrieval using a locally hosted vision-language model, fully subject to
filtering and validation gating, with embeddings generated during ingest/publish behind a readiness
gate. Also complete the deferred feedback-ranking **tuning** now that hybrid + multi-path + metrics
exist to measure it. ~58 pts (Slice 7C) + 5 pts tuning.

## Gating decisions

- **D16 — image model:** CLIP vs SigLIP given offline deployment + licensing; model version +
  preprocessing.
- **D17 — image confidence policy:** similarity floor value; top-1 vs top-N for image-first; PII
  policy for stored images.
- **D5 — bias state identifier:** timestamp cutoff vs snapshot version; per-path vs per-merge bias
  application (for the tuning item).

## Dependencies

Phase 7 (multimodal schema/identity), Phase 8 (assets + 4-state `ready` model + renditions),
Phase 1 (filtering), Phase 2 (validation). Model selection is front-loaded (Sprint 5 Slice 7C
Story 1). Bias tuning depends on Phase 3 (bias layer) + Phase 5 (metrics).

## Ordered execution steps

1. Confirm D16 (model) via dev-research; configure local/offline loading + preprocessing.
2. Build the embedding generation service.
3. Persist embeddings with model + KB-version metadata.
4. Gate embedding generation to ingest/publish with readiness gating.
5. Implement text→image retrieval path + thresholds/tie-breaks (D17).
6. Merge image evidence with text evidence response structure.
7. Apply filtering + validation gates to image retrieval.
8. Image retrieval logging.
9. (Deferred) tune the feedback-adjusted bias layer (D5).

---

## Work items

### S7C.1 — Select and configure image embedding model (5 pts) *(front-loaded)*
- **Implement.** Choose CLIP/SigLIP per D16; document version, local/offline load path,
  preprocessing, license/deployment constraints; smoke-test encoding one image.
- **Files.** new `hub/retrieval/image_embedder.py`, `requirements.txt`,
  `packaging/bundle_models.py` (bundle weights for offline), `docs/` model note.
- **Gates.** **D16.**
- **Acceptance.** Model loads offline; encodes a sample image to a fixed-dim vector; license allows
  offline redistribution.
- **Tests.** New `hub/tests/test_image_embedder.py` — load + encode smoke test; dimension fixed.

### S7C.2 — Implement image embedding generation service (8 pts)
- **Implement.** Service that loads the model, accepts a `ready` image asset, applies preprocessing,
  returns a vector of known dimension; safe model-load failure; logs model name/version + errors.
- **Files.** `hub/retrieval/image_embedder.py`, `hub/services/image_assets.py` (consume `ready`).
- **Acceptance.** Encodes ready assets deterministically; failures handled + logged.
- **Tests.** Extend `test_image_embedder.py` — deterministic embedding (fixed input → stable vector);
  failure path.

### S7C.3 — Persist image embeddings with model + KB-version metadata (8 pts)
- **Implement.** Store embeddings with stable image evidence/asset id, KB version, model name/version;
  invalidate/regenerate on model or KB-version change; log persistence failures.
- **Files.** `hub/db/schema.py` (`ImageEmbedding` or embedding column on asset),
  `hub/db/migrate_schema.py`, `hub/retrieval/image_embedder.py`.
- **Gates.** D5 (state identifier conventions help here).
- **Acceptance.** Embeddings persisted + linked to KB version + model version; stale embeddings
  invalidated on change.
- **Tests.** New `hub/tests/test_image_embedding_persistence.py` — persist/read; invalidation on
  version/model change.

### S7C.4 — Generate image embeddings during ingest/publish with readiness gating (5 pts)
- **Implement.** Trigger embedding generation during the selected ingest/publish step; process only
  eligible `ready` assets; **publish must not expose image evidence until its embeddings are ready or
  the evidence is safely marked unavailable**; stable failure reason codes.
- **Files.** `hub/api/routes_kb.py`/`routes_admin.py` (publish hook), `hub/services/image_assets.py`,
  `hub/retrieval/image_embedder.py`.
- **Acceptance.** On publish, ready assets get embeddings; not-ready/un-embedded image evidence is not
  exposed; failures use reason codes.
- **Tests.** New `hub/tests/test_embedding_publish_gate.py` — readiness gate blocks exposure;
  ready path embeds.

### S7C.5 — Implement text→image semantic retrieval path (8 pts) + S7C.8 thresholds/tie-breaks (3 pts)
- **Implement.** Encode the English retrieval-boundary query; search persisted image embeddings;
  return top-k image evidence IDs + score + rank + render reference; similarity floor + deterministic
  tie-break `(score desc, evidence_id asc)`; low-confidence labeled "possible matches"; safe
  no-result handling.
- **Files.** `hub/retrieval/search.py` (image retrieval entry), `hub/retrieval/image_embedder.py`,
  `hub/retrieval/fusion.py` (tie-break reuse).
- **Gates.** **D17.**
- **Acceptance.** English text query retrieves relevant image evidence; below-floor results withheld/
  labeled; deterministic for fixed KB/model/config/query.
- **Tests.** New `hub/tests/test_text_to_image_retrieval.py` — relevant retrieval; floor behavior;
  run-twice determinism.

### S7C.6 — Merge image evidence with text evidence response structure (5 pts)
- **Implement.** Include image evidence alongside text; deterministic mixed-evidence ordering;
  preserve text-only behavior; evidence carries evidence_id, modality, score, rank, render ref.
- **Files.** `hub/retrieval/formatter.py`/`formatter_contract.py`, `hub/models/api_models.py`,
  `hub/api/routes_query.py`, `docs/openapi.yaml`.
- **Acceptance.** Mixed text+image responses deterministic; text-only unchanged.
- **Tests.** Integration via `TestClient` — mixed evidence ordering stable; text-only intact.

### S7C.7 — Apply filtering and validation gates to image retrieval (5 pts)
- **Implement.** Exclude disabled / unpublished / quarantined / rejected / non-`ready` image
  evidence; apply UI + inferred filters where metadata exists; log filtering decisions + candidate
  counts.
- **Files.** `hub/retrieval/filter_policy.py` (extend for image), `hub/retrieval/search.py`,
  `hub/validation/metadata.py` (gate reuse).
- **Gates.** depends on Phase 2 + Phase 8 states.
- **Acceptance.** No disabled/unpublished/quarantined/rejected/non-ready image evidence returned;
  filters applied; decisions logged.
- **Tests.** New `hub/tests/test_image_retrieval_gates.py` — each exclusion category; filter
  precedence on image path.

### S7C.9 — Log image retrieval evidence and model metadata (3 pts)
- **Implement.** Log normalized English query, model/version, image evidence IDs, scores, thresholds,
  display/suppression, latency.
- **Files.** `hub/api/routes_query.py`, `hub/db/schema.py` (reuse top-k fields + add model/version +
  threshold markers if needed via migration).
- **Acceptance.** Image retrieval decisions reconstructable from logs incl. model/version + threshold.
- **Tests.** Extend `test_query_log_schema.py` — image-retrieval fields populated + bounded.

### S9.tune — Tune feedback-adjusted bias layer (Goal 9, 5 pts)
- **Implement.** Calibrate alpha/scale + caps using Phase 5 metrics; confirm bias state identifier
  for reproducibility (D5); verify bias never bypasses hard rules, filters, or clarification; decide
  per-path vs per-merge application.
- **Files.** `hub/retrieval/rlhf_bias.py`, `hub/retrieval/search.py`/`multipath_merge.py`,
  config env (bias params).
- **Gates.** **D5.**
- **Acceptance.** Tuned bias shows a measured KPI effect with caps respected; deterministic given
  fixed bias state; never overrides hard rules/filters/clarification.
- **Tests.** Extend `hub/tests/` bias tests — caps enforced; determinism for fixed bias state;
  before/after metric delta on the eval set.

---

## Phase 9 Definition of Done

English text queries retrieve relevant image evidence with stable IDs/scores/ranks/render refs;
embeddings generated during ingest/publish with **no image evidence exposed until embeddings ready or
marked unavailable**; disabled/unpublished/quarantined/non-`ready` image evidence never returned;
retrieval deterministic for fixed KB/model/config/query; image decisions logged with model/version +
threshold; bias tuning shows a measured effect with caps respected; D16/D17/D5 recorded; all tests
pass.
