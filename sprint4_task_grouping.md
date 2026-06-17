# Sprint 4 — 5-Person Task Grouping

## Sprint 4 Scope

### Slice 5 — Compound Correctness

1. **Story 1 - Detect compound queries using top-2 intents** — 5 pts
2. **Story 2 - Build intent-scoped retrieval path queries** — 5 pts
3. **Story 3 - Run retrieval separately per compound path** — 8 pts
4. **Story 4 - Merge compound path results deterministically** — 8 pts
5. **Story 5 - Add evidence attribution for compound results** — 5 pts
6. **Story 6 - Support primary and secondary compound response outputs** — 5 pts
7. **Story 7 - Log compound lifecycle and merge decisions** — 3 pts
8. **Story 8 - Create compound retrieval evaluation scenarios** — 3 pts

### Slice 6A — Observability & Trust

9. **Story 2 - Add latency breakdown logging** — 5 pts
10. **Story 3 - Capture final evidence list and stability fields** — 5 pts
11. **Story 4 - Implement MVP metrics export workflow** — 5 pts
12. **Story 5 - Create grounding proxy review fields** — 3 pts
13. **Story 9 - Format hub query logs for readable operational observability** — 3 pts

## Sprint 4 Total

**63 story points**  
**13 stories**

---

# Sprint Goal

Implement compound query handling and complete the main observability foundation before multimodal work accelerates.

By the end of Sprint 4, ResKiosk should be able to:

1. Detect compound or multi-intent resident queries.
2. Build intent-scoped retrieval paths for compound questions.
3. Run retrieval separately per path.
4. Merge path results deterministically.
5. Attribute returned evidence to the path/intent that produced it.
6. Return primary and secondary guidance for compound answers.
7. Log compound lifecycle and merge decisions.
8. Capture latency breakdowns.
9. Capture final evidence IDs, scores, ranks, and stability fields.
10. Export MVP metrics.
11. Support grounding proxy review fields.
12. Produce readable hub logs for operational observability.

The sprint should produce two demoable flows:

- **Compound retrieval flow:** compound query → top-2 intents → per-path retrieval → deterministic merge → primary/secondary evidence
- **Observability flow:** query execution → latency/evidence/fallback fields logged → metrics/export viewable → readable hub log stream

---

# Person 1 — Compound Intent Detection + Path Query Owner

## Assigned Stories

1. **Slice 5 Story 1 - Detect compound queries using top-2 intents** — 5 pts
2. **Slice 5 Story 2 - Build intent-scoped retrieval path queries** — 5 pts

## Main Responsibility

Own the front of the compound query flow: detecting when a query needs multiple retrieval paths and creating the path-level query inputs.

## Tasks

- Expose top-2 intent candidates with confidence scores.
- Define the threshold for compound query detection.
- Set a compound query flag when both top intents meet the configured threshold.
- Preserve normal single-path behavior when a query is not compound.
- Create one retrieval path per detected intent.
- Carry the normalized query into each path.
- Add intent-specific constraints or enrichment where appropriate.
- Respect clarification selections when present.
- Respect hard rules and filter policy.
- Log detected intents, confidence scores, thresholds, path queries, and associated intents.

## Skills Needed

- Python backend development
- Intent classification flow
- Query normalization/pipeline understanding
- Retrieval input design
- Deterministic rule implementation
- Test writing for edge cases

## Dependencies

- Depends on Sprint 1 pipeline and filtering.
- Depends on Sprint 2 clarification resolution behavior.
- Coordinates with Person 2 so path queries match expected retrieval inputs.
- Coordinates with Person 5 so compound detection and path construction are logged consistently.

---

# Person 2 — Per-Path Retrieval Owner

## Assigned Stories

1. **Slice 5 Story 3 - Run retrieval separately per compound path** — 8 pts

## Main Responsibility

Own execution of retrieval for each compound query path.

## Tasks

- Execute retrieval independently for each path query.
- Use hybrid retrieval per path when available.
- Apply filters consistently per path.
- Return per-path top-k evidence IDs, scores, ranks, and candidate counts.
- Handle zero-result paths safely without failing the whole request.
- Track retrieval latency per path.
- Add integration tests for both-path success, one-path-empty, and filter-removed candidates.

## Skills Needed

- Retrieval engine implementation
- Python backend
- Hybrid retrieval integration
- Filtering policy awareness
- Performance/latency instrumentation
- Integration testing

## Dependencies

- Depends on Person 1’s path query shape.
- Depends on Sprint 3 hybrid retrieval implementation.
- Coordinates with Person 3 for merge input structure.
- Coordinates with Person 5 for path-level logging.

---

# Person 3 — Deterministic Merge + Primary/Secondary Output Owner

## Assigned Stories

1. **Slice 5 Story 4 - Merge compound path results deterministically** — 8 pts
2. **Slice 5 Story 6 - Support primary and secondary compound response outputs** — 5 pts

## Main Responsibility

Own the merge strategy and final response structure for compound answers.

## Tasks

- Define and implement merge strategy.
- Apply priority rules, including safety/medical priority where appropriate.
- Deduplicate evidence across paths deterministically.
- Use stable tie-break rules.
- Handle both-path-success, one-path-empty, duplicate evidence, and near-tie cases.
- Represent primary evidence/guidance in the response payload.
- Represent secondary evidence/guidance separately.
- Ensure urgent/safety/medical content is not buried.
- Preserve existing single-intent response behavior.
- Add tests for primary/secondary response behavior.

## Skills Needed

- Ranking/merge algorithm design
- Backend response modeling
- Safety-critical prioritization
- Deterministic tie-break logic
- API payload design
- Test writing

