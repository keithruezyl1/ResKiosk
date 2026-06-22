# ResKiosk AAIH — Session Catch-Up

**Branch:** `aaih-keith` (all work committed & pushed to `origin/aaih-keith`)
**Hub test suite at end of session:** **214 passing** (Python `unittest`), `hub.main` imports/boots clean.
**Scope of this session:** closed out the carried-forward Sprint 1–3 logging, then implemented the AAIH increment **Phases 4–9 in full** (hub/backend, TDD) plus the **hub side of Phase 10**, resolved every gating decision needed along the way, and produced **unverified front-end drafts** for the kiosk/console image work.

This doc is the human-readable summary. The **living source of truth** is:
- `docs/confluence/execution-plan.md` — phase index + decision-resolution status
- `docs/confluence/development-plan.md` — the decision register (D1–D17)
- `docs/confluence/execution/phase-0X-*.md` — per-phase status + work items

---

## TL;DR

- The **Python/hub backend is feature-complete** across the increment (Phases 0–9 + Phase 10 hub bits).
- What remains is **front-end (kiosk Kotlin / console React)**, **real-model/real-data work** (image-floor calibration), one **deferred decision (D5)** + its tuning item, and **Phase 11 stabilization** — none of which is fully doable in a Python-only environment.
- A **critical latent bug was found and fixed**: the merged Sprint 1–3 code could not boot (missing imports in `routes_admin`).

---

## 1. What we did

### 1.1 Tooling & documentation
- Connected the **Atlassian MCP** (OAuth) and confirmed the `reskiosk` workspace (Jira project `RK`, Confluence space `SCRUM`).
- **Mirrored the entire Confluence space (24 pages)** into `docs/confluence/` with traceable frontmatter; added the `sprint4–8_task_grouping.md` planning docs; merged `Sprint-3` (already contained); pushed.

### 1.2 Critical bugfix (app couldn't boot)
- `hub/api/routes_admin.py` referenced `get_current_user`, `get_optional_user`, the validation-gate functions, the `review` module, and `invalidate_lexical_index` **without importing any of them**. Since `hub/main.py` imports `routes_admin`, **the whole hub failed at startup**, and the Slice 3 publish-gate + metadata-review endpoints had never run. `test_publish_gate` had been erroring on import (12 errors).
- **Fix:** restored the dropped imports → app boots, suite green. (commit `3037694`)

### 1.3 Carried-forward logging (Sprint 1–3 remainder)
- **RK-55** — failure/fallback logging: new `hub/retrieval/outcomes.py` (stable reason codes); `query_logs.fallback_reason` / `failed_stage` populated across the pipeline; **partial row written even on hard failure** so no outcome is silently dropped.
- **RK-32** — publish audit persistence: `/admin/publish` now persists a `KBPublishAttempt` + per-rule `KBValidationResult` rows (incl. before the strict-block 422).

### 1.4 Decisions resolved (via the `dev-research` skill, one question at a time)
| Decision | Phase | Resolution (short) |
|---|---|---|
| **D7** | 4 | Top-2 decomposition; `RESKIOSK_COMPOUND_INTENT_MIN=0.35` |
| **D8** | 4 | Priority-bucket-then-RRF; order = `INTENT_PRIORITY` (safety/emergency > medical > children/special_needs > general); additive `secondary_evidence` + `sos_offered` |
| **D9** | 5 | Extend `query_logs` + compute KPIs on read; rule-based offline grounding proxy; structured-only exports + 30-day transcript retention |
| **D10** | 6 | Computed `config_signature` (hash of retrieval config) + `kb_version` in cache key |
| **D11** | 6 | Bypass cache for safety-critical intents; single-flight + re-validation deferred |
| **D12** | 7 | Replace `kb_articles` → canonical `kb_items` (KBItem model + `KBArticle` alias); wipe/re-seed dev data; image = a `kb_items` row (one ID space) |
| **D13** | 7 | Typed columns for filtered fields + one JSON column for extras; evidence contract gains `modality` |
| **D14** | 8 | Filesystem assets under `<db_dir>/assets/`, content-addressed sha256 sharded; served via gated `GET /assets/{id}/{variant}` |
| **D16** | 9 | CLIP ViT-B/32 via sentence-transformers (Apache-2.0, CPU, bundled) |
| **D17** | 9/10 | `RESKIOSK_IMAGE_SIM_THRESHOLD~0.26` (calibrate), `IMAGE_TOP_N=3`, `IMAGE_PRIMARY_FLOOR=0.30`; admin-curation + no-PII policy (defer face redaction) |

