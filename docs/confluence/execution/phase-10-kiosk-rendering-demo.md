---
title: Execution — Phase 10 — Kiosk image rendering & multimodal demo
parent: Execution Plan
---

# Phase 10 — Kiosk image rendering & multimodal demo (Goal 1, 2, 10) — ◐ HUB-SIDE DONE; front-end + eval remaining

> **STATUS: hub-side complete; the rest is front-end / real-data work this Python
> environment can't build or verify.**
>
> **Done (hub):** S7D.2 image-evidence payload (Phase 9 `image_evidence` + `render_ref`);
> S7D.10 text-only fallback (tested — no/failed image leaves the text answer intact);
> **S7D.3 hub side — `QueryResponse.image_primary`** + `RESKIOSK_IMAGE_PRIMARY_FLOOR`
> (0.30): image-first when confident, tentative (non-authoritative, D17) below it.
> S7D.6 backend (`GET /admin/kb/assets[/{id}]`) already shipped in Phase 8.
>
> **Remaining (NOT doable here — needs the Android/React toolchains or real model+images):**
> - **Kiosk (Kotlin/Compose, `kiosk/`):** S7D.1 render image evidence, S7D.3 kiosk image-first
>   UI, S7D.4 broken-image placeholders, S7D.11 thumbnail/rendition-first loading, kiosk-side
>   deserialization/VM tests. No gradle/kotlinc available here — writing it blind would be untested.
> - **Console (React, `console/`):** S7D.6 asset-status UI (backend endpoint ready; no console test runner).
> - **S7D.7 multimodal demo/regression set:** real value needs the bundled CLIP model + labeled
>   images (same blocker as RK-92); a stub version would duplicate existing tests.
>
> Hub is ready for the kiosk to consume `image_evidence` / `image_primary` / `render_ref` via
> `GET /assets/{id}/{variant}`.

## Objective and scope

Integrate image evidence into the resident-facing kiosk experience and prove visual guidance works
for navigation, landmarks, and first-aid use cases. Faithful, lightweight display — **no AI image
enhancement/upscaling/hallucinated detail**, especially for medical/map/sign visuals. Final feature
phase. Mostly Kotlin/Jetpack Compose (`kiosk/`) plus a hub payload item and console status.

## Gating decisions

- **D17 — confidence display policy** (carried from Phase 9): how low-confidence image matches are
  presented (never authoritative).

## Dependencies

Phase 8 (renditions, ready-state assets, admin status) + Phase 9 (image evidence payloads, render
refs, retrieval behavior). Hub→kiosk payload (item 1) is front-loaded in Sprint 5 but
lands/validates here.

## Ordered execution steps

1. Hub→kiosk image evidence payload support (front-loaded).
2. Kiosk rendering of image evidence (thumbnail/rendition-first).
3. Image-first response behavior.
4. Kiosk image-loading optimization.
5. Image loading failure handling + placeholders.
6. Explicit text-only fallback validation.
7. Console/admin image asset status display.
8. Multimodal demo + regression set.

---

## Work items

### S7D.2 — Add hub→kiosk image evidence payload support (5 pts) *(front-loaded)*
- **Implement.** Kiosk response model carries evidence ID, modality, score/rank, and render
  reference; preserve compatibility with text-only responses.
- **Files.** `hub/models/api_models.py`, `hub/api/routes_query.py`, `docs/openapi.yaml`;
  kiosk consumer: `kiosk/app/src/main/java/com/reskiosk/network/HubApiClient.kt` +
  response data classes.
- **Acceptance.** Hub returns image evidence fields; kiosk model deserializes them; text-only
  responses still parse.
- **Tests.** Hub: integration via `TestClient` — payload shape. Kiosk: Kotlin unit test for
  deserialization under `kiosk/app/src/test/...`.

### S7D.1 — Render image evidence in kiosk responses (8 pts)
- **Implement.** Render returned image evidence; **thumbnail/display-rendition-first**; preserve
  aspect ratio; no unsafe cropping; no generative enhancement.
- **Files.** `kiosk/app/src/main/java/com/reskiosk/ui/MainKioskScreen.kt` (+ a new image evidence
  composable), `kiosk/app/src/main/java/com/reskiosk/viewmodel/KioskViewModel.kt`.
