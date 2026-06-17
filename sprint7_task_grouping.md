# Sprint 7 — 5-Person Task Grouping

## Sprint 7 Scope

### Slice 7C — Image Embeddings & Semantic Retrieval

1. **Story 2 - Implement image embedding generation service** — 8 pts
2. **Story 3 - Persist image embeddings with model and KB version metadata** — 8 pts
3. **Story 4 - Generate image embeddings during ingest or publish** — 5 pts
4. **Story 5 - Implement text-to-image semantic retrieval path** — 8 pts
5. **Story 6 - Merge image evidence with text evidence response structure** — 5 pts
6. **Story 7 - Apply filtering and validation gates to image retrieval** — 5 pts
7. **Story 8 - Add image retrieval thresholds and deterministic tie-breaks** — 3 pts
8. **Story 9 - Log image retrieval evidence and model metadata** — 3 pts

### Slice 7D — Kiosk Image Rendering & Multimodal Demo

9. **Story 1 - Render image evidence in kiosk responses** — 8 pts
10. **Story 3 - Support image-first response behavior** — 5 pts

## Sprint 7 Total

**58 story points**  
**10 stories**

---

# Sprint Goal

Deliver the core multimodal image workflow before the feature-complete cutoff.

By the end of Sprint 7, ResKiosk should be able to:

1. Generate image embeddings from ready image assets.
2. Persist image embeddings with model and KB version metadata.
3. Generate embeddings during ingest or publish.
4. Retrieve image evidence from English text queries.
5. Merge image evidence into the response structure.
6. Enforce filtering and validation gates for image retrieval.
7. Apply thresholds and deterministic tie-breaks.
8. Log image retrieval evidence and model metadata.
9. Render image evidence in kiosk responses.
10. Support image-first behavior for visual questions.

The sprint should produce one demoable vertical flow:

- **Multimodal image flow:** admin-uploaded image asset → embedding generated → text query retrieves image evidence → filtering/validation enforced → kiosk displays image evidence → image-first query behaves correctly

---

# Person 1 — Image Embedding Service Owner

## Assigned Stories

1. **Slice 7C Story 2 - Implement image embedding generation service** — 8 pts

## Main Responsibility

Own the service that loads the selected image embedding model and encodes ready image assets.

## Tasks

- Load the selected CLIP/SigLIP-style model.
- Configure local/offline model loading.
- Accept a ready image asset as input.
- Apply defined preprocessing steps.
- Return a vector embedding with known dimension.
- Handle model load failure safely.
- Log model name/version and embedding generation errors.
- Add smoke tests for encoding one image asset.

## Skills Needed

- Python backend
- ML model loading/inference basics
- Image preprocessing
- Local/offline runtime configuration
- Error handling
- Test writing

## Dependencies

- Depends on Sprint 5 model selection.
- Depends on Sprint 6 ready image asset states.
- Coordinates with Person 2 for persistence format.
- Coordinates with Person 5 for retrieval logging requirements.

---

# Person 2 — Embedding Persistence + Ingest/Publish Owner

## Assigned Stories

1. **Slice 7C Story 3 - Persist image embeddings with model and KB version metadata** — 8 pts
2. **Slice 7C Story 4 - Generate image embeddings during ingest or publish** — 5 pts

## Main Responsibility

Own embedding storage and the workflow that generates embeddings as part of ingest or publish.

## Tasks

- Store embeddings with stable image evidence or asset ID.
- Link embeddings to KB version.
- Link embeddings to model name/version.
- Invalidate or regenerate embeddings when model or KB version changes.
- Log failed embedding persistence.
- Trigger embedding generation during the selected ingest/publish step.
- Process only eligible ready image assets.
- Prevent publish from exposing image evidence until embeddings are ready or safely unavailable.
- Use stable failure reason codes.

## Skills Needed

- Database schema/storage
- Vector embedding persistence
- KB publish/ingest flow
- Python backend
- Deterministic processing
- Safety/readiness gating

## Dependencies

- Depends on Person 1’s embedding service.
- Depends on Sprint 6 KB version linkage and asset states.
- Coordinates with Person 4 for filtering/validation gates.
- Coordinates with Person 5 for logs.

---

# Person 3 — Text-to-Image Retrieval Owner

## Assigned Stories

1. **Slice 7C Story 5 - Implement text-to-image semantic retrieval path** — 8 pts
2. **Slice 7C Story 8 - Add image retrieval thresholds and deterministic tie-breaks** — 3 pts

## Main Responsibility

Own the retrieval path that turns an English text query into ranked image evidence.

## Tasks

- Encode English retrieval-boundary query for image retrieval.
- Search persisted image embeddings.
- Return top-k image evidence IDs.
- Include score, rank, and render reference.
- Withhold or mark low-confidence results according to threshold.
- Handle no-result cases safely.
- Define near-tie handling rule.
- Use deterministic tie-breaks.
- Log threshold and tie-break decisions.

## Skills Needed

- Vector retrieval
- Similarity scoring
- Backend retrieval path design
- Deterministic ranking
- Threshold tuning
- Python testing

## Dependencies

