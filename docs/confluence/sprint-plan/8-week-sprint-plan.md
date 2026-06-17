---
title: 8-Week Sprint Plan
confluence_id: 6193162
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM/pages/6193162
parent: ResKiosk AAIH Development Home
last_updated: 2026-05-03T06:20:48.516Z
version: 2
---

# 8-Week Sprint Plan

**Final codebase submission date:** June 20  
**Feature-complete cutoff:** June 14  
**Final stabilization window:** June 15–June 20  
**Sprint format:** Weekly sprints  
**Sprint 1 status:** Delivered  
**Sprint 8 purpose:** End-to-end testing, benchmarking, regression, critical bug fixes, and final submission preparation

This document summarizes the 8-week Jira sprint plan for the ResKiosk AAIH product increment. It identifies the sprint goals, deadlines, included implementation slices, assigned user stories, and items removed or deferred from the active sprint scope.

The final sprint plan protects Sprint 8 for validation and submission work only, with planned feature implementation completed by Sprint 7. :contentReference\[oaicite:0\]{index=0}

---

# Sprint Schedule

| Sprint | Dates | Main Focus |
| --- | --- | --- |
| Sprint 1 | Apr 27–May 3 | Pipeline backbone + filtering foundation |
| Sprint 2 | May 4–May 10 | Clarification UX + validation/publish foundation |
| Sprint 3 | May 11–May 17 | Validation completion + hybrid retrieval/logging |
| Sprint 4 | May 18–May 24 | Multi-path retrieval + observability |
| Sprint 5 | May 25–May 31 | Metrics wrap-up + multimodal schema/assets prep |
| Sprint 6 | Jun 1–Jun 7 | Image asset completion + admin/kiosk safety prep |
| Sprint 7 | Jun 8–Jun 14 | Multimodal image workflow + kiosk image display |
| Sprint 8 | Jun 15–Jun 20 | E2E, benchmarking, regression, final submission |

---

# Sprint 1 — Apr 27–May 3

## Sprint Status

**Delivered fully**

## Sprint Goal

Establish the backend foundation for the increment: canonical query orchestration, initial pipeline logging, taxonomy structure, metadata fields, and hard retrieval safety rules.

## Slices Included

* **Slice 0 — Backbone Contract**
* **Slice 1 — Controlled Scope Foundation**

## User Stories

### Slice 0 — Backbone Contract

1. **Create canonical pipeline orchestrator**  
  Establishes a single backend query pipeline so normalize, intent detection, clarification, rewrite, and retrieval happen in a controlled order.
2. **Add pipeline stage logging skeleton**  
  Adds initial logging for major query stages so later pipeline behavior can be observed and debugged.
3. **Add clarification pause state to query flow**  
  Allows the query flow to pause for clarification before rewrite or retrieval occurs.

### Slice 1 — Controlled Scope Foundation

4. **Define taxonomy v1 data model**  
  Creates the controlled taxonomy structure used for filtering, clarification chips, and later validation.
5. **Add metadata fields for retrieval filtering**  
  Adds filterable metadata to KB items so retrieval can be scoped safely.
6. **Enforce hard retrieval rules**  
  Ensures disabled or unpublished KB evidence is never returned to residents.
7. **Apply UI and inferred intent filters with precedence**  
  Implements filtering order so hard rules, user-selected filters, and inferred intent constraints behave predictably.
8. **Log filter decisions and candidate counts**  
  Records why evidence was included or excluded during retrieval.

## Sprint Total

**44 story points**  
**8 stories**

## Removed / Deferred from Sprint

None. Sprint 1 was delivered fully.

---

# Sprint 2 — May 4–May 10

## Sprint Goal

Build the clarify-first interaction layer and begin enforcing trusted metadata publishing.

## Slices Included

* **Slice 2 — Clarify-first UX**
* **Slice 3 — Trusted KB Publish**

## User Stories

### Slice 2 — Clarify-first UX

1. **Implement clarification trigger policy**  
  Defines when the system should ask for clarification based on ambiguity, low confidence, or missing scope.
2. **Return taxonomy-backed clarification chips**  
  Returns 2–3 structured clarification choices backed by taxonomy IDs.
