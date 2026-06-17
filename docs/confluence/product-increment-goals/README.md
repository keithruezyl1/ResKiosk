---
title: ResKiosk AAIH Product Increment Goals
confluence_id: 98443
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM/pages/98443
parent: ResKiosk AAIH Development Home
last_updated: 2026-04-25T12:25:23.706Z
version: 2
---

# ResKiosk AAIH Product Increment Goals

## Introduction

**ResKiosk** is an evacuation-center information kiosk system designed to help shelter residents get accurate, actionable guidance during emergencies (e.g., registration steps, food/water schedules, medical help, facility locations, and safety procedures) even in constrained or offline environments.

For **AI for ASEAN Hackathon 2026**, we are planning and delivering a **product increment** that upgrades ResKiosk’s AI capabilities to better support real shelter workflows and higher-stakes scenarios.

**Focus of this product increment**

* **Multimodal knowledge base**: ingest, store, and retrieve **images** as first-class KB evidence (originals + thumbnails + versioned invalidation).
* **Semantic image retrieval**: enable image ↔ text semantic search (e.g., landmarks/buildings, first-aid visuals).
* **More reliable retrieval**: implement **hybrid retrieval (BM25 + vectors)** and **multi-path retrieval** for compound queries.
* **Safer interaction flow**: improve **clarification UX** and enforce the pipeline order **normalize → intent → (optional) clarification → constrained rewrite**.
* **Measurement**: add minimum viable **metrics + logging** to quantify grounding, evidence match, and latency.

### Global assumptions (apply to every goal)

* **English at retrieval boundary**: all non-English user input is translated upstream via **NLLB-200** before retrieval.
* **Scale**: KB expected to be \~**500-1000 articles** this increment.
* **Schema-only decision**: **no semantic chunking this increment**; text retrieval unit stays a `kb_articles` **row**. Long-form/PDF content must be **manually split into multiple KB articles** or deferred.
* **Stable ranking**: for a fixed KB version/config, retrieval ordering should be reproducible (except for explicitly enabled feedback bias).

### Prioritization (build order for the product backlog)

This increment is intentionally ordered so we can ship safely and measure correctness before scaling scope.

1. **Product Goal C (Safety & controlled interaction)** — prevent wrong/unsafe behavior first
2. **Product Goal A (Accuracy & reliability)** — make retrieval correct and deterministic
3. **Product Goal D (Observability & trust)** — prove quality with metrics + safe caching
4. **Product Goal B (Visual guidance / multimodal)** — add image capabilities once the core loop is safe and measurable

---

## Goal 1: Semantic image search (CLIP/SigLIP)

* **Currently**: Retrieval is text-embedding cosine similarity only; there is **no image encoder** in the hub, so images cannot be searched semantically.
* **Why we’re developing this**: Residents need reliable visual guidance (landmarks, building identification, first-aid steps) where text-only answers are insufficient.
* **Outcome**: The system supports **image ↔ text semantic search** using a vision-language embedding model (e.g., **CLIP / SigLIP**) and can return image evidence as part of an answer.
* **Success criteria**:

    * Given an English query, the hub can return relevant image results with stable evidence IDs/refs and scores.
    * Directional and first-aid image queries retrieve correct images in the top results on a defined test set.
    
* **Jira breakdown**

    * **User stories**
    
        * As a shelter resident, I can ask “show me the Andres Bonifacio building” and receive a relevant image so that I can navigate correctly.
        * As a shelter resident, I can ask “how do I bandage a wound” and receive step-by-step first aid images so that I can follow safe procedure.
        
    * **Technical tasks**
    
        * Choose and bundle a vision-language model (CLIP/SigLIP) compatible with deployment constraints.
        * Implement image embedding generation at ingest/publish and persistence of image vectors.
        * Implement image retrieval endpoint/response fields (evidence IDs/refs + scores).
        * Add a small evaluation set of image queries and expected top results (for regression checks).
        
    

---

## Goal 2: Image storage as first-class KB assets (original + thumbnail + versioned invalidation)

* **Currently**: KB content is centered on `kb_articles`; images are not modeled as first-class assets with lifecycle/invalidation.
* **Why we’re developing this**: Kiosk UX needs fast image display (thumbnails), and the system needs safe refresh when KB versions change.
* **Outcome**: Image assets are stored with **original + thumbnail**, a **content hash**, and `kb_version` **linkage** so publishing invalidates/refreshes derived caches deterministically.
* **Success criteria**:

    * Publishing a new KB version invalidates image-derived caches and refreshes predictably.
    * Image evidence references are stable and logged with answers and feedback.
    
