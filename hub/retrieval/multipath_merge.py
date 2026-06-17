"""
hub/retrieval/multipath_merge.py

Phase 4 (Slice 5, stories S5.4 + S5.5) — deterministic merge of per-path
compound retrieval results.

Strategy (D8, resolved): **priority-bucket-then-RRF**.
  1. Each unique article is assigned to the highest-priority tier among the
     retrieval paths that returned it (so safety/medical evidence is never
     buried beneath a strongly-ranked general result).
  2. Within a tier, articles are ordered by Reciprocal Rank Fusion across the
     paths that returned them (reusing the same `rrf_k` as hub.retrieval.fusion).
  3. Final ordering is fully deterministic for a fixed set of path inputs:
        (priority desc, rrf_score desc, best_path_rank asc, article_id asc)

Evidence attribution (S5.5): every merged candidate carries the producing
path/intent memberships (intent, per-path rank, per-path score), the merged
rank, and the RRF score — so logs and the response can explain provenance.

Pure module: no DB, no I/O, no globals. Priority values are supplied by the
caller (from search.INTENT_PRIORITY) to keep this decoupled and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence

from hub.retrieval.fusion import RRF_K, HYBRID_TOP_K


@dataclass(frozen=True)
class PathInput:
    """One retrieval path's contribution to the merge.

    candidates: ranked ``(article_id, score)`` pairs, best first (rank = index+1).
    """
    intent: str
    priority: int
    candidates: tuple


@dataclass(frozen=True)
class PathMembership:
    intent: str
    path_rank: int
    path_score: float


@dataclass(frozen=True)
class MergedCandidate:
    article_id: int
    primary_intent: str           # intent of the highest-priority path that returned it
    priority: int                 # tier (max path priority among memberships)
    merged_rank: int              # 1-based rank in the merged ordering
    rrf_score: float              # RRF across all paths that returned this article
    best_path_rank: int           # best (lowest) per-path rank across memberships
    memberships: tuple            # tuple[PathMembership] — all producing paths
    tie_break_key: tuple


@dataclass(frozen=True)
class MultipathMergeOutput:
    strategy: str
    parameters: dict
    results: list                 # list[MergedCandidate]


def merge_paths(
    paths: Sequence[PathInput],
    rrf_k: int = RRF_K,
    top_k: int = HYBRID_TOP_K,
) -> MultipathMergeOutput:
    """Merge per-path candidates into one deterministic ranked list.

    See module docstring for the strategy. Empty / zero-candidate paths are
    handled safely (they simply contribute nothing).
    """
    # article_id -> list[(intent, priority, path_rank, path_score)]
    memberships: dict[int, list[tuple]] = {}
    for path in paths:
        for rank, pair in enumerate(path.candidates, start=1):
            article_id, score = pair
            memberships.setdefault(article_id, []).append(
                (path.intent, path.priority, rank, float(score))
            )

    scored = []
    for article_id, mlist in memberships.items():
        rrf_score = sum(1.0 / (rrf_k + rank) for (_, _, rank, _) in mlist)
        priority = max(pr for (_, pr, _, _) in mlist)
        best_path_rank = min(rank for (_, _, rank, _) in mlist)
        # primary intent = highest-priority membership; tie-break by best rank, then intent name.
        primary_intent = sorted(mlist, key=lambda m: (-m[1], m[2], m[0]))[0][0]
        # memberships rendered deterministically (by path_rank, then intent).
        member_objs = tuple(
            PathMembership(intent=i, path_rank=r, path_score=round(s, 6))
            for (i, _, r, s) in sorted(mlist, key=lambda m: (m[2], m[0]))
        )
        tie_break_key = (-priority, -rrf_score, best_path_rank, article_id)
        scored.append(
            (tie_break_key, article_id, primary_intent, priority, rrf_score, best_path_rank, member_objs)
        )

    scored.sort(key=lambda item: item[0])

    results = []
    for merged_rank, (tie_break_key, article_id, primary_intent, priority, rrf_score, best_path_rank, member_objs) in enumerate(
        scored[:top_k], start=1
    ):
        results.append(
            MergedCandidate(
                article_id=article_id,
                primary_intent=primary_intent,
                priority=priority,
                merged_rank=merged_rank,
                rrf_score=round(rrf_score, 6),
                best_path_rank=best_path_rank,
                memberships=member_objs,
                tie_break_key=tie_break_key,
            )
        )

    return MultipathMergeOutput(
        strategy="priority_bucket_rrf",
        parameters={"rrf_k": rrf_k, "top_k": top_k},
        results=results,
    )
