# Sprint 8 — 5-Person Task Grouping

## Sprint 8 Scope

Sprint 8 contains **no planned feature development**. Work should be represented in Jira as **Tasks**, **Bugs**, or **Test Tasks**, not feature stories.

### End-to-End Testing

1. **Run full text-query E2E test**
2. **Run clarification E2E test**
3. **Run hybrid retrieval E2E test**
4. **Run compound query E2E test**
5. **Run multimodal E2E test**

### Benchmarking

6. **Benchmark query latency**
7. **Benchmark hybrid and multi-path retrieval**
8. **Benchmark image retrieval**
9. **Benchmark kiosk image loading**

### Regression + Submission

10. **Run regression suite against fixed KB snapshot**
11. **Generate final KPI report by KB version**
12. **Verify hub logs are readable during demo flow**
13. **Validate image retrieval evaluation set**
14. **Validate multimodal regression set**
15. **Verify kiosk image display outcomes**
16. **Fix critical/blocking bugs only**
17. **Freeze codebase**
18. **Prepare final submission package**
19. **Run final demo rehearsal**

## Sprint 8 Total

**0 planned feature story points**  
**19 testing/stabilization tasks**

---

# Sprint Goal

Validate, benchmark, stabilize, and submit the ResKiosk AAIH increment.

By the end of Sprint 8, ResKiosk should have:

1. Full text-query E2E validation.
2. Full clarification E2E validation.
3. Full hybrid retrieval E2E validation.
4. Full compound query E2E validation.
5. Full multimodal image E2E validation.
6. Latency benchmarks.
7. Retrieval quality/stability benchmarks.
8. Kiosk image loading benchmarks.
9. Regression results against a fixed KB snapshot.
10. Final KPI report by KB version.
11. Critical/blocking bugs fixed.
12. Final codebase frozen.
13. Final submission package prepared.
14. Final demo rehearsed.

The sprint should produce one final demoable flow:

- **Final product demo flow:** resident query → clarification/retrieval if needed → evidence-backed answer → image evidence where appropriate → readable logs → KPI/benchmark evidence → final submission package

---

# Person 1 — Text, Clarification, and Safety E2E Owner

## Assigned Tasks

1. **Run full text-query E2E test**
2. **Run clarification E2E test**
3. Support **Run regression suite against fixed KB snapshot**

## Main Responsibility

Own validation of the core resident text-query experience and clarification loop.

## Tasks

- Test standard text query path from query input through response and logs.
- Confirm answer includes expected evidence.
- Confirm source IDs and query logs are present.
- Confirm no disabled/unpublished evidence appears.
- Test ambiguous query.
- Confirm clarification chips appear.
- Confirm selected chip is sent back.
- Confirm pipeline resumes correctly.
- Confirm clarification resolution is logged.
- Confirm rewrite/retrieval did not run before clarification resolution.
- Contribute text and clarification cases to the fixed snapshot regression suite.

## Skills Needed

- Manual/automated E2E testing
- Backend/query flow understanding
- Clarification UX understanding
- Safety/filtering awareness
- Bug reporting
- Regression test documentation

## Dependencies

- Depends on final Sprint 7 build.
- Coordinates with Person 5 for bug triage and freeze decisions.

---

# Person 2 — Retrieval Benchmarking Owner

## Assigned Tasks

1. **Run hybrid retrieval E2E test**
2. **Run compound query E2E test**
3. **Benchmark hybrid and multi-path retrieval**
4. Support **Validate image retrieval evaluation set** where retrieval metrics overlap

## Main Responsibility

Own final validation of hybrid retrieval, multi-path retrieval, and retrieval quality/stability benchmarks.

## Tasks

- Test exact-term queries.
- Confirm vector candidates, lexical candidates, and fusion output are logged.
- Confirm filters are applied.
- Confirm final evidence matches expectations.
- Test top-2 intent detection.
- Confirm per-path retrieval runs.
- Confirm deterministic merge.
- Confirm primary and secondary evidence appear correctly.
- Compare vector-only vs hybrid behavior where available.
- Compare single-path vs multi-path behavior.
- Run exact-term and compound evaluation sets.
- Record top-k match and stability results.

## Skills Needed

- Retrieval evaluation
- Hybrid/BM25/vector search understanding
- Test dataset handling
- Metrics interpretation
- Debugging logs
- Reproducibility discipline

## Dependencies

- Depends on Sprint 3 hybrid retrieval and Sprint 4 multi-path retrieval.
- Coordinates with Person 4 for final KPI report.
- Coordinates with Person 5 for critical bugs.

---

# Person 3 — Multimodal E2E + Kiosk Image Owner

## Assigned Tasks

1. **Run multimodal E2E test**
2. **Benchmark image retrieval**
3. **Benchmark kiosk image loading**
4. **Verify kiosk image display outcomes**

## Main Responsibility

Own final validation of the image workflow from upload through kiosk display.

## Tasks

- Test image upload.
- Confirm thumbnail/compressed rendition generation.
- Confirm image embedding generation.
- Confirm text-to-image retrieval returns expected image evidence.
- Confirm kiosk renders image evidence.
- Confirm image-first behavior works.
- Confirm fallback behavior if image evidence fails.
- Measure embedding generation time, retrieval latency, top-k image accuracy, and fixed-config stability.
- Measure thumbnail and compressed rendition load behavior.

