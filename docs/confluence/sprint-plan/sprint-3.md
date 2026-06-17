---
title: Sprint 3
confluence_id: 9076739
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM/pages/9076739
parent: 8-Week Sprint Plan
last_updated: 2026-05-11T08:43:48.610Z
version: 2
---

# Sprint 3

# Sprint Goal

Complete trusted publish validation, implement deterministic hybrid retrieval, and establish the core structured logging needed to observe retrieval behavior.

By the end of Sprint 3, ResKiosk should be able to:

1. Review and audit quarantined metadata.
2. Prevent quarantined metadata from affecting resident-facing retrieval.
3. Log validation and publish audit events.
4. Build and query a lexical retrieval index.
5. Score exact-term matches using BM25-like retrieval.
6. Fuse lexical and vector results deterministically.
7. Apply filtering policy to hybrid retrieval.
8. Log retrieval contributions from lexical, vector, and fused results.
9. Run an exact-term retrieval evaluation set.
10. Store structured query logs that support later metrics and debugging.
11. Log failure and fallback outcomes.

The sprint should produce two demoable flows:

* **Trusted publish/retrieval safety flow:** invalid metadata → quarantined/reviewed → excluded from retrieval → audit log created
* **Hybrid retrieval flow:** user query → vector candidates + lexical candidates → fused ranked result → filter policy applied → contribution logs recorded

---

## Sprint 3 Scope

### Slice 3 — Trusted KB Publish

1. **Story 4 - Build MVP metadata review workflow** — 8 pts
2. **Story 5 - Exclude quarantined metadata from retrieval** — 5 pts
3. **Story 6 - Log validation and publish audit events** — 3 pts

### Slice 4 — Deterministic Retrieval Core

4. **Story 1 - Build lexical retrieval index** — 8 pts
5. **Story 2 - Implement BM25-like lexical scoring** — 5 pts
6. **Story 3 - Fuse lexical and vector results with RRF** — 8 pts
7. **Story 4 - Apply filter policy to hybrid retrieval** — 5 pts
8. **Story 5 - Add hybrid retrieval contribution logging** — 3 pts
9. **Story 6 - Create exact-term retrieval evaluation set** — 3 pts

### Slice 6A — Observability & Trust

10. **Story 1 - Complete structured query log schema** — 8 pts
11. **Story 8 - Add failure and fallback outcome logging** — 3 pts

## Sprint 3 Total

**59 story points** **11 stories**

---

# Story Dependency Map

> Link these as blocking dependencies in Jira. Stories listed as blockers must be in a mergeable or agreed-upon state before the dependent story can be completed.

| Blocker | Blocked Story | Reason |
| --- | --- | --- |
| Slice 6A Story 1 (Person 5) | Slice 4 Story 5 (Person 5) | Contribution logging fields must be in schema before they can be written |
| Slice 6A Story 1 (Person 5) | Slice 6A Story 8 (Person 5) | Fallback reason columns must exist in schema before failure logging is wired |
| Slice 3 Story 6 (Person 5) | Slice 3 Story 4 (Person 1) | `publish_audit_log` table must exist before Person 1 can link review decisions to validation logs |
| Slice 4 Stories 1–2 (Person 3) | Slice 4 Story 5 (Person 5) | Lexical result shape must be finalized before contribution logging can write lexical fields |
| Slice 4 Story 3 (Person 4) | Slice 4 Story 5 (Person 5) | Fusion result shape must be finalized before contribution logging can write fusion fields |
| Slice 4 Story 1 (Person 3) | Slice 4 Story 3 (Person 4) | Fusion requires lexical top-k output as input |
| Sprint 2 validation statuses | Slice 3 Story 4 (Person 1) | Review workflow depends on quarantined/needs_review states being available |
| Sprint 2 validation statuses | Slice 3 Story 5 (Person 2) | Retrieval exclusion depends on validation status fields being present |

### Person 5 Internal Story Order

Person 5 has four stories with internal dependencies. They must be worked in this sequence:

1. **Slice 6A Story 1** — schema design first, shared as interface contract with Persons 3 and 4 on day 1–2
2. **Slice 3 Story 6** — publish audit table, fully independent, can run alongside Story 1
3. **Slice 6A Story 8** — fallback logging, staarts once schema columns exist
4. **Slice 4 Story 5** — contribution logging, starts once Person 3 and Person 4 have finalized their result shapes

---

# Person 1 — Metadata Review Workflow Owner

## Assigned Stories

1. **Slice 3 Story 4 - Build MVP metadata review workflow** — 8 pts

