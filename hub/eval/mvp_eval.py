"""
hub/eval/mvp_eval.py

Phase 5 / Slice 6A Story S6A.6 — fixed MVP evaluation query set.

Loads the canonical scenario catalog (data/mvp_eval_set.json) and validates
coverage of the required case types. Execution for exact-term and compound
scenarios is delegated to the dedicated harnesses; this module is the single
source of truth for *which* scenarios the MVP (and the Phase 11 regression
suite) must cover.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "mvp_eval_set.json"


def load_eval_set(path: Optional[str | Path] = None) -> dict[str, Any]:
    with Path(path or DEFAULT_DATA).open("r", encoding="utf-8") as f:
        return json.load(f)


def coverage(bundle: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Report which required case types are covered and by how many scenarios."""
    bundle = bundle or load_eval_set()
    required = list(bundle.get("required_case_types", []))
    counts: dict[str, int] = {t: 0 for t in required}
    for scn in bundle.get("scenarios", []):
        t = scn.get("type")
        if t in counts:
            counts[t] += 1
    missing = sorted(t for t, c in counts.items() if c == 0)
    return {
        "required_case_types": required,
        "counts": counts,
        "missing": missing,
        "complete": not missing,
        "total_scenarios": len(bundle.get("scenarios", [])),
    }


def main() -> None:
    print(json.dumps(coverage(), indent=2))


if __name__ == "__main__":
    main()
