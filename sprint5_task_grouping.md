# Sprint 5 — 5-Person Task Grouping

## Sprint 5 Scope

### Slice 6A — Observability & Trust

1. **Story 6 - Create fixed evaluation query set** — 3 pts
2. **Story 7 - Generate basic KPI report by KB version** — 5 pts

### Slice 7A — Multimodal Schema

3. **Story 1 - Add multimodal KB item schema** — 8 pts
4. **Story 2 - Add stable multimodal evidence identity** — 5 pts
5. **Story 3 - Prepare image asset reference fields** — 5 pts
6. **Story 4 - Add forward-compatible segmentation fields** — 3 pts
7. **Story 5 - Update evidence response contract for modality** — 5 pts
8. **Story 6 - Backfill existing KB articles as text modality** — 5 pts
9. **Story 7 - Add modality-aware evidence logging** — 3 pts

### Slice 7B — Image Asset Lifecycle

10. **Story 1 - Store image assets as first-class KB assets** — 8 pts
11. **Story 2 - Add image upload API for KB assets** — 5 pts
12. **Story 3 - Generate content hashes for image assets** — 3 pts
13. **Story 4 - Generate deterministic thumbnails for image assets** — 8 pts

### Early Integration / Admin Prep

14. **Slice 7C - Story 1 - Select and configure image embedding model** — 5 pts
15. **Slice 7D - Story 2 - Add hub-to-kiosk image evidence payload support** — 5 pts
16. **Slice 7D - Story 5 - Add admin image upload and asset confirmation path** — 8 pts
17. **Slice 7D - Story 7 - Create multimodal demo scenarios** — 3 pts

## Sprint 5 Total

**87 story points**  
**17 stories**

---

# Sprint Goal

Finish metrics/reporting, establish the multimodal schema foundation, and front-load early image asset/model/payload/admin work.

By the end of Sprint 5, ResKiosk should be able to:

1. Run a fixed evaluation query set.
2. Generate a basic KPI report by KB version.
3. Represent both text and image evidence in schema.
4. Preserve existing text KB behavior under the multimodal schema.
5. Assign stable evidence IDs across modalities.
6. Return modality-aware evidence payloads.
7. Store image assets as first-class KB records.
8. Upload image assets through an admin/backend path.
9. Generate content hashes and thumbnails.
10. Select and configure the image embedding model.
11. Prepare the hub-to-kiosk image evidence payload.
12. Define demo scenarios for multimodal behavior.

The sprint should produce three demoable flows:

- **Metrics/reporting flow:** evaluation query set → query logs/metrics → KPI report by KB version
- **Multimodal schema flow:** existing text article + image evidence schema → modality-aware response/logging
- **Image asset intake flow:** admin upload → asset record → hash → thumbnail → asset reference

---

# Person 1 — Metrics + Evaluation Owner

## Assigned Stories

1. **Slice 6A Story 6 - Create fixed evaluation query set** — 3 pts
2. **Slice 6A Story 7 - Generate basic KPI report by KB version** — 5 pts
3. **Slice 7D Story 7 - Create multimodal demo scenarios** — 3 pts

## Main Responsibility

Own evaluation and reporting artifacts that show the system is measurable and demo-ready.

## Tasks

- Create queries covering exact-term retrieval, compound retrieval, clarification, and safety/medical cases.
- Add expected evidence IDs or expected behavior where feasible.
- Generate a KPI report grouped by KB version.
- Include query count, latency, fallback counts, clarification counts, and evidence stability where available.
- Create landmark/building, wayfinding/navigation, and first-aid visual guidance demo scenarios.
- Ensure demo scenarios use a fixed KB snapshot and known assets.

## Skills Needed

- Evaluation/test design
- SQL/querying or export workflows
- Metrics interpretation
- Documentation
- Product demo planning

## Dependencies

- Depends on Sprint 4 metrics/logging fields.
- Coordinates with Person 2 and Person 3 for modality/evidence IDs.
- Coordinates with Person 5 for demo payload and kiosk constraints.

---

# Person 2 — Multimodal Schema + Backfill Owner

## Assigned Stories

1. **Slice 7A Story 1 - Add multimodal KB item schema** — 8 pts
2. **Slice 7A Story 4 - Add forward-compatible segmentation fields** — 3 pts
3. **Slice 7A Story 6 - Backfill existing KB articles as text modality** — 5 pts

## Main Responsibility

Own schema changes that allow ResKiosk to represent text and image evidence without breaking existing KB behavior.

## Tasks

- Add modality support for text and image.
- Ensure existing text-only KB articles remain supported.
- Prepare schema to reference image assets.
- Keep migration additive/backward-compatible.
- Add future-compatible parent/source and segment fields without enabling semantic chunking.
- Backfill existing KB articles as text modality.
- Preserve enabled/status behavior, embeddings, and current query response behavior.

## Skills Needed

- Database schema design
- SQLAlchemy / migrations
- Backward-compatible migration strategy
- KB data model understanding
- Careful testing against existing DB

## Dependencies

- Coordinates with Person 3 for evidence identity and response contract.
- Coordinates with Person 4 for asset reference structure.
- Depends on Sprint 1 metadata/filter foundation.

---

# Person 3 — Evidence Identity + Response Contract Owner

## Assigned Stories

1. **Slice 7A Story 2 - Add stable multimodal evidence identity** — 5 pts
2. **Slice 7A Story 5 - Update evidence response contract for modality** — 5 pts
3. **Slice 7A Story 7 - Add modality-aware evidence logging** — 3 pts

## Main Responsibility

Own how evidence is identified, returned, and logged across text and image modalities.

## Tasks