## Main Responsibility

Own the MVP workflow that allows operators or admins to review quarantined metadata and decide whether to approve, reject, or override it.

## Tasks

* Build or expose a review path for metadata items marked:

    * quarantined
    * needs_review
    * rejected
    * approved
    
* Allow reviewer actions:

    * approve
    * reject
    * override with reason
    
* Ensure every review decision updates validation state.
* Ensure review decisions are tied to:

    * reviewer identity
    * timestamp
    * reason code
    * notes if provided
    * KB version or publish attempt
    
* Coordinate with logging owner so review decisions are auditable.
* Add tests for approve, reject, and override transitions.

## Skills Needed

* Backend API development
* Admin/console workflow understanding
* SQLAlchemy / database state transitions
* Audit trail design
* Validation workflow logic
* Testing stateful workflows

## Dependencies

* Depends on Sprint 2 validation status and audit storage — **confirm Sprint 2 completion before starting**.
* **Blocked by Slice 3 Story 6 (Person 5)** — `publish_audit_log` table must exist before review decisions can be linked to validation logs.
* Needs coordination with Person 2 so approved/quarantined states are respected by retrieval.

---

# Person 2 — Retrieval Safety + Filter Enforcement Owner

## Assigned Stories

1. **Slice 3 Story 5 - Exclude quarantined metadata from retrieval** — 5 pts
2. **Slice 4 Story 4 - Apply filter policy to hybrid retrieval** — 5 pts

## Main Responsibility

Own the safety enforcement layer between validation/filtering metadata and retrieval results.

This person ensures hybrid retrieval never returns evidence that violates publish, validation, or filter rules.

## Tasks

### For Quarantined Metadata Exclusion

* Ensure quarantined metadata is ignored in resident-facing retrieval.
* Ensure rejected metadata is ignored in resident-facing retrieval.
* Ensure approved metadata remains usable.
* Log when metadata is ignored because of validation state.
* Confirm hard retrieval rules still run before validation/filter behavior.

### For Hybrid Filtering

* Apply filter policy to both:

    * lexical retrieval path
    * vector retrieval path
    
* Enforce:

    * hard system rules
    * UI-selected filters
    * inferred intent filters
    * validation status
    
* Log candidate counts before and after filtering.
* Add tests for:

    * disabled/unpublished exclusion
    * quarantined metadata exclusion
    * lexical path filtering
    * vector path filtering
    * hybrid fused result filtering
    

## Skills Needed

* Retrieval logic
* Backend filtering implementation
* Safety-critical edge case handling
* Understanding of taxonomy/filter policy
* Python testing
* Coordination across vector and lexical search

## Dependencies

* Depends on Sprint 1 filter policy and metadata fields.
* Depends on Sprint 2 validation statuses — **confirm Sprint 2 completion before starting**.
* Coordinates with Person 3 and Person 4 so lexical/vector results are filtered consistently.
* Coordinates with Person 5 on filter and validation logs — align on exclusion reason code format early.

---

# Person 3 — Lexical Retrieval Owner

## Assigned Stories

1. **Slice 4 Story 1 - Build lexical retrieval index** — 8 pts
2. **Slice 4 Story 2 - Implement BM25-like lexical scoring** — 5 pts

## Main Responsibility

Own the lexical retrieval path that improves exact-term matching for names, locations, procedures, and specific KB terms.

## Tasks

### Lexical Index

* Define indexed KB fields, minimum:

    * question/title
    * tags
    * answer/content if feasible
    
* Build a lexical index from approved/published KB rows.
* Make the index rebuildable from the KB.
* Ensure the index is version-aware or invalidated on KB publish.
* Add safe fallback if the lexical index is missing or stale.

### BM25-like Scoring

* Implement deterministic tokenization and normalization.
* Return top-k lexical candidates.
* Include:

    * evidence ID
    * lexical score
    * lexical rank
    
* Handle empty lexical results safely.
* Capture lexical retrieval latency.
* Add tests for exact-term query behavior.

## Skills Needed

* Search/retrieval implementation
* BM25 or lexical scoring concepts
* Python backend development
* Deterministic indexing/tokenization
* KB schema awareness
* Performance-aware implementation

## Dependencies

* Needs Person 2's filtering rules.
* Needs Person 4 for fusion integration.
* **Interface contract with Person 5** — lexical result object must expose: article IDs, BM25 scores, ranks, and latency for top-5 candidates. Align on this at sprint start.
* Depends on KB versioning/publish behavior.

---

# Person 4 — Hybrid Fusion + Evaluation Owner

