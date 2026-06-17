# Sprint 6 — 5-Person Task Grouping

## Sprint 6 Scope

### Slice 7B — Image Asset Lifecycle

1. **Story 5 - Add image asset processing states** — 5 pts
2. **Story 6 - Link image assets to KB version** — 5 pts
3. **Story 7 - Invalidate image artifacts on KB publish** — 5 pts
4. **Story 8 - Add admin asset confirmation view** — 5 pts
5. **Story 9 - Log image asset lifecycle events** — 3 pts
6. **Story 10 - Compress uploaded images and generate optimized renditions** — 5 pts

### Slice 7D — Kiosk Image Rendering & Multimodal Demo

7. **Story 4 - Handle image loading failures and placeholders** — 3 pts
8. **Story 6 - Display image asset status in admin console** — 5 pts
9. **Story 10 - Validate text-only fallback when image evidence is unavailable** — 3 pts
10. **Story 11 - Optimize kiosk image loading and display** — 5 pts

## Sprint 6 Total

**44 story points**  
**10 stories**

---

# Sprint Goal

Complete image asset lifecycle, add basic admin asset/status visibility, and finish kiosk image safety behavior.

By the end of Sprint 6, ResKiosk should be able to:

1. Track image asset processing states.
2. Link image assets and derived artifacts to KB versions.
3. Invalidate image artifacts when a new KB version is published.
4. Show basic admin confirmation/status for uploaded image assets.
5. Log image asset lifecycle events.
6. Generate compressed kiosk-ready image renditions.
7. Handle missing or broken image references safely on kiosk.
8. Fall back to text guidance when image evidence is unavailable.
9. Optimize kiosk loading/display for thumbnails and compressed renditions.

The sprint should produce two demoable flows:

- **Image asset lifecycle flow:** uploaded image → processing state → hash/thumbnail/rendition → KB version link → publish invalidation → logs
- **Kiosk image safety flow:** missing/broken/unavailable image → safe placeholder or suppression → text fallback remains visible

---

# Person 1 — Image State + KB Version Owner

## Assigned Stories

1. **Slice 7B Story 5 - Add image asset processing states** — 5 pts
2. **Slice 7B Story 6 - Link image assets to KB version** — 5 pts

## Main Responsibility

Own the lifecycle state model and KB version linkage for image assets.

## Tasks

- Add image asset states: pending, ready, failed, rejected.
- Ensure pending/failed/rejected assets are not resident-facing.
- Ensure publish does not reference partially processed assets.
- Add reason codes for failed processing.
- Link image asset records or image evidence records to KB version.
- Associate derived artifacts with the KB version used during publish.
- Ensure query logs can identify the KB version that produced image evidence.
- Add tests for state transitions and retrieval eligibility.

## Skills Needed

- Database schema/state modeling
- SQLAlchemy / migrations
- KB versioning knowledge
- Backend safety rules
- Test writing
- Auditability mindset

## Dependencies

- Depends on Sprint 5 image asset records.
- Coordinates with Person 2 for publish invalidation.
- Coordinates with Person 4 for admin status display.
- Coordinates with Person 5 for log events.

---

# Person 2 — Publish Invalidation + Asset Lifecycle Logging Owner

## Assigned Stories

1. **Slice 7B Story 7 - Invalidate image artifacts on KB publish** — 5 pts
2. **Slice 7B Story 9 - Log image asset lifecycle events** — 3 pts

## Main Responsibility

Own artifact invalidation and lifecycle auditability for image assets.

## Tasks

- Invalidate or refresh image-derived artifacts tied to prior KB versions.
- Ensure new KB version uses current image artifact references.
- Include KB version and content hash in image artifact keys where applicable.
- Fail closed or bypass affected image artifacts if invalidation fails.
- Log upload, thumbnail/rendition generation, processing transitions, readiness failures, and invalidation events.
- Ensure logs can be joined by asset ID and KB version.

## Skills Needed

- Publish flow integration
- Backend logging
- KB versioning
- Error handling / fail-closed behavior
- Audit trail design
- Test writing

## Dependencies

- Depends on Person 1’s version/state model.
- Coordinates with Person 3 for rendition metadata.
- Coordinates with Person 4 for admin status information.

---

# Person 3 — Image Compression + Rendition Owner

## Assigned Stories

1. **Slice 7B Story 10 - Compress uploaded images and generate optimized renditions** — 5 pts
2. Support **Slice 7D Story 11 - Optimize kiosk image loading and display** — partial support

## Main Responsibility

Own compressed kiosk-ready image renditions and provide the metadata the kiosk needs to load images efficiently.

## Tasks

- Generate at least one display-size compressed rendition.
- Preserve original image for audit/detail use.
- Use deterministic compression settings.
- Preserve aspect ratio.
- Avoid unsafe cropping.
- Store rendition reference with asset record.
- Store output byte size, dimensions, format, and derivative hash if applicable.
- Log rendition generation failures.
- Define which image reference the kiosk should prefer.