- Depends on Person 2’s persisted embeddings.
- Coordinates with Person 4 for filtering/validation gates.
- Coordinates with Person 5 for logging and response structure.
- Depends on Sprint 5 modality/evidence schema.

---

# Person 4 — Image Retrieval Filtering + Validation Owner

## Assigned Stories

1. **Slice 7C Story 7 - Apply filtering and validation gates to image retrieval** — 5 pts

## Main Responsibility

Ensure image retrieval is safe and scoped before results are returned to the kiosk.

## Tasks

- Exclude disabled image evidence.
- Exclude unpublished image evidence.
- Exclude quarantined or rejected image metadata.
- Exclude non-ready image assets.
- Apply UI-selected and inferred filters to image evidence where metadata exists.
- Log filtering decisions and candidate counts.
- Add tests for disabled, unpublished, quarantined, rejected, and non-ready asset exclusion.

## Skills Needed

- Retrieval filtering
- Validation gate integration
- Safety-critical edge case handling
- Backend testing
- Taxonomy/metadata awareness
- Query log linkage

## Dependencies

- Depends on Sprint 1 filtering policy.
- Depends on Sprint 3 validation states.
- Depends on Sprint 6 image asset states.
- Coordinates with Person 3’s retrieval path and Person 5’s logs.

---

# Person 5 — Response Integration + Kiosk Rendering Owner

## Assigned Stories

1. **Slice 7C Story 6 - Merge image evidence with text evidence response structure** — 5 pts
2. **Slice 7C Story 9 - Log image retrieval evidence and model metadata** — 3 pts
3. **Slice 7D Story 1 - Render image evidence in kiosk responses** — 8 pts
4. **Slice 7D Story 3 - Support image-first response behavior** — 5 pts

## Main Responsibility

Own the final user-visible image result: response structure, logs, kiosk rendering, and image-first behavior.

## Tasks

- Include image evidence alongside text evidence.
- Ensure image evidence contains evidence ID, modality, score, rank, and render reference.
- Preserve existing text-only response behavior.
- Keep mixed evidence ordering deterministic.
- Log normalized English query, model/version, image evidence IDs, scores, thresholds, display/suppression, and latency.
- Render image evidence returned by the hub.
- Prefer thumbnail/display rendition.
- Handle missing/broken references gracefully.
- Allow hub to mark image evidence as primary.
- Display image-first responses with minimal text framing.
- Avoid authoritative display of low-confidence image matches.

## Skills Needed

- Backend API response design
- Kotlin / Jetpack Compose
- Kiosk UI integration
- Logging/observability
- Image rendering behavior
- Safety-aware UX

## Dependencies

- Depends on Sprint 5 hub-to-kiosk payload support.
- Depends on Sprint 6 kiosk image fallback/optimization.
- Coordinates with Person 3 and Person 4 for retrieved/gated image evidence.
- Coordinates with Person 2 for model/version metadata.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
|---|---|---:|---:|
| Person 1 | Image embedding service | Slice 7C Story 2 | 8 |
| Person 2 | Embedding persistence + ingest/publish generation | Slice 7C Stories 3–4 | 13 |
| Person 3 | Text-to-image retrieval + thresholds/tie-breaks | Slice 7C Stories 5 and 8 | 11 |
| Person 4 | Image retrieval filtering and validation gates | Slice 7C Story 7 | 5 |
| Person 5 | Response integration, logging, kiosk rendering, image-first behavior | Slice 7C Stories 6 and 9; Slice 7D Stories 1 and 3 | 21 |

Person 5 has the largest point load because kiosk rendering and response integration converge in this sprint. If needed, Person 4 can help with image retrieval logging once filtering gates are stable.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Image Retrieval Team: Persons 1–4

Agree on:

```text
How embeddings are generated
Where embeddings are stored
How the text query is encoded
How image search returns candidates
How filters/validation remove unsafe candidates
What thresholds and tie-breaks apply
```

### Response/Kiosk Team: Persons 3–5

Agree on:

```text
What image evidence fields appear in the hub response
Which render reference the kiosk uses
When image-first applies
How low-confidence image matches are handled
What gets logged when images are displayed or suppressed
```

---

# End-of-Sprint Demo Checklist

By the Sprint 7 review, the team should be able to demo:

1. A ready image asset is encoded into an embedding.
2. Image embedding is persisted with KB version and model metadata.
3. Embedding generation occurs during ingest or publish.
4. A text query retrieves relevant image evidence.
5. Image retrieval excludes invalid/unpublished/quarantined/non-ready images.
6. Image retrieval applies threshold and deterministic tie-break rules.
7. Hub response contains image evidence with render reference.
8. Kiosk displays returned image evidence.
9. Image-first query produces image-focused behavior.
10. Logs include image evidence IDs, model metadata, thresholds, latency, and display/suppression status.

---

# Practical Scope Warning

Do not turn Sprint 7 into a full multimodal platform. The goal is the core product path: image asset → embedding → retrieval → kiosk display.

Do not add generative image enhancement or upscaling. Images should be rendered faithfully using hub-generated thumbnails/renditions.
