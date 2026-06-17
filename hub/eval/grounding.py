"""
hub/eval/grounding.py

Phase 5 / Slice 6A — rule-based grounding proxy (D9b: rule_v1, offline).

Estimates how much of an answer is supported by the retrieved KB evidence using
deterministic lexical overlap — NO model in the loop, never on the hot path.
Computed offline over logged rows (or in eval). The answer text itself comes
from the non-deterministic local LLM formatter, so this is a *descriptive
measurement of a specific answer instance*, not a reproducible-ranking metric;
given fixed (answer, evidence) inputs the function is fully deterministic.

Output shape matches the query_logs columns:
  grounded_ratio (0..1), unsupported_span_count, grounding_method, grounding_detail (JSON-able)
"""

from __future__ import annotations

import os
import re
from typing import Sequence

GROUNDING_METHOD_RULE_V1 = "rule_v1"

# Sentence is "supported" when this fraction of its content tokens appear in evidence.
SUPPORT_MIN = float(os.environ.get("RESKIOSK_GROUNDING_SUPPORT_MIN", 0.5))

# Tiny, fixed stopword set (deterministic; intentionally small for offline use).
_STOPWORDS = frozenset(
    """a an and are as at be by for from has have in is it its of on or that the
    to was were will with you your this these those they them their our we i he she
    do does can could should would may might please thank thanks here there""".split()
)

_SENT_SPLIT = re.compile(r"[.!?\n]+")
_TOKEN = re.compile(r"[a-z0-9]+")


def _content_tokens(text: str) -> set[str]:
    return {
        t for t in _TOKEN.findall((text or "").lower())
        if len(t) >= 3 and t not in _STOPWORDS
    }


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_SPLIT.split(text or "") if s.strip()]


def grounding_score(
    answer_text: str,
    evidence_texts: Sequence[str],
    *,
    support_min: float = SUPPORT_MIN,
) -> dict:
    """Compute the rule_v1 grounding proxy for one answer against its evidence.

    A sentence is supported if >= support_min of its content tokens appear in the
    combined evidence vocabulary. Sentences with no content tokens (e.g. "Okay.")
    are treated as trivially supported (they make no factual claim).
    """
    evidence_vocab: set[str] = set()
    for ev in evidence_texts or ():
        evidence_vocab |= _content_tokens(ev)

    sentences = _sentences(answer_text)
    if not sentences:
        return {
            "grounded_ratio": None,
            "unsupported_span_count": 0,
            "grounding_method": GROUNDING_METHOD_RULE_V1,
            "grounding_detail": {"support_min": support_min, "unsupported_spans": [], "sentences": 0},
        }

    supported = 0
    unsupported_spans: list[str] = []
    for sentence in sentences:
        toks = _content_tokens(sentence)
        if len(toks) < 2:
            # Fewer than two content tokens (e.g. "Okay.") makes no factual claim
            # worth grounding — treat as trivially supported to avoid false positives.
            supported += 1
            continue
        overlap = len(toks & evidence_vocab) / len(toks)
        if overlap >= support_min:
            supported += 1
        else:
            unsupported_spans.append(sentence[:160])

    total = len(sentences)
    return {
        "grounded_ratio": round(supported / total, 6),
        "unsupported_span_count": len(unsupported_spans),
        "grounding_method": GROUNDING_METHOD_RULE_V1,
        "grounding_detail": {
            "support_min": support_min,
            "sentences": total,
            "supported": supported,
            "unsupported_spans": unsupported_spans,
        },
    }