*Still open:* **D5** (feedback-bias state identifier / per-path vs per-merge) — minor, tune-time.

### 1.5 Phases implemented (hub, TDD — encoder/LLM mocked in tests)

**Phase 4 — Slice 5: Compound multi-path retrieval**
`hub/retrieval/multipath_merge.py` (deterministic priority-bucket-then-RRF + attribution); `search.retrieve_multipath` / `build_path_queries`; `secondary_evidence` + `sos_offered` on `/query`; `compound_detected`/`compound_paths` logging; `hub/eval/compound_eval.py`.

**Phase 5 — Slice 6A: Observability & MVP metrics**
Rule-based grounding proxy (`hub/eval/grounding.py`, `rule_v1`); per-stage latency breakdown + `final_evidence` stability anchor; **KPI report by KB version** (`hub/eval/kpi_report.py`, structured-only); fixed eval set (`hub/eval/mvp_eval.py`); 30-day transcript **retention purge** (`hub/db/retention.py`); readable query trace (`logger_stream.format_query_trace`).

**Phase 6 — Slice 6B: Safe caching**
`hub/retrieval/response_cache.py` — config-aware, in-memory TTL+LRU; key = normalized query | intent | language | filters | kb_version | `config_signature`; **safety-critical intents bypass**; invalidate on publish; `cache_status` (hit/miss/bypass) + KPI hit-rate.

**Phase 7 — Slice 7A: Multimodal schema**
`kb_articles` → **`kb_items`** (`KBItem` model + `KBArticle` alias so 54 references untouched); new columns `modality` / `image_asset_id` / `parent_article_id` / `segment_index` / `metadata_json`; evidence contract gains `modality` (+ `render_ref`).

**Phase 8 — Slice 7B: Image asset lifecycle**
`image_assets` table + `hub/services/image_assets.py` — filesystem (content-addressed sha256, sharded, dedup), deterministic Pillow thumbnail + display rendition, **4-state model** (pending/ready/failed/rejected); upload + **gated serving** (`GET /assets/{id}/{variant}`) + admin status endpoints; KB-version linkage + publish invalidation + broken-artifact guard.

**Phase 9 — Slice 7C: Image embeddings & semantic retrieval**
`hub/retrieval/image_embedder.py` (CLIP ViT-B/32 via sentence-transformers, bundled to `hub_models/clip`); image embeddings persisted on `image_assets`, generated at publish (readiness-gated, model-versioned); `search.retrieve_images` (floor + top-N + deterministic tie-break + filter/validation gates); `GET /assets/search`; additive `image_evidence` on `/query`.

**Phase 10 — Slice 7D: hub side only**
`QueryResponse.image_primary` + `RESKIOSK_IMAGE_PRIMARY_FLOOR` (image-first when confident; tentative below — D17). The rest of Phase 10 is front-end (see §2).

### 1.6 Front-end drafts (UNVERIFIED — committed, not built)
- **Console (React):** `console/src/pages/AssetManager.jsx` + wired into `App.jsx` (upload + status + thumbnail previews). Convention-matched, wires to tested endpoints. *(commit `515ab79`)*
- **Kiosk (Kotlin/Compose):** `HubQueryResponse`/`ChatMessage` extended with image fields; **Coil** dependency added; `ui/ImageEvidenceSection.kt` composable (render display rendition, aspect-preserved, loading/broken placeholder, image-first vs tentative). Two wiring edits intentionally left documented, not hacked blind. *(commit `aae9036`)*
- **Neither was built/run** (no gradle/kotlinc, no console test runner here) — treat as review-and-build drafts.

### 1.7 Jira hygiene
Transitioned completed **backend** stories to **Done** with commit-referencing comments as each slice finished (Sprint 3; Slice 5 RK-40–47+RK-9; Slice 6A RK-49–54,103+RK-10; Slice 6B RK-56–61,63+RK-11; Slice 7A RK-64–73+RK-12; Slice 7B RK-74–82,104; Slice 7C RK-83–91,102). Epics with unfinished front-end/eval children (**RK-67, RK-68, RK-69**) were **left open on purpose** with handoff comments. No front-end story was marked Done off unverified code.