## Dependencies

- Depends on Person 2’s per-path retrieval outputs.
- Coordinates with Person 4 for evidence attribution.
- Coordinates with Person 5 for merge decision logging.

---

# Person 4 — Evidence Attribution + Evaluation Owner

## Assigned Stories

1. **Slice 5 Story 5 - Add evidence attribution for compound results** — 5 pts
2. **Slice 5 Story 8 - Create compound retrieval evaluation scenarios** — 3 pts

## Main Responsibility

Own auditability and evaluation for compound results.

## Tasks

- Attach producing path/intent to each returned evidence item.
- Capture path rank, path score, merged rank, and merged score.
- Preserve information when evidence appears in multiple paths.
- Ensure final response generation can identify primary and secondary evidence.
- Keep attribution bounded to configured top-k size.
- Create 3–5 compound scenarios.
- Include medical + location, safety + shelter ops, and basic needs + schedule examples.
- Define expected primary and secondary evidence.
- Compare single-path vs multi-path behavior.
- Confirm deterministic final ranking for a fixed KB version/config.

## Skills Needed

- Retrieval evaluation design
- Test fixture creation
- Evidence/ranking data modeling
- Python testing
- Auditability mindset
- Understanding of compound user scenarios

## Dependencies

- Depends on Person 2’s path retrieval outputs.
- Depends on Person 3’s merge result format.
- Coordinates with Person 5 to ensure attribution appears in logs/metrics.

---

# Person 5 — Metrics, Logging, and Operational Observability Owner

## Assigned Stories

1. **Slice 5 Story 7 - Log compound lifecycle and merge decisions** — 3 pts
2. **Slice 6A Story 2 - Add latency breakdown logging** — 5 pts
3. **Slice 6A Story 3 - Capture final evidence list and stability fields** — 5 pts
4. **Slice 6A Story 4 - Implement MVP metrics export workflow** — 5 pts
5. **Slice 6A Story 5 - Create grounding proxy review fields** — 3 pts
6. **Slice 6A Story 9 - Format hub query logs for readable operational observability** — 3 pts

## Main Responsibility

Own Sprint 4 observability, metrics, and readable hub logs.

## Tasks

- Log compound trigger, top-2 intents, path queries, per-path evidence, merge strategy, dedupe behavior, and final ordering.
- Add overall and retrieval latency breakdowns.
- Capture final evidence IDs, ranks, scores, modality, and path attribution.
- Implement basic metrics export/query workflow.
- Add grounding proxy review fields: evidence links, manual supported/unsupported labels, and reviewer notes.
- Format live hub logs with stable IDs, clear stage labels, clear outcomes, and bounded payloads.

## Skills Needed

- Backend logging/observability
- Metrics/reporting workflow design
- SQLAlchemy / schema updates
- Python error handling
- Retrieval debugging
- Data export/query design

## Dependencies

- Needs Person 1’s compound detection fields.
- Needs Person 2’s per-path retrieval fields.
- Needs Person 3’s merge metadata.
- Needs Person 4’s evidence attribution format.
- Builds on Sprint 3 structured query logs.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
|---|---|---:|---:|
| Person 1 | Compound detection + path query construction | Slice 5 Stories 1–2 | 10 |
| Person 2 | Per-path retrieval execution | Slice 5 Story 3 | 8 |
| Person 3 | Deterministic merge + primary/secondary outputs | Slice 5 Stories 4 and 6 | 13 |
| Person 4 | Evidence attribution + compound evaluation | Slice 5 Stories 5 and 8 | 8 |
| Person 5 | Metrics, logging, and observability | Slice 5 Story 7 + Slice 6A Stories 2–5 and 9 | 24 |

Person 5 has the largest point load because observability spans the whole sprint. If capacity becomes tight, Person 4 should help with metrics export or grounding proxy fields after the evaluation scenarios are stable.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Compound Retrieval Team: Persons 1–4

Agree on:

```text
What makes a query compound?
What does a path query look like?
What does each path return?
How is evidence merged?
How are primary and secondary outputs represented?
```

### Observability Team: Persons 3–5

Agree on:

```text
What fields must be logged for compound handling?
What latency fields are required?
What final evidence stability fields are required?
What should be readable in the hub/log stream?
```

---

# Mid-Sprint Integration Check

Run these flows together:

## Compound Query Flow

```text
compound query
→ top-2 intents detected
→ path queries created
→ retrieval runs per path
→ evidence attributed to path/intent
→ deterministic merge
→ primary/secondary response returned
```

## Metrics / Observability Flow

```text
query runs through pipeline
→ latency fields captured
→ final evidence IDs/scores/ranks stored
→ compound lifecycle logged
→ hub log stream clearly shows major events
→ metrics export produces usable output
```

---

# End-of-Sprint Demo Checklist

By the Sprint 4 review, the team should be able to demo:

1. A compound query is detected using top-2 intents.
2. Separate retrieval paths are built.
3. Each path returns evidence independently.
4. Path results are merged deterministically.
5. Final output separates primary and secondary guidance.
6. Evidence includes producing path/intent attribution.
7. Logs show compound lifecycle and merge decisions.
8. Latency breakdowns are recorded.
9. Final evidence IDs/scores/ranks are stored.
10. Metrics can be exported or queried.
11. Hub logs are readable during the demo flow.

---

# Practical Scope Warning

Do not turn compound handling into a full planner or agent. Sprint 4 only needs deterministic top-2 intent pathing and deterministic merge behavior.

Do not overbuild the metrics layer into a full analytics dashboard. Sprint 4 only needs MVP export/query capability and enough structured fields to support later evaluation.
