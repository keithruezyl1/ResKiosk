---
title: Execution — Phase 8 — Image asset lifecycle
parent: Execution Plan
---

# Phase 8 — Image asset lifecycle (Goal 2, +11, 10)

## Objective and scope

Store KB images as durable first-class assets with stable identity, thumbnails, a compressed display
rendition, content hashes, a 4-state processing model, KB-version linkage, publish-time
invalidation, and admin confirmation/status. Asset readiness + debugging support — **not** a polished
DAM. ~50 pts across Slice 7B + admin items.

## Gating decisions

- **D14 — image binary storage:** filesystem vs object storage; reference representation (path vs
  content-addressed ID vs DB row). Must align with Phase 7 asset-ref fields.
- **D15 — RESOLVED:** 4-state model `pending|ready|failed|rejected`; thumbnail + one compressed
  display rendition with deterministic params; only `ready` is resident-facing. *(Remaining sub-Q —
  global vs per-KB-version dedup of identical hashes — fold into D14.)*

## Dependencies

Phase 7 (multimodal schema + asset-ref fields). Assets must exist and be `ready` before Phase 9
embeddings. Upload API + admin confirmation are prerequisites for Phase 9's readiness gate.

## Ordered execution steps

1. Decide D14; create asset records + storage (original ref, hash, MIME, size, timestamps).
2. Add the upload API.
3. Generate content hashes.
4. Generate deterministic thumbnails.
5. Generate compressed display rendition(s).
6. Add the 4-state processing model + reason codes (D15).
7. Link assets/artifacts to KB version.
8. Publish-time invalidation/refresh.
9. Broken/missing asset guard.
10. Admin asset confirmation view.
11. Asset lifecycle logging.

---

## Work items

### S7B.1 — Store image assets as first-class KB assets (8 pts)
- **Implement.** Durable `image_assets` table: stable asset id, original ref, MIME, size,
  timestamps, minimal audit fields. Storage per D14.
- **Files.** `hub/db/schema.py` (`ImageAsset`), `hub/db/migrate_schema.py`, new
  `hub/services/image_assets.py`.
- **Gates.** **D14.**
- **Acceptance.** Asset records persist with stable IDs + metadata; referenced from KB items (Phase 7).
- **Tests.** New `hub/tests/test_image_assets.py` — create/read asset record; stable IDs.

### S7B.2 — Add image upload API for KB assets (5 pts)
- **Implement.** Endpoint to accept supported image uploads; validate file size + MIME; store original
  ref; log failures. Security-conscious file validation.
- **Files.** `hub/api/routes_kb.py` (or new `routes_assets.py`), `hub/services/image_assets.py`,
  `docs/openapi.yaml`.
- **Acceptance.** Valid images stored + asset record created; invalid type/size rejected with clear
  error; failures logged.
- **Tests.** Extend `test_image_assets.py` + integration via `TestClient` — accept valid, reject
  invalid, failure logged.

### S7B.3 — Generate content hashes for image assets (3 pts)
- **Implement.** Deterministic content hash for identity, dedupe, integrity; store on the asset.
- **Files.** `hub/services/image_assets.py`, `hub/db/schema.py`.
- **Gates.** D14 (dedup scope sub-question).
- **Acceptance.** Same bytes → same hash; stored + queryable; dedup behavior per decision.
- **Tests.** Extend `test_image_assets.py` — hash determinism; dedup behavior.

### S7B.4 — Generate deterministic thumbnails (8 pts)
- **Implement.** Thumbnail with fixed parameters (same input → same output); store reference.
- **Files.** `hub/services/image_assets.py` (e.g. Pillow), `hub/db/schema.py`.
- **Acceptance.** Deterministic thumbnail bytes for fixed params; reference stored.
- **Tests.** Extend `test_image_assets.py` — deterministic thumbnail (hash of output stable).