---

## 2. What's left to do

### 2.1 Front-end — build & QA the drafts (needs Android Studio / npm)
- **Console `AssetManager`** (RK-81/97/98): `npm` build + click-through QA. Likely close to working.
- **Kiosk image rendering** (RK-93/95/96/101/105): Gradle **sync Coil**, then the **two wiring edits** —
  1. In `KioskViewModel` (assistant `ChatMessage` creation): set `imageEvidence = resp.imageEvidence`, `imagePrimary = resp.imagePrimary == true`.
  2. In `MainKioskScreen` assistant bubble: call `ImageEvidenceSection(hubBaseUrl, message.imageEvidence, message.imagePrimary)`.
  Then build, fix any Compose/Coil API mismatches, QA on device. **RK-101 (log kiosk display outcomes)** is kiosk-side and not started.

### 2.2 Real-model / real-data work (needs bundled CLIP + labeled images)
- **RK-92 — image retrieval evaluation set**: build a labeled query→expected-image set, run against the **real CLIP model**, and **calibrate `RESKIOSK_IMAGE_SIM_THRESHOLD`** (currently a ~0.26 starting guess). Until then image-search precision is **untuned**.
- **S7D.7 — multimodal demo/regression scenarios**: same blocker (real model + images); feeds Phase 11 regression.
- Bundle CLIP into the EXE via `packaging/bundle_models.py` (`bundle_clip()` added) — run `02_download_models.bat` on a build machine.

### 2.3 Deferred hub items
- **S9.tune — feedback-bias tuning** (Goal 9): gated on **D5** (open). Mechanism codeable; final α/cap calibration needs real metrics.
- **RK-62 — safety re-validation for cached responses**: intentionally deferred (D11 chose *bypass*; safety is already correct). Optional.
- **Route double-retrieve cleanup** (tech debt): `/query` runs the pipeline's internal retrieval **and** a second `search.retrieve`; consolidating would cut latency. Optional refactor, well-covered by tests.

### 2.4 Phase 11 — Slice 8: Stabilization
E2E testing, benchmarking, regression, critical-bug pass over the **full stack** (real models + kiosk) — largely a real-deployment activity, not a Python-only task.

### 2.5 Housekeeping
- Open decision **D5** (resolve via the dev-research flow before S9.tune).
- 4 Jira comments were blocked by the permission classifier (status is correct, comment didn't post): **RK-50, RK-54, RK-57, RK-59** — repost on request.
- Epics left open for remaining children: **RK-67** (console UI RK-81/97/98), **RK-68** (RK-92 eval set), **RK-69** (kiosk/console front-end).

---

## 3. Key new files this session

**Hub (Python):**
`hub/retrieval/outcomes.py`, `hub/retrieval/multipath_merge.py`, `hub/retrieval/response_cache.py`, `hub/retrieval/image_embedder.py`, `hub/services/image_assets.py`, `hub/api/routes_assets.py`, `hub/db/retention.py`, `hub/eval/{grounding,kpi_report,mvp_eval,compound_eval}.py` + eval data.
Modified core: `hub/db/schema.py` (kb_items + image_assets + query_logs columns), `hub/retrieval/search.py`, `hub/retrieval/pipeline.py`, `hub/api/routes_query.py`, `hub/api/routes_admin.py`, `hub/models/api_models.py`, `hub/db/migrate_schema.py`, `packaging/bundle_models.py`.

**Front-end (drafts):**
`console/src/pages/AssetManager.jsx`, `kiosk/.../ui/ImageEvidenceSection.kt` (+ `HubApiClient.kt`, `KioskViewModel.kt`, `build.gradle`).

**Tests:** ~13 new hub test files; suite **214 green**.

---

## 4. How to resume

1. Pull `aaih-keith`. Run the hub suite: `python -m unittest discover -s hub/tests -p "test_*.py"` → expect **214 OK**.
2. Front-end: build the console + kiosk drafts, do the kiosk wiring edits, QA. Mark RK-81/93/95/96/97/98/101/105 Done after QA.
3. Real-model: bundle CLIP, build the image eval set (RK-92), calibrate the image floor.
4. Resolve **D5**, then do S9.tune.
5. Phase 11 stabilization on a real deployment.

*(Cross-session memory pointer: `aaih-progress.md` in the agent memory tracks this same state.)*
