---
title: Sprint 2
confluence_id: 6193199
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM/pages/6193199
parent: 8-Week Sprint Plan
last_updated: 2026-05-03T06:37:05.350Z
version: 3
---

# Sprint 2

# Sprint Goal

Build the clarify-first interaction layer and establish the first enforceable metadata validation path.

By the end of Sprint 2, ResKiosk should be able to:

1. Detect when a resident query is ambiguous or low-confidence.
2. Pause the hub pipeline before rewrite/retrieval when clarification is needed.
3. Return taxonomy-backed clarification chips to the kiosk.
4. Allow the kiosk to send back a selected clarification option.
5. Resume the pipeline deterministically using the selected option.
6. Persist and log the clarification lifecycle.
7. Validate KB metadata using deterministic rules.
8. Store validation status and audit records.
9. Gate KB publish based on validation results.

The sprint should produce two demoable flows:

* **Clarification flow:** ambiguous query → clarification chips → selected chip → resumed query flow → persisted/logged resolution
* **Validation flow:** KB metadata validation → validation status stored → publish passes/blocks/warns → audit trail created

---

# Sprint 2 Scope:

### Slice 2 — Clarify-first UX

1. **Implement clarification trigger policy** — 5 pts
2. **Return taxonomy-backed clarification chips** — 5 pts
3. **Add kiosk clarification chip UI** — 5 pts
4. **Implement clarification retry contract** — 8 pts
5. **Persist clarification resolution** — 3 pts
6. **Log clarification lifecycle events** — 3 pts

### Slice 3 — Trusted KB Publish

7. **Implement metadata validation rule engine** — 8 pts
8. **Add validation status and audit storage** — 8 pts
9. **Gate KB publish using validation results** — 8 pts

## Sprint 2 Total

**53 story points** **9 stories**

---

# Person 1 — Clarification Trigger + Pipeline Gate Owner

## Assigned Stories

1. **Slice 2 Story 1 - Implement clarification trigger policy** — 5 pts
2. Support clarification pipeline integration for Story 4, but not primary owner

## Main Responsibility

Own the backend decision logic for when the hub should pause and ask for clarification before rewrite or retrieval.

## Tasks

* Define clarification trigger conditions:

    * low intent confidence
    * unclear intent
    * low retrieval confidence
    * missing required scope
    
* Represent trigger reasons as stable reason codes.
* Make trigger behavior deterministic for the same query/config.
* Plug trigger logic into the canonical pipeline.
* Ensure the pipeline stops when clarification is required.
* Add tests for:

    * low-confidence trigger
    * unclear-intent trigger
    * missing-scope trigger
    * non-trigger normal query flow
    

## Skills Needed

* Python / FastAPI
* Backend pipeline logic
* Intent classification flow
* Retrieval confidence handling
* Unit/integration testing
* Safety-aware decision logic

## Dependencies

* Depends on Sprint 1 pipeline orchestration.
* Coordinates with Person 2 on the retry contract and clarification response shape.
* Coordinates with Person 5 for trigger logging.

---

# Person 2 — Clarification Contract Owner

## Assigned Stories

1. **Slice 2 Story 2 - Return taxonomy-backed clarification chips** — 5 pts
2. **Slice 2 Story 4 - Implement clarification retry contract** — 8 pts

## Main Responsibility

Own the full hub-side clarification contract: the clarification payload, chip IDs, retry request shape, selected option validation, and deterministic resume behavior.

This person is the best fit for Story 4 because they control the contract between:

```
clarification response → selected chip → resumed query flow
```

## Tasks

### For Story 2

* Define the clarification response format.
* Return 2–3 chip options.
* Ensure each chip has:

    * stable ID
    * display label
    * taxonomy node mapping
    
* Ensure chip ordering is deterministic.
* Mark the response as paused pending clarification.

### For Story 4

* Define the retry request format.
* Accept selected clarification option ID.
* Accept original session/request context.
* Validate selected option ID.
* Resolve selected option to taxonomy node or intent constraint.
* Resume the pipeline after clarification selection.
* Ensure rewrite and retrieval only occur after clarification is resolved.
* Return safe fallback/error for invalid or expired clarification context.
* Add API tests for valid and invalid retry flows.

## Skills Needed

* FastAPI / Pydantic
* API contract design
* Backend request/response modeling
* Taxonomy/filtering awareness
* Pipeline state continuation
* Error handling
* Integration testing

## Dependencies

* Depends on Sprint 1 taxonomy and pipeline work.
* Needs Person 1’s clarification trigger reason/context.
* Needs Person 3 to consume the retry contract from the kiosk.
* Needs Person 5 to persist and log selected options.

---

# Person 3 — Kiosk Clarification UI Owner

## Assigned Stories

1. **Slice 2 Story 3 - Add kiosk clarification chip UI** — 5 pts

## Main Responsibility

Own the resident-facing kiosk UI for clarification prompts and chip selection.

## Tasks

* Display clarification prompt returned by the hub.
* Render 2–3 tap-friendly chip options.
* Submit selected option ID using the retry contract owned by Person 2.
* Prevent final answer display until clarification is resolved.
* Handle fallback option such as “Say that differently” if provided.
* Handle invalid/expired clarification context gracefully.
* Verify normal non-clarification responses still render correctly.

## Skills Needed

* Kotlin
* Jetpack Compose
* Android state management
* API integration
* Kiosk UI/UX
* Error/fallback handling

## Dependencies