### S7B.10 — Compress images + generate optimized renditions (5 pts)
- **Implement.** At least one display-size compressed rendition; deterministic settings; preserve
  original; preserve aspect ratio; no unsafe cropping; store rendition ref + output size/dims/format/
  derivative hash. Define which reference the kiosk prefers (thumbnail vs rendition vs original).
  **No AI enhancement/upscaling.**
- **Files.** `hub/services/image_assets.py`, `hub/db/schema.py`.
- **Acceptance.** Deterministic rendition; original preserved; metadata stored; kiosk-preferred ref
  defined.
- **Tests.** Extend `test_image_assets.py` — rendition determinism + aspect ratio preserved.

### S7B.5 — Add image asset processing states (5 pts) *(D15 resolved)*
- **Implement.** States `pending|ready|failed|rejected` with reason codes; only `ready` is
  resident-facing; publish never references partially processed assets.
- **Files.** `hub/db/schema.py` (`status`/state field on `ImageAsset`), `hub/services/
  image_assets.py`.
- **Acceptance.** State transitions enforced; non-`ready` excluded from resident retrieval; failure
  reason codes recorded.
- **Tests.** New `hub/tests/test_image_asset_states.py` — transitions + retrieval eligibility.

### S7B.6 — Link image assets to KB version (5 pts)
- **Implement.** Link asset records + derived artifacts to the KB version used at publish; query logs
  can identify which KB version produced image evidence.
- **Files.** `hub/db/schema.py`, `hub/services/image_assets.py`, publish path in
  `hub/api/routes_kb.py`.
- **Acceptance.** Assets/artifacts carry KB-version linkage; logs can join by KB version.
- **Tests.** Extend `test_image_asset_states.py` — version linkage present + correct.

### S7B.7 — Invalidate image artifacts on KB publish (5 pts)
- **Implement.** On publish, invalidate/refresh artifacts tied to prior KB versions; include KB
  version + content hash in artifact keys; fail closed / bypass affected artifacts if invalidation
  fails (Goal 11 integration).
- **Files.** `hub/api/routes_kb.py`/`routes_admin.py` (publish hook), `hub/services/image_assets.py`.
- **Acceptance.** New KB version uses current artifacts; stale image artifacts not served; failure is
  fail-closed + logged.
- **Tests.** Extend `test_image_asset_states.py` — publish invalidates/refreshes; fail-closed path.

### S7B.8 — Add admin asset confirmation view (5 pts)
- **Implement.** Console view: upload status, original/thumbnail preview, content hash/identity,
  processing errors; admin can confirm asset is ready for KB use; distinguish publish-eligible vs
  not-ready; show KB item/taxonomy linkage where available.
- **Files.** `console/src/pages/` (new `AssetManager.jsx` or extend `KBViewer.jsx`),
  `console/src/api/hubClient.js`, supporting endpoint in `hub/api/routes_kb.py`.
- **Acceptance.** Admin sees per-asset status + previews + errors and can confirm readiness.
- **Tests.** Backend: endpoint returns asset status (extend `test_image_assets.py`). Frontend: light
  component/smoke test if console test setup exists; otherwise manual checklist.

### S7B.9 — Log image asset lifecycle events (3 pts)
- **Implement.** Log upload, thumbnail/rendition generation, processing transitions, readiness
  failures, invalidation events; joinable by asset id + KB version.
- **Files.** `hub/services/image_assets.py`, `hub/core/logger_stream.py`, optional audit table.
- **Acceptance.** Full asset lifecycle reconstructable from logs.
- **Tests.** Extend `test_image_asset_states.py` — events emitted for each transition.

---

## Phase 8 Definition of Done

Assets stored with original + thumbnail + compressed rendition + content hash + KB-version linkage;
thumbnails/renditions deterministic; 4-state model enforced (only `ready` resident-facing); upload
API validates + stores; admin can confirm status; broken assets excluded; KB publish
invalidates/refreshes safely; lifecycle events logged; D14 recorded (D15 already resolved); all
Phase 8 tests pass.