3. **Add kiosk clarification chip UI**  
  Adds resident-facing chip UI on the kiosk for clarification choices.
4. **Implement clarification retry contract**  
  Allows the kiosk to send a selected clarification option back to the hub so the pipeline can resume deterministically.
5. **Persist clarification resolution**  
  Stores the selected clarification option and resolved intent/taxonomy context.
6. **Log clarification lifecycle events**  
  Logs trigger reason, options shown, selection, and downstream resolution.

### Slice 3 — Trusted KB Publish

7. **Implement metadata validation rule engine**  
  Adds rule-based validation checks for metadata before publish.
8. **Add validation status and audit storage**  
  Stores validation states, rule results, and audit information.
9. **Gate KB publish using validation results**  
  Begins enforcing validation results in the publish flow.

## Sprint Total

**53 story points**  
**9 stories**

## Removed / Deferred from Sprint

None.

---

# Sprint 3 — May 11–May 17

## Sprint Goal

Complete trusted publish validation, implement hybrid retrieval, and establish core structured logging needed to observe retrieval behavior.

## Slices Included

* **Slice 3 — Trusted KB Publish**
* **Slice 4 — Deterministic Retrieval Core**
* **Slice 6A — Observability & Trust**

## User Stories

### Slice 3 — Trusted KB Publish

1. **Build MVP metadata review workflow**  
  Allows operators to approve, reject, or override quarantined metadata with an audit trail.
2. **Exclude quarantined metadata from retrieval**  
  Prevents unapproved metadata from affecting resident-facing retrieval.
3. **Log validation and publish audit events**  
  Records validation outcomes, review decisions, and publish audit details.

### Slice 4 — Deterministic Retrieval Core

4. **Build lexical retrieval index**  
  Adds a BM25-like lexical search path over selected KB fields.
5. **Implement BM25-like lexical scoring**  
  Returns lexical candidates with deterministic scores and ranks.
6. **Fuse lexical and vector results with RRF**  
  Combines lexical and vector retrieval into one stable ranked result set.
7. **Apply filter policy to hybrid retrieval**  
  Ensures both lexical and vector retrieval obey filtering and validation rules.
8. **Add hybrid retrieval contribution logging**  
  Logs lexical, vector, and fusion contributions for explainability.
9. **Create exact-term retrieval evaluation set**  
  Adds a small test set to measure exact-term retrieval improvements.

### Slice 6A — Observability & Trust

10. **Complete structured query log schema**  
  Expands query logs so system behavior can be analyzed by request, KB version, intent, and evidence.
11. **Add failure and fallback outcome logging**  
  Captures failures, fallback reasons, and partial pipeline outcomes.

## Sprint Total

**59 story points**  
**11 stories**

## Removed / Deferred from Sprint

* **Slice 4 - Tune feedback-adjusted ranking as a separate layer**  
  Deferred because the current feedback/FAQ-style mechanism already exists and the increment’s main retrieval improvements come from hybrid retrieval, filtering, clarification, and multi-path handling.

---

# Sprint 4 — May 18–May 24

## Sprint Goal

Implement compound query handling and complete the main observability foundation.

## Slices Included

* **Slice 5 — Compound Correctness**
* **Slice 6A — Observability & Trust**

## User Stories

### Slice 5 — Compound Correctness

1. **Detect compound queries using top-2 intents**  
  Identifies multi-intent queries using the top two detected intents.
2. **Build intent-scoped retrieval path queries**  
  Creates separate retrieval paths for each detected sub-intent.
3. **Run retrieval separately per compound path**  
  Runs retrieval independently for each compound query path.
4. **Merge compound path results deterministically**  
  Combines path results using explicit priority and tie-break rules.
5. **Add evidence attribution for compound results**  
  Records which intent/path produced each returned evidence item.
6. **Support primary and secondary compound response outputs**  
  Allows compound answers to present primary and secondary guidance clearly.
7. **Log compound lifecycle and merge decisions**  
  Logs compound detection, path queries, per-path results, and merge decisions.
8. **Create compound retrieval evaluation scenarios**  
  Adds scenarios to compare single-path and multi-path behavior.

