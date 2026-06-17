---
title: ResKiosk AAIH Development — Confluence Mirror
source: https://reskiosk.atlassian.net/wiki/spaces/SCRUM
space_key: SCRUM
synced: 2026-06-17
---

# ResKiosk AAIH Development — Documentation

This directory is a local mirror of the **ResKiosk AAIH Development** Confluence
space (`SCRUM`). Each file carries frontmatter with its `confluence_id`,
`source` URL, and `last_updated` timestamp so it can be traced back to the
original page.

> The Confluence space *home page* itself contained only the default Confluence
> welcome template (no project content), so this README replaces it with an
> index of the real pages.

## Start here

- [What ResKiosk currently is (pre-AAIH)](what-reskiosk-currently-is.md) — baseline of the existing product
- [PLEASE READ PRIOR TO DEVELOPMENT](please-read-prior-to-development.md) — ground rules before writing code
- [Suggested workflow for implementing user stories](suggested-workflow-for-user-stories.md)

## Sprint plan

- [8-Week Sprint Plan](sprint-plan/8-week-sprint-plan.md) — overall cadence and cutoffs
  - [Sprint 1](sprint-plan/sprint-1.md)
  - [Sprint 2](sprint-plan/sprint-2.md)
  - [Sprint 3](sprint-plan/sprint-3.md)

## Post-sprint documentation

- [Post-Sprint Documentation (overview)](post-sprint/README.md)
  - [Sprint 1 Post-Sprint Summary](post-sprint/sprint-1-post-sprint-summary.md)

## Product Increment Goals (AAIH)

- [Product Increment Goals — overview](product-increment-goals/README.md)
- [Implementation Slices Sequence (AAIH Increment)](product-increment-goals/implementation-slices-sequence.md)

| # | Goal |
|---|------|
| 1 | [Semantic image search (CLIP/SigLIP)](product-increment-goals/goal-01-semantic-image-search-clip-siglip.md) |
| 2 | [Image storage as first-class KB assets](product-increment-goals/goal-02-image-storage-as-first-class-kb-assets.md) |
| 3 | [KB schema rework for multimodal retrieval](product-increment-goals/goal-03-kb-schema-rework-for-multimodal-retrieval.md) |
| 4 | [Hybrid retrieval with BM25 + vectors (reproducible ranking)](product-increment-goals/goal-04-hybrid-retrieval-with-bm25-vectors-reproducible-ranking.md) |
| 5 | [Multi-path (split/dual) retrieval for compound queries](product-increment-goals/goal-05-multi-path-split-dual-retrieval-for-compound-queries.md) |
| 6 | [Clarification UX before rewriting](product-increment-goals/goal-06-clarification-ux-before-rewriting.md) |
| 7 | [Metadata schema + filtering policy (UI + inferred + hard rules)](product-increment-goals/goal-07-metadata-schema-filtering-policy-ui-inferred-hard-rules.md) |
| 8 | [Metadata validation gate (rules + stats + human review before KB publish)](product-increment-goals/goal-08-metadata-validation-gate-rules-stats-human-review-before-kb-publish.md) |
| 9 | [Retrieval quality improvements without heavy reranking](product-increment-goals/goal-09-retrieval-quality-improvements-without-heavy-reranking.md) |
| 10 | [MVP metrics + logging](product-increment-goals/goal-10-mvp-metrics-logging.md) |
| 11 | [Safer caching patterns (version + TTL + refresh hooks)](product-increment-goals/goal-11-safer-caching-patterns-version-ttl-refresh-hooks.md) |
| 12 | [Canonical pipeline order (normalize → intent → optional clarification → constrained rewrite)](product-increment-goals/goal-12-canonical-pipeline-order-normalize-intent-optional-clarification-constrained-rewrite.md) |

---

*Mirror generated from the Atlassian MCP on 2026-06-17. To refresh, re-pull the
`SCRUM` space and regenerate.*