* **Jira breakdown**

    * **User stories**
    
        * As an admin, I can upload a KB image and the kiosk will display it quickly (thumbnail) so that residents get visual guidance without delay.
        * As an admin, when I publish a new KB version, older image assets are replaced safely so that residents don’t see outdated visuals.
        
    * **Technical tasks**
    
        * Add DB schema for image assets (original ref, thumbnail ref, hash, kb_version, metadata).
        * Implement thumbnail generation and storage conventions.
        * Implement publish-time invalidation hooks for image caches and derived artifacts.
        * Ensure logs can reference image evidence IDs used in answers.
        
    

---

## Goal 3: KB schema rework for multimodal retrieval (schema-only; forward-compatible)

* **Currently**: `kb_articles` stores a single `embedding` blob and Q/A fields; schema does not fully represent multimodal assets, modality, or filtering policy.
* **Why we’re developing this**: CLIP/SigLIP + hybrid retrieval require explicit entities/fields; we must keep the system evolvable without premature complexity.
* **Outcome**: Versioned schema/migrations that support:

    * **modality** (text vs image; extensible)
    * **asset references** for images
    * **metadata fields** required for filtering/rules
    * **forward-compatible fields** for later segmentation (e.g., `parent_article_id`, `segment_index`) without using chunking this increment
    
* **Success criteria**:

    * Migrations are safe; publish increments KB version; retrieval/logs can reference stable IDs for text and image evidence.
    
* **Jira breakdown**

    * **User stories**
    
        * As an admin, I can manage KB items that are either text articles or images so that both can be served as evidence.
        * As a developer, I can evolve the KB schema without breaking older versions so that releases remain safe.
        
    * **Technical tasks**
    
        * Design and implement schema migrations for modality + assets + forward-compatible segmentation fields (without enabling chunking).
        * Update ingest/publish flows to write the new schema consistently and increment KB version.
        * Update retrieval/logging contracts to include modality-aware evidence references.
        
    

---

## Goal 4: Hybrid retrieval with BM25 + vectors (reproducible ranking)

* **Currently**: Retrieval is vector-only; there is no lexical index/BM25.
* **Why we’re developing this**: Exact terms (building names, procedures) need lexical determinism; hybrid improves recall and debuggability.
* **Outcome**: Implement BM25 (or equivalent lexical retrieval) and fuse with vector search using an explicit strategy (e.g., **RRF**) with reproducible ordering per KB version/config.
* **Success criteria**:

    * Exact-term queries reliably surface correct articles in top results on a test set.
    * Rankings are stable for a fixed KB version/config.
    
* **Jira breakdown**

    * **User stories**
    
        * As a shelter resident, when I ask using an exact building/clinic name, I get the correct article so that I can act confidently.
        * As a staff member, I can trust that the same query on the same KB version yields the same top answer so that guidance is consistent.
        
    * **Technical tasks**
    
        * Add a lexical index for KB articles (BM25 or equivalent) and define what fields are indexed (question, tags, optional metadata).
        * Implement fusion strategy (RRF or equivalent) with reproducible scoring and tie-breaking.
        * Add regression tests for deterministic ranking on a fixed KB snapshot.
        
    

---

## Goal 5: Multi-path (split/dual) retrieval for compound queries

* **Currently**: Compound handling concatenates intent enrichment into one query and runs a single retrieval pass.
* **Why we’re developing this**: One-pass enrichment can hide critical sub-intents (medical/safety). Multi-path retrieval improves precision and supports intent priority.
* **Outcome**: For compound queries, run **separate retrieval paths** per intent/subtask and merge with explicit rules (priority + fusion).
* **Success criteria**:

    * Compound scenarios (e.g., medical + nearest help + SOS offer) produce correct primary answer plus correct secondary prompt/actions.
    * Logs attribute evidence to the retrieval path/intent that produced it.
    
* **Jira breakdown**

    * **User stories**
    
        * As a resident, when I ask for medical help and nearest doctor, I get both medical guidance and location guidance so that I can get help quickly.
        * As a resident, when my query indicates urgency, I am offered an SOS option so that I can escalate safely.
        
    * **Technical tasks**
    
        * Define compound query decomposition rules (intent-driven split) and merge rules (priority + fusion).
        * Implement dual retrieval execution and evidence attribution per path/intent.
        * Update response payload to include multiple evidence items and follow-up prompts/actions.
        
    

---

## Goal 6: Clarification UX before rewriting