### Slice 6A — Observability & Trust

9. **Add latency breakdown logging**  
  Captures pipeline timing for retrieval, rewrite, clarification, and overall query handling.
10. **Capture final evidence list and stability fields**  
  Stores final evidence IDs, scores, ranks, and modality where available.
11. **Implement MVP metrics export workflow**  
  Enables basic export or reporting of MVP metrics.
12. **Create grounding proxy review fields**  
  Adds fields needed for manual or sampled grounding review.
13. **Format hub query logs for readable operational observability**  
  Makes live hub logs readable during development, demos, and field operation.

## Sprint Total

**63 story points**  
**13 stories**

## Removed / Deferred from Sprint

None.

---

# Sprint 5 — May 25–May 31

## Sprint Goal

Finish metrics/reporting, establish the multimodal schema foundation, and prepare early image asset, model, payload, and admin upload work.

## Slices Included

* **Slice 6A — Observability & Trust**
* **Slice 7A — Multimodal Schema**
* **Slice 7B — Image Asset Lifecycle**
* **Slice 7C — Image Embeddings & Semantic Retrieval**
* **Slice 7D — Kiosk Image Rendering & Multimodal Demo**

## User Stories

### Slice 6A — Observability & Trust

1. **Create fixed evaluation query set**  
  Adds a small query set for repeatable evaluation across retrieval and clarification scenarios.
2. **Generate basic KPI report by KB version**  
  Produces a basic report summarizing quality and performance metrics by KB version.

### Slice 7A — Multimodal Schema

3. **Add multimodal KB item schema**  
  Updates the KB schema so evidence can be represented as text or image.
4. **Add stable multimodal evidence identity**  
  Ensures text and image evidence can be referenced consistently in logs and responses.
5. **Prepare image asset reference fields**  
  Adds schema support for linking image evidence to stored image assets.
6. **Add forward-compatible segmentation fields**  
  Adds future-ready segmentation fields without enabling semantic chunking.
7. **Update evidence response contract for modality**  
  Updates response payloads so downstream systems can distinguish text and image evidence.
8. **Backfill existing KB articles as text modality**  
  Preserves existing text articles under the new modality-aware schema.
9. **Add modality-aware evidence logging**  
  Logs evidence modality alongside evidence IDs and scores.

### Slice 7B — Image Asset Lifecycle

10. **Store image assets as first-class KB assets**  
  Adds durable image asset records with stable identity.
11. **Add image upload API for KB assets**  
  Provides a backend upload path for adding image assets.
12. **Generate content hashes for image assets**  
  Adds deterministic content hashes for identity, integrity, and cache/version behavior.
13. **Generate deterministic thumbnails for image assets**  
  Creates thumbnail renditions for fast kiosk display.

### Early Integration / Admin Prep

14. **Select and configure image embedding model**  
  Selects and configures the CLIP/SigLIP-style model used for image embeddings.
15. **Add hub-to-kiosk image evidence payload support**  
  Prepares the kiosk response model to accept image evidence fields.
16. **Add admin image upload and asset confirmation path**  
  Adds a basic admin path for uploading and confirming image assets.
17. **Create multimodal demo scenarios**  
  Defines demo scenarios for landmark, navigation, and first-aid visual guidance.

## Sprint Total

**87 story points**  
**17 stories**

## Removed / Deferred from Sprint

None.

---

# Sprint 6 — Jun 1–Jun 7

## Sprint Goal

Complete image asset lifecycle, add basic admin asset/status visibility, and finish kiosk image safety behavior.

## Slices Included

* **Slice 7B — Image Asset Lifecycle**
* **Slice 7D — Kiosk Image Rendering & Multimodal Demo**

## User Stories

### Slice 7B — Image Asset Lifecycle

1. **Add image asset processing states**  
  Adds pending, ready, failed, and rejected states for image assets.
2. **Link image assets to KB version**  
  Ties image assets and derived artifacts to a KB version.
3. **Invalidate image artifacts on KB publish**  
  Ensures image-derived artifacts do not remain stale across KB publishes.
4. **Add admin asset confirmation view**  
  Allows admins to confirm uploaded image assets and basic processing results.