## Assigned Stories

1. **Slice 4 Story 3 - Fuse lexical and vector results with RRF** — 8 pts
2. **Slice 4 Story 6 - Create exact-term retrieval evaluation set** — 3 pts

## Main Responsibility

Own the ranking combination layer and evaluation set for proving hybrid retrieval improves exact-term performance.

## Tasks

### Hybrid Fusion

* Take vector top-k results and lexical top-k results.
* Implement RRF or equivalent deterministic fusion.
* Define fusion parameters.
* Handle:

    * lexical-only candidates
    * vector-only candidates
    * overlapping candidates
    * empty lexical results
    * empty vector results
    
* Add deterministic tie-breaks.
* Ensure final fused result can be passed through filter policy.
* Add tests for fusion behavior.

### Exact-Term Evaluation

* Create a small exact-term evaluation set with:

    * proper nouns
    * locations
    * procedures
    * mixed semantic/exact queries
    
* Define expected top-1 or top-k evidence IDs where feasible.
* Compare vector-only vs hybrid retrieval.
* Report top-k accuracy and stability.

## Skills Needed

* Ranking/fusion algorithms
* Retrieval evaluation design
* Python testing
* Data fixtures/test dataset creation
* Ability to reason about deterministic scoring
* Familiarity with vector and lexical result formats

## Dependencies

* **Blocked by Slice 4 Story 1 (Person 3)** — fusion requires lexical top-k output as input.
* Depends on existing vector retrieval output.
* Needs Person 2's filtering integration.
* **Interface contract with Person 5** — fusion result object must expose: strategy used (e.g., `"rrf"`), fused top-5 IDs, scores, ranks, and tie-break decisions. Align on this at sprint start.

---

# Person 5 — Structured Logging + Audit Observability Owner

## Assigned Stories

1. **Slice 6A Story 1 - Complete structured query log schema** — 8 pts _(start here — day 1)_
2. **Slice 3 Story 6 - Log validation and publish audit events** — 3 pts _(start here — day 1–2, independent)_
3. **Slice 6A Story 8 - Add failure and fallback outcome logging** — 3 pts _(after schema columns exist)_
4. **Slice 4 Story 5 - Add hybrid retrieval contribution logging** — 3 pts _(after Person 3 and 4 finalize result shapes)_

> Stories are listed in the order they should be worked. Do not treat them as a single block.

## Main Responsibility

Own observability for validation, publish, hybrid retrieval, and pipeline failures.

This person ensures Sprint 3 behavior can be inspected, debugged, and used later for metrics.

## Tasks

### Slice 6A Story 1 — Structured Query Log Schema (Day 1–2)

* Design new columns to add to `query_logs` (all nullable, additive, safe for existing rows):

    * `intent_label`, `intent_confidence`
    * `clarification_categories_offered`, `clarification_node_id_selected`
    * `lexical_top_k_ids`, `lexical_top_k_scores`, `lexical_top_k_ranks`, `lexical_latency_ms`
    * `vector_top_k_ids`, `vector_top_k_scores`, `vector_top_k_ranks`
    * `fusion_strategy`, `fusion_top_k_ids`, `fusion_top_k_scores`, `fusion_top_k_ranks`
    * `fallback_reason`, `failed_stage`
    
* Write idempotent migration in `hub/db/migrate_schema.py`.
* Share interface contracts with Person 3 and Person 4 at sprint start:

    * Person 3: lexical result must expose IDs, BM25 scores, ranks (top-5), latency
    * Person 4: fusion result must expose strategy, fused IDs, scores, ranks (top-5), tie-break decisions
    

### Slice 3 Story 6 — Validation / Publish Audit Logs (Day 1–2, independent)

* Create new `publish_audit_log` table:

    * `id`, `attempted_at` (Unix timestamp)
    * `gate_policy` — strict / warn_only / off
    * `validation_status` — pass / warning / blocked
    * `kb_version_before`, `kb_version_after` (null if blocked)
    * `total_items`, `approved_count`, `quarantined_count`, `needs_review_count`, `failed_rules_count`
    * `failure_reasons` (TEXT, JSON array)
    * `triggered_by` (nullable, user identity)
    
* Wire `publish_kb` to write a row on every publish attempt.
* Ensure Person 1 can reference this table when linking review decisions to publish attempts.

### Slice 6A Story 8 — Failure and Fallback Outcome Logging

* Log pipeline failure status.
* Log fallback reason codes via `fallback_reason` column:

    * `no_results`, `low_confidence`, `validation_blocked`, `retrieval_error`, `rewrite_error`
    