* **Currently**: Clarification exists but is not fully productized; ambiguity handling is limited.
* **Why we’re developing this**: Kiosk users ask incomplete/ambiguous questions; wrong answers reduce trust and increase retries.
* **Outcome**: A clarification flow that triggers on low-confidence/ambiguous cases and offers fast UI choices (chips) **before** rewrite/retrieve continues.
* **Success criteria**:

    * Clarification resolves ambiguity within 1–2 steps for defined scenarios.
    * Clarification resolutions are logged (session → resolved intent/category).
    
* **Jira breakdown**

    * **User stories**
    
        * As a resident, when my question is unclear, I can pick from 2–3 options so that I reach the right topic quickly.
        * As an operator, I can review what residents clarified so that we can improve content and prompts.
        
    * **Technical tasks**
    
        * Define clarification triggers (confidence, ambiguity, missing required scope) and chip option sets.
        * Implement clarification UI/flow integration and persistence to `clarification_resolutions`.
        * Ensure clarification happens before rewrite and is represented in logs.
        
    

---

## Goal 7: Metadata schema + filtering policy (UI + inferred + hard rules)

* **Currently**: Basic fields exist (`category`, `tags`, `enabled`, `status`) but filtering precedence is not formalized and enforceable end-to-end.
* **Why we’re developing this**: Multimodal KB and safety constraints require explicit scoping; filters prevent unsafe/irrelevant results.
* **Outcome**: Implement metadata filtering with explicit precedence:

    * **Hard system rules** override all
    * **User UI filters** override inference
    * **Inferred intent** fills missing constraints
    
* **Success criteria**:

    * Applied filters are logged and explainable.
    * Filter changes produce predictable behavior for the same query + KB version.
    
* **Jira breakdown**

    * **User stories**
    
        * As a resident, I only see information relevant to my center/context so that I don’t follow incorrect guidance.
        * As an admin, I can enforce safety constraints so that unsafe content is never served.
        
    * **Technical tasks**
    
        * Define filter fields and precedence rules (hard rules > UI > inferred intent).
        * Implement filtering in retrieval for both lexical and vector paths.
        * Add logging of applied filters and reasons (auditability).
        
    

---

## Goal 8: Metadata validation gate (rules + stats + human review before KB publish)

* **Currently**: There is no formal publish gate for autogenerated metadata/captions.
* **Why we’re developing this**: Bad metadata breaks filtering/retrieval and is risky for medical/safety content.
* **Outcome**: Default validation pipeline is **rules + statistical checks + human review** before publish. LLM-as-judge is allowed **offline/batch**, not in the hot path.
* **Success criteria**:

    * Low-confidence/rule-failing metadata is quarantined until reviewed.
    * Review outcomes are auditable and tied to KB version.
    
* **Jira breakdown**

    * **User stories**
    
        * As an admin, I can review and approve autogenerated metadata so that only verified labels ship to residents.
        * As a resident, I can trust that filtered results are based on validated metadata so that answers remain safe.
        
    * **Technical tasks**
    
        * Define validation rules and statistical checks for captions/labels.
        * Implement “quarantine vs approved” workflow for KB publish.
        * Implement offline/batch LLM-judge hook (optional) for admin review support (not on the hot path).
        
    

---

## Goal 9: Retrieval quality improvements without heavy reranking (keep feedback bias; focus on retrieval stack)

* **Currently**: “RLHF” is a scalar bias adjustment to cosine scores (feedback-adjusted ranking), not a true reranker.
* **Why we’re developing this**: Biggest gains this increment should come from hybrid + multi-path retrieval + clarification + constrained rewrite.
* **Outcome**: Keep feedback bias as a tunable signal, but improve quality primarily via the retrieval architecture changes in Goals 4–6.
* **Success criteria**:

    * Precision improves on an evaluation set without adding a cross-encoder reranker this increment.
    * Bias effects are measurable and safe (enable/disable; logged).
    
* **Jira breakdown**

    * **User stories**
    
        * As a resident, I get better answers over time as the system incorporates feedback so that the kiosk improves in real deployments.
        * As a maintainer, I can understand why an answer ranked higher so that tuning is safe.
        
    * **Technical tasks**
    
        * Keep feedback bias as a distinct layer and ensure it doesn’t break deterministic ranking expectations (when enabled, it’s still reproducible given bias state).
        * Add monitoring for bias impact (top-1 changes vs raw cosine / hybrid baseline).
        * Calibrate thresholds/gating with the new hybrid + multi-path retrieval outputs.
        
    

---

## Goal 10: MVP metrics + logging for grounding, evidence match, and latency

* **Currently**: `query_logs` has basic fields (including `latency_ms`), but MVP evaluation instrumentation is not complete.
* **Why we’re developing this**: Without metrics, retrieval/model changes are subjective and regressions are hard to detect.
* **Outcome**: Implement logging sufficient to compute:

    * grounded answer rate (sampled/manual + optional offline checks)
    * hallucination proxy (unsupported spans vs retrieved evidence)
    * citation/source/evidence match & stability
    * latency breakdown (at least retrieve vs overall; expand as feasible)
    