5. **Log image asset lifecycle events**  
  Logs upload, processing, thumbnail, rendition, failure, and invalidation events.
6. **Compress uploaded images and generate optimized renditions**  
  Creates compressed kiosk-ready image renditions for faster display.

### Slice 7D — Kiosk Image Rendering & Multimodal Demo

7. **Handle image loading failures and placeholders**  
  Ensures the kiosk handles missing or broken image references safely.
8. **Display image asset status in admin console**  
  Shows basic image asset readiness/status information in the admin interface.
9. **Validate text-only fallback when image evidence is unavailable**  
  Ensures text guidance still works if image evidence fails or is unavailable.
10. **Optimize kiosk image loading and display**  
  Improves kiosk display behavior for thumbnails and compressed renditions.

## Sprint Total

**44 story points**  
**10 stories**

## Removed / Deferred from Sprint

None.

---

# Sprint 7 — Jun 8–Jun 14

## Sprint Goal

Deliver the core multimodal image workflow before the feature-complete cutoff.

## Slices Included

* **Slice 7C — Image Embeddings & Semantic Retrieval**
* **Slice 7D — Kiosk Image Rendering & Multimodal Demo**

## User Stories

### Slice 7C — Image Embeddings & Semantic Retrieval

1. **Implement image embedding generation service**  
  Adds the backend service for generating embeddings from ready image assets.
2. **Persist image embeddings with model and KB version metadata**  
  Stores image embeddings with evidence, model, and KB version context.
3. **Generate image embeddings during ingest or publish**  
  Ensures embeddings are generated as part of the KB ingest/publish workflow.
4. **Implement text-to-image semantic retrieval path**  
  Allows English text queries to retrieve semantically relevant image evidence.
5. **Merge image evidence with text evidence response structure**  
  Allows image evidence to be returned alongside text evidence.
6. **Apply filtering and validation gates to image retrieval**  
  Ensures image retrieval obeys filtering, validation, readiness, and publish rules.
7. **Add image retrieval thresholds and deterministic tie-breaks**  
  Adds confidence thresholds and stable ranking behavior for image retrieval.
8. **Log image retrieval evidence and model metadata**  
  Logs image evidence IDs, scores, model version, thresholds, and latency.

### Slice 7D — Kiosk Image Rendering & Multimodal Demo

9. **Render image evidence in kiosk responses**  
  Displays returned image evidence in the kiosk UI.
10. **Support image-first response behavior**  
  Supports visual-first behavior for queries such as “show me the clinic.”

## Sprint Total

**58 story points**  
**10 stories**

## Removed / Deferred from Sprint

None from required image functionality.

---

# Sprint 8 — Jun 15–Jun 20

## Sprint Goal

Validate, benchmark, stabilize, and submit. Sprint 8 contains no planned feature development.

## Work Type

These should be represented in Jira as **Tasks**, **Bugs**, or **Test Tasks**, not feature stories.

## Assigned Work

### End-to-End Testing

1. **Run full text-query E2E test**  
  Tests query input through response and logging.
2. **Run clarification E2E test**  
  Tests ambiguity detection, clarification chips, retry, and logged resolution.
3. **Run hybrid retrieval E2E test**  
  Tests lexical/vector retrieval, fusion, filtering, and contribution logs.
4. **Run compound query E2E test**  
  Tests multi-path retrieval, deterministic merge, and primary/secondary evidence.
5. **Run multimodal E2E test**  
  Tests upload, thumbnails/renditions, embeddings, image retrieval, kiosk display, and image-first behavior.

### Benchmarking

6. **Benchmark query latency**  
  Measures total, retrieval, rewrite, and clarification latency.
7. **Benchmark hybrid and multi-path retrieval**  
  Measures quality and stability of hybrid and compound retrieval behavior.
8. **Benchmark image retrieval**  
  Measures image embedding/retrieval latency and top-k image match quality.
9. **Benchmark kiosk image loading**  
  Measures thumbnail and compressed rendition loading behavior.

### Regression + Submission

10. **Run regression suite against fixed KB snapshot**  
  Confirms the final build behaves consistently on a fixed KB snapshot.