* Log which stage failed via `failed_stage` column.
* Preserve partial logs when failure happens mid-pipeline.

### Slice 4 Story 5 — Hybrid Retrieval Contribution Logging

* Log lexical top-k IDs, scores, and ranks (up to top-5).
* Log vector top-k IDs, scores, and ranks (up to top-5).
* Log fusion strategy and parameters.
* Log fused top-k IDs, scores, and ranks (up to top-5).
* Log tie-break decisions when applicable.
* All stored as JSON text in `query_logs` columns defined in Story 1.

## Skills Needed

* Backend logging / observability
* SQLAlchemy / structured log schema design
* Python error handling
* Metrics-oriented data modeling
* Retrieval debugging
* Audit trail design

## Dependencies

* Needs Person 1's review workflow events to link to `publish_audit_log`.
* Needs Person 2's filtering/exclusion reason codes — align on format at sprint start.
* Needs Person 3's lexical result format — defined by interface contract at sprint start.
* Needs Person 4's fusion result format — defined by interface contract at sprint start.
* Builds on Sprint 1 logging skeleton and Sprint 2 validation audit storage.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
| --- | --- | --- | --- |
| Person 1 | Metadata review workflow | Slice 3 Story 4 | 8 |
| Person 2 | Retrieval safety + hybrid filter enforcement | Slice 3 Story 5, Slice 4 Story 4 | 10 |
| Person 3 | Lexical retrieval index + BM25 scoring | Slice 4 Stories 1–2 | 13 |
| Person 4 | Hybrid fusion + exact-term evaluation | Slice 4 Stories 3 and 6 | 11 |
| Person 5 | Structured logging + audit observability | Slice 6A Story 1, Slice 3 Story 6, Slice 6A Story 8, Slice 4 Story 5 | 17 |

Person 5 has the highest point load. The risk is managed by front-loading the schema design (Slice 6A Story 1) and publish audit table (Slice 3 Story 6) in days 1–2, then working contribution and fallback logging in week 2 as Persons 3 and 4 finalize their result shapes. If needed, Person 1 can support validation audit logging after the review workflow is stable.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Validation / Publish Team: Persons 1, 2, and 5

Agree on:

```
What metadata states exist?
What does review change?
How does retrieval know metadata is quarantined?
What gets logged during validation, review, and publish?
What does the publish_audit_log table look like?
```

### Retrieval Team: Persons 2, 3, 4, and 5

Agree on:

```
What does a lexical result object look like? (Person 3 → Person 5 contract)
What does a vector result object look like?
Where are filters applied?
What does the fused result object look like? (Person 4 → Person 5 contract)
What contribution metadata must be logged?
```

---

# Mid-Sprint Integration Check

Run these flows together:

## Trusted Publish / Retrieval Safety Flow

```
metadata validation result
→ item marked quarantined/needs_review
→ reviewer approves/rejects/overrides
→ validation state updates
→ resident retrieval excludes quarantined/rejected metadata
→ validation and exclusion logs are created
```

## Hybrid Retrieval Flow

```
resident query
→ vector retrieval
→ lexical retrieval
→ filter policy applied
→ RRF/fusion combines candidates
→ final ranked evidence returned
→ lexical/vector/fusion contributions are logged
```

## Failure / Fallback Flow

```
query or retrieval error
→ fallback path triggered
→ failure reason code recorded
→ partial pipeline log preserved
```

---

# End-of-Sprint Demo Checklist

By the Sprint 3 review, the team should be able to demo:

1. Quarantined metadata appears in the review workflow.
2. A reviewer can approve, reject, or override a quarantined item.
3. Quarantined/rejected metadata is excluded from resident retrieval.
4. Validation and publish audit events are logged.
5. A query returns lexical candidates.
6. A query returns vector candidates.
7. Lexical and vector candidates are fused deterministically.
8. Hybrid retrieval obeys filter policy.
9. Logs show lexical, vector, and fusion contribution details.
10. Exact-term evaluation compares vector-only vs hybrid retrieval.
11. Failure or fallback outcomes are logged with reason codes.

---

# Practical Scope Warning

Do not overbuild the review workflow into a full moderation platform. Sprint 3 only needs the MVP review path required to approve, reject, or override metadata with an audit trail.

Do not over-tune retrieval ranking in Sprint 3. The feedback-adjusted ranking tuning story remains stretch. The required work is lexical retrieval, BM25-like scoring, RRF fusion, filtering, logging, and a small evaluation set.

‌