## Skills Needed

- Image processing
- File/rendition generation
- Backend storage references
- Performance awareness
- Deterministic processing
- Safety around medical/map/sign visuals

## Dependencies

- Depends on Sprint 5 thumbnails/hash asset work.
- Coordinates with Person 5 for kiosk display optimization.
- Coordinates with Person 2 for rendition lifecycle logs.

---

# Person 4 — Admin Asset Confirmation + Status Owner

## Assigned Stories

1. **Slice 7B Story 8 - Add admin asset confirmation view** — 5 pts
2. **Slice 7D Story 6 - Display image asset status in admin console** — 5 pts

## Main Responsibility

Own the admin-facing visibility for image asset confirmation and status.

## Tasks

- Show uploaded image asset status.
- Show original image reference or preview.
- Show thumbnail reference or preview when available.
- Show content hash or stable asset identity.
- Show processing errors when present.
- Allow admin to confirm whether an asset is ready for KB use.
- Display pending, ready, failed, and rejected states.
- Distinguish publish-eligible assets from not-ready assets.
- Show KB item or taxonomy linkage where available.

## Skills Needed

- Admin/console UI
- Backend API integration
- Basic asset preview/display handling
- State/status visualization
- Error messaging
- Product/operator UX

## Dependencies

- Depends on Person 1’s processing states.
- Depends on Person 2’s lifecycle logs where needed.
- Depends on Sprint 5 upload/confirmation path.
- Coordinates with Person 3 for thumbnail/rendition references.

---

# Person 5 — Kiosk Image Safety + Fallback Owner

## Assigned Stories

1. **Slice 7D Story 4 - Handle image loading failures and placeholders** — 3 pts
2. **Slice 7D Story 10 - Validate text-only fallback when image evidence is unavailable** — 3 pts
3. **Slice 7D Story 11 - Optimize kiosk image loading and display** — 5 pts

## Main Responsibility

Own kiosk-side safety and graceful display behavior for image evidence.

## Tasks

- Show safe placeholder or hide image block if reference is missing.
- Fall back to original reference only if allowed.
- Prevent broken images from crashing or freezing the kiosk.
- Keep text answer visible when image loading fails.
- Log/report image loading errors where feasible.
- Ensure text answer still works if no image evidence is returned.
- Prefer thumbnail or display-size rendition over original.
- Preserve aspect ratio.
- Avoid unsafe cropping.
- Do not apply generative enhancement or hallucinated detail.

## Skills Needed

- Kotlin / Android
- Jetpack Compose
- Image loading/rendering
- UI fallback behavior
- Offline/local network assumptions
- Safety-conscious UI handling

## Dependencies

- Depends on Person 3’s rendition references.
- Depends on Sprint 5 hub-to-kiosk image evidence payload.
- Coordinates with Person 4 if admin/kiosk share asset fields.
- Feeds into Sprint 7 kiosk image rendering and image-first behavior.

---

# Ownership Map

| Person | Ownership Area | Main Stories | Points |
|---|---|---:|---:|
| Person 1 | Image asset states + KB version linkage | Slice 7B Stories 5–6 | 10 |
| Person 2 | Publish invalidation + lifecycle logging | Slice 7B Stories 7 and 9 | 8 |
| Person 3 | Compression/renditions + kiosk display support | Slice 7B Story 10 + support Story 11 | 5+ |
| Person 4 | Admin confirmation/status visibility | Slice 7B Story 8; Slice 7D Story 6 | 10 |
| Person 5 | Kiosk image failure handling + fallback + optimization | Slice 7D Stories 4, 10, 11 | 11 |

---

# Recommended Collaboration Flow

## Start-of-Sprint Alignment

### Image Lifecycle Team: Persons 1–3

Agree on:

```text
What processing states exist?
What does ready mean?
How are artifacts linked to KB version?
What gets invalidated on publish?
What references are created for thumbnails and compressed renditions?
```

### Admin/Kiosk Display Team: Persons 3–5

Agree on:

```text
Which image reference does the kiosk use first?
What does admin status display?
How are broken/missing images handled?
What fallback should the resident see?
What should be logged?
```

---

# End-of-Sprint Demo Checklist

By the Sprint 6 review, the team should be able to demo:

1. Image asset has processing state.
2. Image asset is linked to a KB version.
3. Image artifact invalidates on publish/version change.
4. Lifecycle events are logged.
5. Compressed display rendition is generated.
6. Admin can see asset confirmation/status.
7. Kiosk handles broken image reference safely.
8. Kiosk preserves text fallback when image is unavailable.
9. Kiosk prefers thumbnail/display rendition for loading.
10. Safety/medical/map/sign images are rendered without content-altering enhancement.

---

# Practical Scope Warning

Do not build a polished digital asset management platform. Sprint 6 only needs enough admin status/confirmation behavior to support image readiness and debugging.

Do not add AI image enhancement. Kiosk display should be faithful and lightweight, using compressed renditions created by the hub.