* **Success criteria**:

    * Logs support metric computation per KB version, intent, and modality.
    
* **Jira breakdown**

    * **User stories**
    
        * As a maintainer, I can measure whether answers are grounded in KB evidence so that we can reduce hallucinations.
        * As a stakeholder, I can see latency and success rates so that we can judge readiness for deployment.
        
    * **Technical tasks**
    
        * Define event/log schema for: evidence IDs, retrieval scores, fusion details, rewrite/clarification steps, latency breakdown.
        * Implement instrumentation in hub routes and persistence in `query_logs` (and related tables as needed).
        * Create a minimal evaluation workflow (query set + label capture via `feedback_logs` and/or manual review).
        
    

---

## Goal 11: Safer caching patterns (version + TTL + refresh hooks)

* **Currently**: In-memory caches exist for corpus/config; response-level caching is not implemented as a product goal.
* **Why we’re developing this**: Kiosk needs speed; cached wrong answers are worse than slower correct answers.
* **Outcome**: Caching keyed by normalized query/resolved intent + **KB version** (+ relevant config version), with TTL and publish-time invalidation.
* **Success criteria**:

    * Cache invalidates automatically on KB publish/config updates; cache behavior is observable (hit/miss logged).
    
* **Jira breakdown**

    * **User stories**
    
        * As a resident, I get fast answers without seeing outdated information so that I can act safely.
        * As an admin, when I publish updates, kiosks stop serving old answers quickly so that changes take effect.
        
    * **Technical tasks**
    
        * Define cache keys (normalized query, resolved intent, filters, KB version, config version) and TTL policy.
        * Implement invalidation hooks on publish/config update and log cache hit/miss.
        * Add optional lightweight re-validation hook (e.g., compare top evidence IDs) before serving cached responses in safety-critical intents.
        
    

---

## Goal 12: Canonical pipeline order (normalize → intent → optional clarification → constrained rewrite)

* **Currently**: Normalization/intent/rewrite exist, but ordering/constraints are not enforced as a product requirement.
* **Why we’re developing this**: Correct ordering reduces ambiguity, prevents unsafe rewrite expansion, and improves hybrid retrieval performance.
* **Outcome**: Enforce the pipeline order and log: normalized query, intent, clarification (if any), rewrite constraints/output.
* **Success criteria**:

    * Clarification (when triggered) occurs before rewrite.
    * Rewrites respect hard rules and are logged deterministically.
    

---

## Higher-level outcomes (grouped product goals)

### Product Goal A (Epic) — Ensure residents receive accurate and reliable answers in emergency scenarios

* Goal 4: Hybrid retrieval with BM25 + vectors (reproducible ranking)
* Goal 5: Multi-path (split/dual) retrieval for compound queries
* Goal 9: Retrieval quality improvements without heavy reranking

### Product Goal B (Epic) — Enable residents to use visual guidance for navigation and first aid

* Goal 1: Semantic image search (CLIP/SigLIP)
* Goal 2: Image storage as first-class KB assets
* Goal 3: KB schema rework for multimodal retrieval (schema-only; forward-compatible)

### Product Goal C (Epic) — Ensure safe and controlled kiosk interactions under uncertainty

* Goal 6: Clarification UX before rewriting
* Goal 7: Metadata schema + filtering policy (UI + inferred + hard rules)
* Goal 8: Metadata validation gate (rules + stats + human review before KB publish)
* Goal 12: Canonical pipeline order (normalize → intent → optional clarification → constrained rewrite)

### Product Goal D (Epic) — Increase system trust through observability and safe performance optimizations

* Goal 10: MVP metrics + logging
* Goal 11: Safer caching patterns (version + TTL + refresh hooks)

## Session notes: codebase + `reskiosk_db.md` (do not delete — working context)

### Confirmed from codebase