- Preserve stable identifiers for text evidence.
- Define stable evidence identity for image evidence.
- Tie evidence identity to KB version.
- Maintain backward compatibility with existing source_id behavior.
- Add evidence_id and modality to evidence responses.
- Allow image evidence to include asset/render references when available.
- Log evidence modality alongside evidence IDs.
- Keep logs bounded to top-k and legacy-compatible.

## Skills Needed

- API schema design
- Backend response modeling
- Logging/observability
- Backward compatibility awareness
- KB/evidence model understanding

## Dependencies

- Depends on Person 2’s schema changes.
- Coordinates with Person 5 on kiosk payload support.
- Coordinates with Person 1 so KPI reporting can group by modality.

---

# Person 4 — Image Asset Backend Owner

## Assigned Stories

1. **Slice 7A Story 3 - Prepare image asset reference fields** — 5 pts
2. **Slice 7B Story 1 - Store image assets as first-class KB assets** — 8 pts
3. **Slice 7B Story 2 - Add image upload API for KB assets** — 5 pts
4. **Slice 7B Story 3 - Generate content hashes for image assets** — 3 pts
5. **Slice 7B Story 4 - Generate deterministic thumbnails for image assets** — 8 pts

## Main Responsibility

Own the backend path for adding and storing image assets.

## Tasks

- Add image asset reference fields or link structure.
- Support original and thumbnail references once generated.
- Handle missing/broken asset references safely.
- Create durable image asset records.
- Accept supported image uploads.
- Validate file size and MIME type.
- Store original image reference.
- Generate deterministic content hashes.
- Generate deterministic thumbnails using fixed parameters.
- Store hash and thumbnail references.
- Log upload/hash/thumbnail failures.

## Skills Needed

- FastAPI/backend API
- File upload handling
- Image processing basics
- Hashing/content identity
- Database modeling
- Error handling/logging
- Security around file validation

## Dependencies

- Depends on Person 2’s schema foundation.
- Coordinates with Person 3 for evidence reference shape.
- Coordinates with Person 5 for admin upload/confirmation and kiosk payload needs.

---

# Person 5 — Model/Payload/Admin Integration Owner

## Assigned Stories

1. **Slice 7C Story 1 - Select and configure image embedding model** — 5 pts
2. **Slice 7D Story 2 - Add hub-to-kiosk image evidence payload support** — 5 pts
3. **Slice 7D Story 5 - Add admin image upload and asset confirmation path** — 8 pts

## Main Responsibility

Own early integration work that connects backend assets to model selection, kiosk payloads, and admin upload/confirmation.

## Tasks

- Select CLIP/SigLIP-style model.
- Document model choice, version, local/offline loading path, preprocessing, and licensing/deployment constraints.
- Run smoke test to encode an image.
- Update kiosk response model to support image evidence.
- Include evidence ID, modality, score/rank, and render reference in payload.
- Preserve compatibility with text-only responses.
- Allow admin to upload image assets and confirm upload details.
- Show stored original reference, thumbnail status, content hash, and errors.

## Skills Needed

- Model selection / ML integration basics
- Android/kiosk API contract awareness
- Backend/API integration
- Admin console workflow
- Documentation
- Image pipeline understanding

## Dependencies

- Depends on Person 4’s upload API and asset record shape.
- Coordinates with Person 3 on evidence payload shape.
- Coordinates with Person 1 on demo scenario needs.
- Feeds directly into Sprint 7 image retrieval work.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
|---|---|---:|---:|
| Person 1 | Evaluation, KPI report, demo scenarios | Slice 6A Stories 6–7; Slice 7D Story 7 | 11 |
| Person 2 | Multimodal schema + text backfill | Slice 7A Stories 1, 4, 6 | 16 |
| Person 3 | Evidence identity, response contract, modality logging | Slice 7A Stories 2, 5, 7 | 13 |
| Person 4 | Image asset backend, upload, hashes, thumbnails | Slice 7A Story 3; Slice 7B Stories 1–4 | 29 |
| Person 5 | Model selection, kiosk payload, admin upload path | Slice 7C Story 1; Slice 7D Stories 2 and 5 | 18 |

Person 4 has the largest point load because image asset intake is the largest backend workstream. If capacity becomes tight, Person 2 or Person 3 should support asset reference and thumbnail integration once their schema/API work is stable.

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Multimodal Data Contract Team: Persons 2, 3, 4, and 5

Agree on:

```text
What is a multimodal evidence item?
How does image evidence reference an asset?
What fields appear in hub responses?
What fields does the kiosk need?
What gets logged for text vs image evidence?
```

### Image Asset Pipeline Team: Persons 4 and 5

Agree on:

```text
How does admin upload an image?
What does the asset record contain?
When are hashes and thumbnails generated?
What does confirmation show?
How will the embedding model consume the image later?
```

---

# End-of-Sprint Demo Checklist

By the Sprint 5 review, the team should be able to demo:

1. Existing KB articles are represented as text modality.
2. Image modality exists in the schema.
3. Evidence IDs are stable for text and image evidence.
4. Evidence responses include modality.
5. Query logs include evidence modality.
6. Admin can upload an image asset.
7. Image asset receives a content hash.
8. Image asset receives a thumbnail.
9. Admin can confirm uploaded image information.
10. Kiosk response model can accept image evidence fields.
11. Basic KPI report can be generated by KB version.
12. Multimodal demo scenarios are documented.

---

# Practical Scope Warning

Do not introduce semantic chunking in Sprint 5. The schema can include future-compatible fields, but the retrieval unit remains one KB row.

Do not overbuild the admin image workflow. Sprint 5 only needs enough upload/confirmation behavior to support image asset ingestion and the later retrieval/demo path.
