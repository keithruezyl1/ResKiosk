---
title: Execution — Phase 7 — Multimodal schema
parent: Execution Plan
---

# Phase 7 — Multimodal schema (Goal 3, +10, 7)

## Objective and scope

Introduce the minimum schema + evidence-contract changes to represent both text and image evidence
without breaking existing text-only KB behavior. Start of the multimodal track. No semantic chunking
(forward-compatible fields only). 16 pts cluster (Slice 7A; backfill + identity + contract).

## Gating decisions

- **D12 — table strategy:** extend `kb_articles` in place vs a new generalized KB item table +
  compatibility view. *(Given the current single-table model and additive-migration pattern,
  extending `kb_articles` in place is the likely smallest-viable choice — confirm via dev-research.)*
- **D13 — metadata storage form:** dedicated columns vs JSON blob; evidence-log shape for
  multimodal/top-k.

## Dependencies

Phase 0 (schema/migration pattern), Phase 1 (filters/taxonomy), Phase 2 (trusted publish), Phase 5
(observability — so image evidence is measurable). Must precede Phases 8–10.

## Ordered execution steps

1. Decide D12/D13; add modality + asset-ref + segmentation fields via idempotent migration.
2. Backfill existing rows as `text` modality.
3. Define stable multimodal evidence identity tied to `kb_version`.
4. Update the evidence response contract to carry modality.
5. Add modality-aware evidence logging.

---

## Work items

### S7A.1 — Add multimodal KB item schema (8 pts)
- **Implement.** Add `modality` (`text|image`, default `text`) and image-asset reference field(s)
  to the KB item model (extend `kb_articles` per D12); additive, backward-compatible.
- **Files.** `hub/db/schema.py` (`KBArticle`: `modality`, `image_asset_id`/ref), `hub/db/
  migrate_schema.py` (idempotent ALTER), `hub/db/init_db.py`.
- **Gates.** **D12, D13.**
- **Acceptance.** New columns exist on fresh + migrated DBs; existing text rows unaffected; default
  modality `text`.
- **Tests.** New `hub/tests/test_multimodal_schema.py` — migration idempotent; existing reads work;
  defaults correct.

### S7A.2 — Add stable multimodal evidence identity (5 pts)
- **Implement.** Preserve stable IDs for text evidence (current integer `kb_articles.id` /
  `source_id`); define stable evidence identity for image evidence tied to `kb_version`; keep
  backward compatibility with `source_id` behavior.
- **Files.** `hub/retrieval/search.py`, `hub/models/api_models.py` (evidence identity),
  `hub/retrieval/formatter_contract.py`.
- **Acceptance.** Evidence IDs are stable + reproducible across runs for a fixed KB version, for both
  modalities; legacy `source_id` still works.
- **Tests.** Extend `test_multimodal_schema.py` — identity stability for text + image; legacy compat.

### S7A.3 — Prepare image asset reference fields (5 pts) *(bridges to Phase 8)*
- **Implement.** Add the reference fields/link structure for image assets (original + thumbnail +
  rendition refs once Phase 8 exists); handle missing/broken refs safely.
- **Files.** `hub/db/schema.py` (asset-ref fields or FK to an assets table created in Phase 8),
  `hub/db/migrate_schema.py`.
- **Gates.** D14 (reference representation — align with Phase 8).
- **Acceptance.** Image evidence can reference asset records once Phase 8 lands; null/missing refs do
  not break text retrieval.
- **Tests.** Extend `test_multimodal_schema.py` — ref fields nullable + safe.

### S7A.4 — Add forward-compatible segmentation fields (3 pts)
- **Implement.** Add `parent_article_id` + `segment_index` (stored, **not** used to change the
  retrieval unit — no chunking).
- **Files.** `hub/db/schema.py`, `hub/db/migrate_schema.py`.
- **Acceptance.** Fields present + nullable; retrieval unit remains one `kb_articles` row.
- **Tests.** Extend `test_multimodal_schema.py` — fields exist; retrieval unchanged.

### S7A.5 — Update evidence response contract for modality (5 pts)
- **Implement.** Add `evidence_id` + `modality` to evidence responses; allow image evidence to carry
  asset/render references when available; preserve text-only response shape.
- **Files.** `hub/models/api_models.py`, `hub/retrieval/formatter.py`/`formatter_contract.py`,
  `hub/api/routes_query.py`, `docs/openapi.yaml`.
- **Gates.** D13.
- **Acceptance.** Responses include modality; text-only consumers unaffected; openapi updated.
- **Tests.** Integration via `TestClient` — evidence carries modality; legacy shape intact.

### S7A.6 — Backfill existing KB articles as text modality (5 pts)
- **Implement.** Backfill `modality="text"` for existing rows; preserve enabled/status, embeddings,
  current query behavior.
- **Files.** `hub/db/migrate_schema.py` (backfill step) or `hub/db/seed.py`.
- **Acceptance.** All pre-existing rows are `text`; no behavior change to text retrieval.
- **Tests.** Extend `test_multimodal_schema.py` — backfill correctness + idempotency.

### S7A.7 — Add modality-aware evidence logging (3 pts)
- **Implement.** Log evidence modality alongside evidence IDs; bounded to top-k; legacy-compatible.
- **Files.** `hub/api/routes_query.py`, `hub/db/schema.py` (reuse existing top-k fields; add
  `modality` markers if needed).
- **Acceptance.** Logs record modality per evidence item; KPI reporting can group by modality.
- **Tests.** Extend `test_query_log_schema.py` — modality logged; grouping works.

---

## Phase 7 Definition of Done

Existing text-only content remains retrievable; evidence objects can carry modality; image evidence
can reference asset records once Phase 8 exists; evidence IDs stable + loggable; migration additive /
backward-compatible; D12/D13 recorded (D14 alignment noted for Phase 8); all Phase 7 tests pass.
