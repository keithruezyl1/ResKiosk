"""
Compound (multi-path) retrieval evaluation on a fixed scenario set.

Phase 4 Slice 5 Story S5.8. Validates the deterministic priority-bucket-then-RRF
merge (D8) against hand-specified per-path rankings:
  - the merged primary evidence/intent matches expectation,
  - the secondary evidence (best non-primary-intent candidate) matches expectation,
  - multi-path is compared against the single-path (primary-path-only) baseline,
  - the merge is reproducible (run twice → identical ordering).

Pure / offline: operates on the merge engine with synthetic per-path candidates,
so results are independent of model drift. Run:
  python -m hub.eval.compound_eval
  python -m hub.eval.compound_eval --json-out results.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Optional

from hub.retrieval.multipath_merge import PathInput, merge_paths

DEFAULT_DATA = Path(__file__).resolve().parent / "data" / "compound_eval_v1.json"


def load_bundle(path: Optional[str | Path] = None) -> dict[str, Any]:
    with Path(path or DEFAULT_DATA).open("r", encoding="utf-8") as f:
        return json.load(f)


def _path_inputs(scenario: dict[str, Any]) -> list[PathInput]:
    return [
        PathInput(
            intent=p["intent"],
            priority=int(p["priority"]),
            candidates=tuple((int(a), float(s)) for a, s in p["candidates"]),
        )
        for p in scenario["paths"]
    ]


def run_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    paths = _path_inputs(scenario)
    merged = merge_paths(paths)
    results = merged.results

    primary = results[0] if results else None
    primary_intent = primary.primary_intent if primary else None
    primary_article_id = primary.article_id if primary else None

    secondary = next((c for c in results if c.primary_intent != primary_intent), None)
    secondary_intent = secondary.primary_intent if secondary else None
    secondary_article_id = secondary.article_id if secondary else None

    # Single-path baseline = top candidate of the highest-priority path.
    top_path = sorted(paths, key=lambda p: (-p.priority, p.intent))[0]
    single_path_top = top_path.candidates[0][0] if top_path.candidates else None

    # Determinism: re-run and compare ordering.
    rerun = merge_paths(paths)
    deterministic = [c.article_id for c in results] == [c.article_id for c in rerun.results]

    primary_ok = (
        primary_intent == scenario["expected_primary_intent"]
        and primary_article_id == scenario["expected_primary_article_id"]
    )
    secondary_ok = (
        secondary_intent == scenario["expected_secondary_intent"]
        and secondary_article_id == scenario["expected_secondary_article_id"]
    )

    return {
        "id": scenario["id"],
        "primary_intent": primary_intent,
        "primary_article_id": primary_article_id,
        "secondary_intent": secondary_intent,
        "secondary_article_id": secondary_article_id,
        "single_path_top": single_path_top,
        "multipath_differs_from_single": (primary_article_id != single_path_top)
        or (secondary_article_id is not None),
        "merged_order": [c.article_id for c in results],
        "primary_ok": primary_ok,
        "secondary_ok": secondary_ok,
        "deterministic": deterministic,
        "passed": primary_ok and secondary_ok and deterministic,
    }


def run_eval(bundle: Optional[dict[str, Any]] = None, *, data_path: Optional[str | Path] = None) -> dict[str, Any]:
    bundle = bundle or load_bundle(data_path)
    per_scenario = [run_scenario(s) for s in bundle["scenarios"]]
    n = len(per_scenario)
    return {
        "eval_version": bundle.get("eval_version"),
        "kb_version": bundle.get("kb_version"),
        "config": bundle.get("config"),
        "metrics": {
            "n": n,
            "primary_accuracy": sum(r["primary_ok"] for r in per_scenario) / n if n else 0.0,
            "secondary_accuracy": sum(r["secondary_ok"] for r in per_scenario) / n if n else 0.0,
            "deterministic_all": all(r["deterministic"] for r in per_scenario),
            "passed_all": all(r["passed"] for r in per_scenario),
        },
        "per_scenario": per_scenario,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run compound multi-path retrieval eval.")
    parser.add_argument("--data", type=str, default=None)
    parser.add_argument("--json-out", type=str, default=None)
    args = parser.parse_args()
    report = run_eval(data_path=args.data)
    text = json.dumps(report, indent=2)
    print(text)
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