* **Embeddings:** `hub/retrieval/embedder.py` loads `SentenceTransformer` from bundled `all-MiniLM-L6-v2`. Only `embed_text()` exists — **no image encoder**. `get_embeddable_text()` uses **question + tags only** (answer body excluded on purpose).
* **Retrieval:** `hub/retrieval/search.py` — **single** query embedding vs **in-memory matrix** of article vectors; `sentence_transformers.util.cos_sim`. **No BM25**, no Elasticsearch/OpenSearch, no SQLite FTS for articles.
* **“RLHF”:** Env-gated `RESKIOSK_RLHF_ENABLED`. Applies **per-article bias** from `article_biases` to cosine scores (`RLHF_ALPHA`). **Not** online learning / policy gradients; **not** a cross-encoder reranker.
* **Compound queries:** `classify_top2` + `_resolve_compound_intents` can mark compound and merge **both intents’ enrichment strings into one** `search_query`. Still **one** embedding and **one** retrieval pass — **no parallel** sub-queries.
* **Clarification:** `needs_clarification()` returns true only when `intent == "unclear"` AND **best retrieval score <** `CLARIFICATION_FLOOR` (and not suppressed by compound shortcut). “Ambiguous scope” is **not** a separate coded trigger — it’s approximated by **unclear intent + low score**.
* **Caching today:** In-memory `_corpus_cache` (embeddings) and `_shelter_config_cache`; invalidated on publish/admin paths. **No** response-level FAQ cache yet (your item 15 is greenfield).

### `reskiosk_db.md` — fields relevant to backlog

* `kb_articles`**:** `id`, `question`, `answer`, `category`, `tags`, `enabled`, `source`, `created_at`, `last_updated`, `embedding` **(BLOB)**, `status`, `created_by`, `updated_by`.
* **Versioning:** `kb_meta.kb_version`, `query_logs.kb_version`, `system_version.kb_version` — use these for **cache invalidation** and audit trails.
* **Feedback / “RLHF” bias:** `feedback_logs` (per interaction), `article_biases` (`source_id`, `bias`, `updated_at`).
* **Clarification analytics:** `clarification_resolutions` (`session_id`, `resolved_intent`, `language`, …).
* **Shelter/runtime config:** `evac_info`, `structured_config` — align metadata filters and pre-filters with what you already store here before inventing new tables.

### Recommendations captured from discussion (for next design pass)

* **1b Embeddings:** MiniLM **does not** embed images. Practical pattern: **text** (EN/tl/ceb) via multilingual sentence model _or_ keep MiniLM short-term + **separate** CLIP/SigLIP **or** image→caption/OCR→same text pipeline. True single “lightweight” model for **photo of building + Tagalog query** with SOTA text quality is uncommon — **dual path** is the usual tradeoff.
* **6b/c Images:** Store **original** + **thumbnail** (kiosk UI); add **content hash** / `kb_version` for invalidation. PII policy TBD.
* **8b Metadata (starter set):** Leverage existing: `source_id`, `category`, `tags`, `status`, `enabled`, `last_updated`, `kb_version` (session/query). New work: `modality`, `locale`, `parent_article_id` (PDF multi-article), `chunk_index`, image asset refs — extend schema deliberately (versioned migrations).
* **9a LLM-as-judge:** Optional **offline** or **human-review queue** to avoid latency bloat; rules + confidence first.
* **10b “Optimal” reranker:** Phase 1: **hybrid + RRF** + thresholding. Phase 2: **cross-encoder** on top-k only if metrics show need. Keep **bias-from-feedback** as separate tunable layer; rename stakeholder-facing “RLHF” → **“feedback-adjusted ranking”** unless you add real RL.
* **12c MVP metrics (example set):** (1) **Answer supported rate** — claims checkable against `article_data` / retrieved text. (2) **Hallucination proxy** — unsupported spans vs context (LLM or rule-based for MVP). (3) **Citation / source match** — `source_id` stability vs top-1 raw cosine. (4) **Latency** — STT + retrieve + TTS from `query_logs.latency_ms` / breakdown fields. (5) **Thumb feedback rate** optional.
* **13a Filters:** Yes, combine **UI + inferred intent + hard rules** — precedence should be explicit (e.g. hard safety > user filter > inferred).
* **14c Staged filtering:** With **\~1k–5k** articles and SQLite-scale corpus, **likely defer** staged ANN pre/post filter until profiling shows **latency or index** pain; still add **metadata columns** early if you know filters are coming.
* **15c Cache safety:** Do **not** use “other sessions’ thumbs” as primary truth for correctness. Prefer `kb_version` **+ TTL** + optional **re-validate top answer** against current retrieval hash.
* **18c Clarification UX:** Offer **2–3 tap chips** (categories / “which building”) before free-text re-query; keep **one** fallback “Say that differently” with example.
* **19a Rewrite:** **Structured filters** for high-stakes (medical, child safety); **NL rewrite** for noisy STT. Order: normalize → intent → **optional clarification** → rewrite with constraints.
* **16b / 20b Compound merge:** **Retrieve top-k per sub-intent** (or split query) then **RRF** or **priority merge** (safety/medical first); parallel **fan-out** only after you have **multiple retrieval keys** (not one concatenated embedding).