## Skills Needed

- Android/kiosk testing
- Image retrieval workflow understanding
- Performance benchmarking
- Multimodal evidence debugging
- UI fallback validation
- Bug reporting

## Dependencies

- Depends on Sprint 6 image asset lifecycle and Sprint 7 image retrieval/rendering.
- Coordinates with Person 4 for KPI report.
- Coordinates with Person 5 for demo rehearsal and bug triage.

---

# Person 4 — KPI, Logs, and Regression Owner

## Assigned Tasks

1. **Run regression suite against fixed KB snapshot**
2. **Generate final KPI report by KB version**
3. **Verify hub logs are readable during demo flow**
4. **Validate image retrieval evaluation set**
5. **Validate multimodal regression set**

## Main Responsibility

Own final reporting, regression evidence, and observable proof that the system works.

## Tasks

- Run fixed KB snapshot regression.
- Validate expected outcomes for text retrieval, clarification, hybrid retrieval, compound retrieval, image retrieval, and kiosk rendering.
- Generate final KPI report by KB version.
- Include query count, p50/p95 latency, fallback/no-result count, clarification trigger count, evidence stability, and image retrieval results where available.
- Confirm hub logs are readable during demo.
- Validate image retrieval and multimodal regression results.
- Record final results for submission materials.

## Skills Needed

- Metrics/report generation
- Regression test execution
- SQL/log analysis
- Documentation
- Retrieval/evidence interpretation
- Quality assurance

## Dependencies

- Depends on Persons 1–3 test results.
- Coordinates with Person 5 for final submission package.
- Coordinates with all owners for bug severity classification.

---

# Person 5 — Release, Bug Triage, Freeze, and Submission Owner

## Assigned Tasks

1. **Fix critical/blocking bugs only**
2. **Freeze codebase**
3. **Prepare final submission package**
4. **Run final demo rehearsal**

## Main Responsibility

Own release discipline, bug triage, code freeze, final packaging, and demo readiness.

## Tasks

- Review bugs from Persons 1–4.
- Classify bugs as critical/blocking, non-blocking, or deferred.
- Ensure only critical/blocking bugs are fixed during Sprint 8.
- Track fixes and retests.
- Prevent scope creep or new feature work.
- Define freeze criteria.
- Record final commit/tag/version.
- Prepare final codebase submission.
- Include final KPI/benchmark outputs and known limitations/deferred items.
- Run final demo path end-to-end.

## Skills Needed

- Release management
- Bug triage
- Git/version control
- Documentation
- Demo coordination
- Ability to enforce scope discipline

## Dependencies

- Depends on Persons 1–4 testing and benchmark outputs.
- Coordinates with all team members for final bug fixes.
- Owns final codebase freeze and submission readiness.

---

# Ownership Map

| Person | Ownership Area | Main Tasks | Points |
|---|---|---:|---:|
| Person 1 | Text query, clarification, safety E2E | Text E2E, clarification E2E, regression support | 0 |
| Person 2 | Hybrid and compound retrieval benchmarking | Hybrid E2E, compound E2E, retrieval benchmarks | 0 |
| Person 3 | Multimodal and kiosk image validation | Multimodal E2E, image retrieval benchmark, kiosk image benchmark | 0 |
| Person 4 | KPI, logs, regression, evaluation validation | Regression suite, KPI report, log verification, evaluation sets | 0 |
| Person 5 | Release, bug triage, freeze, submission | Critical bugs, code freeze, package, demo rehearsal | 0 |

Sprint 8 has no planned feature story points. The points column is intentionally zero because this sprint is reserved for validation and stabilization.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

All five people agree on:

```text
What build is being tested?
What KB snapshot is fixed?
What benchmark scripts/checklists are used?
What counts as critical/blocking?
What is the code freeze deadline?
What demo path is required?
```

## Final Submission Flow

```text
critical bugs fixed
→ regression rerun
→ KPI report finalized
→ demo rehearsal completed
→ codebase frozen
→ final package prepared
```

---

# End-of-Sprint Demo / Submission Checklist

By June 20, the team should have:

1. Full text-query E2E result.
2. Full clarification E2E result.
3. Hybrid retrieval E2E result.
4. Compound retrieval E2E result.
5. Multimodal E2E result.
6. Query latency benchmark.
7. Retrieval benchmark.
8. Image retrieval benchmark.
9. Kiosk image loading benchmark.
10. Regression suite result.
11. Final KPI report by KB version.
12. Readable hub log verification.
13. Image retrieval evaluation result.
14. Multimodal regression result.
15. Kiosk image display outcome verification.
16. Critical/blocking bugs fixed.
17. Codebase frozen.
18. Final submission package prepared.
19. Final demo rehearsed.

---

# Practical Scope Warning

Do not add planned feature development in Sprint 8. Only critical/blocking bug fixes should be accepted.

Do not change the fixed KB snapshot unless a blocking issue requires it. Benchmarking and regression results depend on a stable snapshot.