- **Acceptance.** Image evidence displays offline/local using thumbnail/rendition; aspect ratio
  preserved.
- **Tests.** Kotlin UI/VM unit tests for rendering state; manual kiosk checklist for visual.

### S7D.3 — Support image-first response behavior (5 pts)
- **Implement.** Hub can mark image evidence as primary; kiosk shows image-first with minimal text
  framing; low-confidence matches never presented as authoritative (D17).
- **Files.** `hub/retrieval/formatter.py` / `hub/models/api_models.py` (primary flag),
  `kiosk/.../ui/MainKioskScreen.kt`, `kiosk/.../viewmodel/KioskViewModel.kt`.
- **Gates.** **D17.**
- **Acceptance.** Visual question → image-first display; low-confidence shown as tentative, not
  authoritative.
- **Tests.** Kotlin VM unit test — image-first vs text-first selection; low-confidence framing.

### S7D.11 — Optimize kiosk image loading and display (5 pts)
- **Implement.** Prefer thumbnail / compressed display rendition over original; efficient
  offline/local-network loading using hub-generated renditions.
- **Files.** `kiosk/.../ui/MainKioskScreen.kt`, image loading util (kiosk), `HubApiClient.kt`.
- **Acceptance.** Kiosk loads thumbnail/rendition first; original only if allowed; smooth on
  local network.
- **Tests.** Kotlin unit test for reference-preference logic; manual load-time check in demo.

### S7D.4 — Handle image loading failures and placeholders (3 pts)
- **Implement.** Safe placeholder or hide image block on missing reference; broken images never
  crash/freeze the kiosk; keep text answer visible; report load errors where feasible.
- **Files.** `kiosk/.../ui/MainKioskScreen.kt`, `kiosk/app/src/main/res/drawable/placeholder.xml`
  (exists), `KioskViewModel.kt`.
- **Acceptance.** Missing/broken refs → placeholder or suppression; text remains; no crash.
- **Tests.** Kotlin unit test — broken ref path → fallback state, text preserved.

### S7D.10 — Validate text-only fallback when image evidence unavailable (3 pts)
- **Implement.** Verify (as validated behavior, not incidental) the text answer still works when no
  image evidence is returned or image evidence is unavailable.
- **Files.** `kiosk/app/src/test/java/com/reskiosk/...` (test), `KioskViewModel.kt` (ensure path).
- **Acceptance.** No-image / unavailable-image responses render a correct text-only answer.
- **Tests.** Kotlin unit test — no-image response → text-only answer renders; hub integration test for
  no-image response shape.

### S7D.6 — Display image asset status in admin console (5 pts)
- **Implement.** Console shows pending/ready/failed/rejected states; shares asset fields with the
  Phase 8 admin confirmation view.
- **Files.** `console/src/pages/` (extend `AssetManager.jsx`/`KBViewer.jsx`),
  `console/src/api/hubClient.js`, endpoint in `hub/api/routes_kb.py`.
- **Acceptance.** Admin sees current asset states in the console.
- **Tests.** Backend endpoint test; frontend smoke/manual checklist.

### S7D.7 — Create multimodal demo scenarios (3 pts) + regression set
- **Implement.** Landmark/building, wayfinding/navigation, and first-aid visual scenarios on a fixed
  KB snapshot + known assets; deterministic; feeds Phase 11 regression.
- **Files.** `hub/eval/data/multimodal_eval.json`, `hub/eval/multimodal_eval.py`,
  `hub/tests/test_multimodal_eval.py`.
- **Acceptance.** Scenarios run deterministically against the fixed snapshot; expected image evidence
  returned/displayed.
- **Tests.** `test_multimodal_eval.py` — scenarios + reproducibility.

---

## Phase 10 Definition of Done

Kiosk displays returned image evidence offline/local using thumbnail/compressed renditions;
broken/missing references handled safely with text preserved; **text-only fallback validated** when
image evidence unavailable; image-first behavior works; low-confidence never authoritative; console
shows asset status; text-only answers still render; "show me [building]" and "how do I bandage a
wound?" return correct visual evidence; demo/regression set deterministic; D17 recorded; hub + kiosk
tests pass.