* Depends on Person 2’s clarification response and retry contract.
* Coordinates with Person 5 if kiosk-side event identifiers need to match persisted/logged values.
* Tests against Person 1’s trigger scenarios.

---

# Person 4 — Metadata Validation + Publish Gate Owner

## Assigned Stories

1. **Slice 3 Story 1 - Implement metadata validation rule engine** — 8 pts
2. **Slice 3 Story 3 - Gate KB publish using validation results** — 8 pts

## Main Responsibility

Own the validation logic and enforce validation during KB publish.

## Tasks

### Validation Rule Engine

* Implement deterministic validation rule framework.
* Validate:

    * taxonomy assignment
    * authority/source
    * scope/context
    * caption/label quality where applicable
    
* Return stable:

    * rule ID
    * severity
    * pass/fail status
    * message
    
* Ensure validation can run without online services.

### Publish Gate

* Run validation before KB publish completes.
* Return publish result:

    * pass
    * blocked
    * warning
    
* Include summary counts and failure reasons.
* Ensure validation failure does not corrupt the existing published KB.
* Ensure quarantined/failed metadata does not move into resident-facing publish state.

## Skills Needed

* Python backend
* Rule-engine design
* KB publish flow
* Safety-oriented validation logic
* Deterministic test design
* API/error response handling

## Dependencies

* Depends on Sprint 1 taxonomy and metadata fields.
* Needs Person 5’s validation status/audit storage.
* Coordinates with future retrieval filtering behavior to ensure invalid metadata does not affect resident retrieval.

---

# Person 5 — Persistence, Audit, and Lifecycle Logging Owner

## Assigned Stories

1. **Slice 2 Story 5 - Persist clarification resolution** — 3 pts
2. **Slice 2 Story 6 - Log clarification lifecycle events** — 3 pts
3. **Slice 3 Story 2 - Add validation status and audit storage** — 8 pts

## Main Responsibility

Own data persistence and auditability for clarification and metadata validation.

## Tasks

### Clarification Persistence

* Store selected clarification option ID.
* Store selected label or recoverable label.
* Store session ID.
* Store resolved intent or taxonomy node.
* Store language where available.
* Link clarification resolution to the related query log record.

### Clarification Lifecycle Logging

* Log whether clarification was triggered.
* Log trigger reason codes.
* Log option IDs and labels shown.
* Log selected option ID and label.
* Log downstream resolved taxonomy/intent.
* Log that rewrite/retrieval did not occur before clarification resolution.

### Validation Status and Audit Storage

* Add validation states:

    * approved
    * quarantined
    * needs_review
    * rejected
    
* Store rule results:

    * rule ID
    * severity
    * message
    * timestamp
    
* Store review/publish attempt linkage.
* Ensure audit records can be tied back to KB version or publish attempt.

## Skills Needed

* SQLAlchemy / SQLite
* Database migrations
* Backend logging
* Audit trail design
* Data modeling
* Query log linkage
* Careful handling of bounded log payloads

## Dependencies

* Needs Person 2’s clarification option IDs and retry shape.
* Needs Person 1’s trigger reason codes.
* Needs Person 4’s validation rule result format.
* Depends on Sprint 1 logging skeleton and metadata schema.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
| --- | --- | --- | --- |
| Person 1 | Clarification trigger + pipeline gate | Slice 2 Story 1 | 5 |
| Person 2 | Clarification API/chip/retry contract | Slice 2 Stories 2 and 4 | 13 |
| Person 3 | Kiosk clarification UI | Slice 2 Story 3 | 5 |
| Person 4 | Validation engine + publish gate | Slice 3 Stories 1 and 3 | 16 |
| Person 5 | Persistence, audit, lifecycle logging | Slice 2 Stories 5–6 + Slice 3 Story 2 | 14 |

This is not perfectly equal by points, but it is cleaner by ownership. Person 2 owns the full clarification contract instead of splitting Story 4 across multiple people.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Clarification Team: Persons 1–3 and 5

Agree on:

```
What triggers clarification?
What does the hub return?
What does the kiosk send back?
What gets persisted?
What gets logged?
What context is needed to resume the pipeline?
```

### Validation Team: Persons 4–5

Agree on:

```
What does each validation rule return?
Where are validation results stored?
What states can metadata be in?
How does publish decide pass, block, or warn?
What audit trail is required?
```

---

# Mid-Sprint Integration Check

Run these flows together:

## Clarification flow

```
ambiguous query
→ trigger policy fires
→ hub returns taxonomy-backed chips
→ kiosk displays chips
→ kiosk submits selected option
→ hub validates selected option
→ hub resumes pipeline
→ clarification resolution is persisted
→ lifecycle logs show the full flow
```

## Validation flow

```
KB metadata snapshot
→ validation rules run
→ validation results stored
→ publish gate checks results
→ publish passes/blocks/warns
→ audit records are persisted
```

---

# End-of-Sprint Demo Checklist

By the Sprint 2 review, the team should be able to demo:

1. Ambiguous query triggers clarification.
2. Kiosk displays 2–3 clarification chips.
3. Selecting a chip resumes the query flow.
4. Invalid chip selection fails safely.
5. Clarification resolution is persisted.
6. Clarification lifecycle is logged.
7. Invalid metadata fails validation.
8. Publish is blocked or warned based on validation results.
9. Validation decision is auditable.

---

# Practical Scope Warning

Do not turn clarification into a general chatbot or full multi-turn conversation system. Sprint 2 only needs a bounded clarification loop.

Do not turn validation into a full moderation platform. Sprint 2 only needs deterministic validation rules, validation status storage, and a publish gate.
