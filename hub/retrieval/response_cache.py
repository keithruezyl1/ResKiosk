"""
hub/retrieval/response_cache.py

Phase 6 / Slice 6B — safe response-level cache (Goal 11).

Version- and config-aware, in-memory, TTL + LRU bounded. Caches only clean
non-safety answers; safety-critical intents always bypass (D11). The cache key
includes kb_version AND a config_signature (D10) so any KB publish or config
change misses stale entries; publish/admin paths also hard-invalidate.

Pure/process-local: no DB, no I/O on the hot path (the hub is single-process).
`now` is injectable for deterministic tests.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from collections import OrderedDict
from pathlib import Path
from typing import Optional

TTL_SECS = int(os.environ.get("RESKIOSK_RESPONSE_CACHE_TTL_SECS", 300))
MAX_ENTRIES = int(os.environ.get("RESKIOSK_RESPONSE_CACHE_MAX", 512))

# D11: never cache life-safety topics (matches the high-priority INTENT_PRIORITY set).
SAFETY_CRITICAL_INTENTS = frozenset({"safety", "emergency", "medical", "children", "special_needs"})

# cache_status values written to query_logs / logs.
STATUS_HIT = "hit"
STATUS_MISS = "miss"
STATUS_BYPASS = "bypass"

_TAXONOMY_DIR = Path(__file__).resolve().parents[1] / "taxonomy"
_POLICY_FILES = ("taxonomy_v1.json", "legacy_category_map_v1.json")

# key -> [expires_at, payload]
_CACHE: "OrderedDict[str, list]" = OrderedDict()

# Memoized config signature (config is process-static; recomputed on restart).
_CONFIG_SIG: Optional[str] = None


def current_config_signature() -> str:
    """Process-memoized config signature (computed once; restart picks up changes)."""
    global _CONFIG_SIG
    if _CONFIG_SIG is None:
        _CONFIG_SIG = build_config_signature()
    return _CONFIG_SIG


def reset_config_signature() -> None:
    """Test hook: force recomputation of the memoized config signature."""
    global _CONFIG_SIG
    _CONFIG_SIG = None


# ── config signature (D10) ───────────────────────────────────────────────────

def _policy_digest() -> str:
    h = hashlib.sha1()
    for name in _POLICY_FILES:
        p = _TAXONOMY_DIR / name
        try:
            h.update(p.read_bytes())
        except OSError:
            h.update(b"<missing>")
    return h.hexdigest()[:12]


def build_config_signature() -> str:
    """Short hash of all retrieval-affecting config. Computed from the effective
    constants in search/fusion (read at import) plus the taxonomy/filter policy
    files. Changes only when config changes (which needs a process restart)."""
    # Lazy import to avoid any import cycle (search does not import this module).
    from hub.retrieval import search
    from hub.retrieval.fusion import RRF_K, HYBRID_TOP_K

    payload = {
        "sim_threshold": search.THRESHOLD,
        "clarification_floor": search.CLARIFICATION_FLOOR,
        "non_en_threshold": search.NON_EN_THRESHOLD,
        "non_en_clarification_floor": search.NON_EN_CLARIFICATION_FLOOR,
        "intent_action_threshold": search.INTENT_ACTION_THRESHOLD,
        "compound_intent_min": search.COMPOUND_INTENT_MIN,
        "compound_gap_max": search.COMPOUND_GAP_MAX,
        "rrf_k": RRF_K,
        "hybrid_top_k": HYBRID_TOP_K,
        "rlhf_enabled": search.RLHF_ENABLED,
        "rlhf_alpha": search.RLHF_ALPHA,
        "rlhf_max_delta": search.RLHF_BIAS_MAX_DELTA,
        "policies": _policy_digest(),
    }
    raw = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


# ── key + safety ─────────────────────────────────────────────────────────────

def is_safety_critical(intent: Optional[str]) -> bool:
    return intent in SAFETY_CRITICAL_INTENTS


def make_cache_key(
    *,
    normalized_query: str,
    intent: Optional[str],
    language: str,
    ui_filter: Optional[str],
    exclude_ids,
    kb_version,
    config_signature: str,
) -> str:
    parts = [
        (normalized_query or "").strip().lower(),
        intent or "",
        language or "en",
        ui_filter or "",
        ",".join(str(i) for i in sorted(exclude_ids or [])),
        str(kb_version),
        config_signature,
    ]
    return hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()


# ── store / lookup ───────────────────────────────────────────────────────────

def get(key: str, now: Optional[float] = None):
    now = now if now is not None else time.time()
    entry = _CACHE.get(key)
    if entry is None:
        return None
    expires_at, payload = entry
    if now >= expires_at:
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)  # LRU touch
    return payload


def set(key: str, payload: dict, now: Optional[float] = None, ttl: Optional[int] = None) -> None:
    now = now if now is not None else time.time()
    ttl = ttl if ttl is not None else TTL_SECS
    if ttl <= 0:
        return
    _CACHE[key] = [now + ttl, payload]
    _CACHE.move_to_end(key)
    while len(_CACHE) > MAX_ENTRIES:
        _CACHE.popitem(last=False)  # evict LRU


def invalidate_response_cache() -> None:
    """Clear all cached responses. Called on KB publish / config update."""
    _CACHE.clear()


def stats() -> dict:
    return {"size": len(_CACHE), "max_entries": MAX_ENTRIES, "ttl_secs": TTL_SECS}
