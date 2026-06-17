---
title: Sprint 1
confluence_id: 6160395
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM/pages/6160395
parent: 8-Week Sprint Plan
last_updated: 2026-05-03T06:41:43.586Z
version: 1
---

# Sprint 1

### **Sprint Goal**

Build the deterministic hub pipeline foundation and establish the core metadata structure required for controlled query processing and KB integrity.

---

### **By the end of Sprint 1, ResKiosk should be able to:**

* Accept and process a resident query through a structured pipeline.
* Perform deterministic query rewrite based on predefined rules.
* Execute retrieval against a taxonomy-aware knowledge base.
* Return a structured, traceable response to the kiosk.
* Maintain a consistent taxonomy structure for classification and filtering.
* Store and associate metadata with KB entries.
* Log query execution steps for traceability.
* Support basic pipeline observability for debugging and validation.

---

### **The sprint should produce two demoable flows:**

#### **1. Core Query Pipeline Flow**

```
resident query 
→ pipeline entry 
→ deterministic rewrite 
→ taxonomy-aware retrieval 
→ structured response 
→ logged execution trace
```

#### **2. Metadata-Backed Retrieval Flow**

```
KB entry with metadata 
→ taxonomy classification applied 
→ query retrieval respects taxonomy 
→ relevant results returned 
→ metadata-linked response trace
```

---

## **Sprint 1 Scope**

### **Slice 1 — Core Query Pipeline**

* Implement pipeline orchestration (entry → rewrite → retrieval → response) — 8 pts
* Implement deterministic query rewrite rules — 8 pts
* Implement taxonomy-aware retrieval layer — 8 pts
* Return structured response format to kiosk — 5 pts

---

### **Slice 2 — Taxonomy & Metadata Foundation**

* Define and implement taxonomy structure — 5 pts
* Add metadata schema to KB entries — 5 pts
* Link taxonomy to KB entries — 5 pts

---

### **Slice 3 — Logging & Observability**

* Implement query logging skeleton — 5 pts
* Log pipeline stages and outputs — 4 pts

---

## **Sprint 1 Total**

**53 story points — 9 stories**

---

# **Team Task Grouping & Ownership**

---

## **Person 1 — Pipeline Orchestration Owner**

### **Assigned Stories**

* Slice 1 Story 1 — Implement pipeline orchestration — 8 pts

### **Main Responsibility**

Own the end-to-end execution flow of the hub pipeline, ensuring deterministic progression from query input to response output.

### **Tasks**

* Define pipeline stages:

    * query intake
    * rewrite
    * retrieval
    * response assembly
    
* Ensure strict execution order.
* Enforce deterministic behavior for identical inputs.
* Provide hooks for future pipeline interruption (for clarification in Sprint 2).
* Integrate with rewrite and retrieval components.
* Add integration tests for:

    * full pipeline execution
    * failure handling
    * deterministic outputs
    

### **Skills Needed**

* Python / FastAPI
* Backend architecture
* Pipeline orchestration
* Integration testing

### **Dependencies**

* Coordinates with Person 2 (rewrite logic).
* Coordinates with Person 3 (retrieval layer).
* Provides pipeline hooks for Person 5 logging.

---

## **Person 2 — Query Rewrite Owner**

### **Assigned Stories**

* Slice 1 Story 2 — Implement deterministic query rewrite — 8 pts

### **Main Responsibility**

Own deterministic transformation of raw user queries into structured, retrieval-ready queries.

### **Tasks**

* Define rewrite rules:

    * normalization
    * synonym handling
    * phrase standardization
    
* Ensure rewrite output is consistent for identical inputs.
* Avoid probabilistic or LLM-based variation.
* Provide structured output format for retrieval.
* Add unit tests for:

    * rewrite correctness
    * edge cases
    * stability across repeated runs
    

### **Skills Needed**

* Python
* Text processing
* Rule-based systems
* Testing

### **Dependencies**

* Feeds output into Person 3 retrieval system.
* Integrated into Person 1 pipeline.

---

## **Person 3 — Retrieval & Taxonomy Integration Owner**

### **Assigned Stories**

* Slice 1 Story 3 — Implement taxonomy-aware retrieval — 8 pts
* Slice 2 Story 3 — Link taxonomy to KB entries — 5 pts

### **Main Responsibility**

Own retrieval logic and ensure results are filtered and ranked using taxonomy and metadata.

### **Tasks**