11. **Generate final KPI report by KB version**  
  Produces the final report for readiness and evaluation.
12. **Verify hub logs are readable during demo flow**  
  Confirms operational logs are clear during the final demo.
13. **Validate image retrieval evaluation set**  
  Confirms image retrieval works against expected results.
14. **Validate multimodal regression set**  
  Confirms multimodal behavior remains stable.
15. **Verify kiosk image display outcomes**  
  Confirms image evidence is displayed, suppressed, or failed safely as expected.
16. **Fix critical/blocking bugs only**  
  Limits final development changes to issues blocking submission or demo validity.
17. **Freeze codebase**  
  Locks the implementation after final fixes.
18. **Prepare final submission package**  
  Packages the final codebase and supporting materials.
19. **Run final demo rehearsal**  
  Confirms the final demo path works end-to-end.

## Sprint 8 Total

**0 planned feature story points**  
**19 testing/stabilization tasks**

## Removed / Deferred from Sprint

No feature stories are scheduled in Sprint 8. Planned feature development ends in Sprint 7.

---

# Overall Assignment Summary

| Sprint | Stories / Tasks | Story Points | Main Output |
| --- | --- | --- | --- |
| Sprint 1 | 8 stories | 44 | Pipeline + filtering foundation — delivered |
| Sprint 2 | 9 stories | 53 | Clarification UX + validation/publish foundation |
| Sprint 3 | 11 stories | 59 | Validation completion + hybrid retrieval/logging |
| Sprint 4 | 13 stories | 63 | Multi-path retrieval + observability |
| Sprint 5 | 17 stories | 87 | Metrics wrap-up + multimodal schema/assets prep |
| Sprint 6 | 10 stories | 44 | Image asset completion + admin/kiosk safety prep |
| Sprint 7 | 10 stories | 58 | Multimodal image workflow + kiosk image display |
| Sprint 8 | 19 tasks | 0 | E2E, benchmarking, regression, final submission |
| **Total Required Feature Scope** | **78 feature stories + 19 final tasks** | **408** | Feature-complete by Jun 14; final submission by Jun 20 |

---

# Deferred / Stretch Backlog

The following work is not required for the June 20 MVP submission.

## Slice 6B — Safe Caching

1. **Define version-aware cache key structure** — 5 pts
2. **Implement response-level cache storage** — 8 pts
3. **Add TTL policy and cache bypass rules** — 5 pts
4. **Invalidate cache on KB publish** — 5 pts
5. **Invalidate cache on config update** — 5 pts
6. **Log cache hit, miss, and bypass decisions** — 3 pts
7. **Add safety re-validation for cached high-stakes responses** — 8 pts
8. **Add cache behavior tests** — 5 pts

**Deferred total:** 44 pts

## Other Stretch Item

1. **Tune feedback-adjusted ranking as a separate layer** — 5 pts

**Additional deferred total:** 5 pts

## Total Deferred

**49 story points**

## Why This Work Was Deferred

### Safe Caching

Safe caching was deferred because it is primarily a performance optimization. It is valuable, but the increment can still demonstrate its core product value without response-level caching. The protected MVP focuses first on correctness, safety, retrieval quality, multimodal image support, kiosk display, and final validation.

### Feedback-Adjusted Ranking Tuning

Feedback-adjusted ranking tuning was deferred because ResKiosk already has a basic feedback/FAQ-style mechanism. The main retrieval improvements in this increment come from clarification, filtering, hybrid retrieval, and multi-path retrieval. Ranking-bias tuning can be improved later without blocking the required image workflow.

---

# Final Notes

This sprint plan keeps the June 20 submission goal focused on a complete, demonstrable product increment:

1. Controlled query pipeline
2. Safe retrieval filtering
3. Clarification UX
4. Metadata validation and publish control
5. Hybrid retrieval
6. Compound query handling
7. Metrics and observability
8. Multimodal schema
9. Image asset upload/storage/renditions
10. Image embeddings
11. Text-to-image retrieval
12. Kiosk image rendering
13. Image-first visual response behavior
14. End-to-end testing and benchmarking

‌