* Implement retrieval mechanism over KB.
* Apply taxonomy filtering during retrieval.
* Ensure retrieval respects metadata constraints.
* Define mapping between query structure and taxonomy nodes.
* Validate retrieval relevance.
* Add tests for:

    * correct taxonomy filtering
    * retrieval accuracy
    * edge cases with missing taxonomy
    

### **Skills Needed**

* Backend search/retrieval systems
* Data modeling
* Taxonomy integration

### **Dependencies**

* Depends on Person 4 taxonomy definition.
* Uses Person 2 rewritten query output.
* Integrated into Person 1 pipeline.

---

## **Person 4 — Taxonomy & Metadata Schema Owner**

### **Assigned Stories**

* Slice 2 Story 1 — Define taxonomy structure — 5 pts
* Slice 2 Story 2 — Add metadata schema to KB entries — 5 pts

### **Main Responsibility**

Own the structure and consistency of taxonomy and metadata used across the system.

### **Tasks**

* Define taxonomy hierarchy:

    * categories
    * subcategories
    * relationships
    
* Ensure taxonomy is stable and versionable.
* Define metadata schema fields:

    * taxonomy assignment
    * source/authority
    * scope/context
    * labels/captions
    
* Ensure schema supports validation in future sprints.
* Document schema clearly for backend use.

### **Skills Needed**

* Data modeling
* Schema design
* Information architecture

### **Dependencies**

* Provides taxonomy to Person 3 retrieval.
* Provides metadata schema to Person 5 logging.

---

## **Person 5 — Logging & Response Structure Owner**

### **Assigned Stories**

* Slice 1 Story 4 — Return structured response format — 5 pts
* Slice 3 Story 1 — Implement query logging skeleton — 5 pts
* Slice 3 Story 2 — Log pipeline stages and outputs — 4 pts

### **Main Responsibility**

Own observability, structured outputs, and traceability of all pipeline activity.

### **Tasks**

* Define response format:

    * answer
    * metadata references
    * trace identifiers
    
* Implement query log structure.
* Log:

    * input query
    * rewritten query
    * retrieval results
    * final response
    
* Ensure logs are linked via request/session IDs.
* Ensure logs are bounded and safe.
* Add tests for:

    * log completeness
    * traceability
    * consistency
    

### **Skills Needed**

* SQLAlchemy / SQLite
* Backend logging systems
* Data modeling
* API response design

### **Dependencies**

* Receives pipeline data from Person 1.
* Receives rewrite output from Person 2.
* Receives retrieval output from Person 3.

---

# **Ownership Map**

| Person | Ownership Area | Main Stories | Points |
| --- | --- | --- | --- |
| Person 1 | Pipeline orchestration | Slice 1 Story 1 | 8 |
| Person 2 | Query rewrite | Slice 1 Story 2 | 8 |
| Person 3 | Retrieval + taxonomy integration | Slice 1 Story 3 + Slice 2 Story 3 | 13 |
| Person 4 | Taxonomy + metadata schema | Slice 2 Stories 1–2 | 10 |
| Person 5 | Logging + response structure | Slice 1 Story 4 + Slice 3 Stories 1–2 | 14 |

---

# **Recommended Collaboration Flow**

---

## **Start-of-Sprint Alignment**

### **Pipeline Team (Persons 1–3, 5)**

Agree on:

* Pipeline stage boundaries
* Rewrite output format
* Retrieval input/output format
* Response structure
* Logging schema

### **Metadata Team (Persons 3–5)**

Agree on:

* Taxonomy structure
* Metadata schema
* How metadata affects retrieval
* How metadata appears in logs

---

## **Mid-Sprint Integration Check**

### **Run Core Flow**

```
query 
→ rewrite 
→ retrieval 
→ response 
→ logs recorded
```

Verify:

* Deterministic outputs
* Correct taxonomy filtering
* Complete logging trace

---

## **End-of-Sprint Demo Checklist**

* Query flows through full pipeline without failure
* Rewrite produces consistent output
* Retrieval respects taxonomy
* Response is structured and traceable
* Logs show full pipeline execution
* Metadata is attached to KB entries and used in retrieval

---

# **Practical Scope Warning**

* Do not introduce clarification logic yet; pipeline must remain linear in Sprint 1.
* Do not introduce probabilistic or LLM-driven rewrite behavior.
* Do not over-engineer taxonomy; keep it minimal but structured.
* Do not build full analytics; logging is for traceability only.
