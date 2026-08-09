#!/usr/bin/env python3
"""Integrate age-interval competing risks from matched life-table inputs.

Input JSON:
{
  "rows": [
    {
      "age_start": 40,
      "age_end": 45,
      "q_all": 0.01,
      "cause_shares": {"heart disease": 0.2, "all other causes": 0.8}
    }
  ],
  "multipliers": {"heart disease": 1.2, "all other causes": 1.0}
}

Every interval's cause shares must have the same keys and sum to 1. The last
open-ended interval may use q_all=1 to allocate all remaining survival.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


TOLERANCE = 1e-8


def _positive_number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{label} must be finite and greater than zero")
    return number


def estimate(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("rows must be a non-empty list")

    raw_multipliers = payload.get("multipliers", {})
    if not isinstance(raw_multipliers, dict):
        raise ValueError("multipliers must be an object")

    categories: list[str] | None = None
    probabilities: dict[str, float] = {}
    survival = 1.0

    for row_index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"row {row_index} must be an object")

        q_all_raw = row.get("q_all")
        if isinstance(q_all_raw, bool) or not isinstance(q_all_raw, (int, float)):
            raise ValueError(f"row {row_index} q_all must be numeric")
        q_all = float(q_all_raw)
        if not math.isfinite(q_all) or not 0 < q_all <= 1:
            raise ValueError(f"row {row_index} q_all must be in (0, 1]")

        shares = row.get("cause_shares")
        if not isinstance(shares, dict) or not shares:
            raise ValueError(f"row {row_index} cause_shares must be a non-empty object")

        row_categories = list(shares)
        if categories is None:
            categories = row_categories
            probabilities = {category: 0.0 for category in categories}
        elif set(row_categories) != set(categories):
            raise ValueError(f"row {row_index} cause categories differ from earlier rows")

        numeric_shares: dict[str, float] = {}
        for category, value in shares.items():
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"row {row_index} share for {category!r} must be numeric")
            share = float(value)
            if not math.isfinite(share) or share < 0:
                raise ValueError(f"row {row_index} share for {category!r} must be non-negative")
            numeric_shares[category] = share

        share_sum = sum(numeric_shares.values())
        if not math.isclose(share_sum, 1.0, abs_tol=TOLERANCE):
            raise ValueError(f"row {row_index} cause shares sum to {share_sum}, not 1")

        adjusted_weights: dict[str, float] = {}
        for category in categories:
            multiplier = _positive_number(
                raw_multipliers.get(category, 1.0), f"multiplier for {category!r}"
            )
            adjusted_weights[category] = numeric_shares[category] * multiplier

        adjusted_weight_sum = sum(adjusted_weights.values())
        if adjusted_weight_sum <= 0:
            raise ValueError(f"row {row_index} has no positive adjusted cause weight")

        if q_all == 1:
            for category in categories:
                probabilities[category] += (
                    survival * adjusted_weights[category] / adjusted_weight_sum
                )
            survival = 0.0
            if row_index != len(rows):
                raise ValueError("q_all=1 is permitted only in the final row")
            break

        baseline_hazard = -math.log1p(-q_all)
        adjusted_hazards = {
            category: baseline_hazard * adjusted_weights[category]
            for category in categories
        }
        adjusted_total_hazard = sum(adjusted_hazards.values())
        adjusted_q_all = 1.0 - math.exp(-adjusted_total_hazard)

        for category in categories:
            probabilities[category] += (
                survival
                * adjusted_q_all
                * adjusted_hazards[category]
                / adjusted_total_hazard
            )
        survival *= 1.0 - adjusted_q_all

    probability_total = sum(probabilities.values())
    return {
        "cause_probabilities": dict(
            sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
        ),
        "cause_total": probability_total,
        "remaining_survival": survival,
        "total_check": probability_total + survival,
        "rows_processed": len(rows),
        "complete_lifetime_distribution": math.isclose(survival, 0.0, abs_tol=TOLERANCE),
    }


def _self_test() -> None:
    result = estimate(
        {
            "rows": [
                {"q_all": 0.2, "cause_shares": {"a": 0.5, "other": 0.5}},
                {"q_all": 1.0, "cause_shares": {"a": 0.6, "other": 0.4}},
            ],
            "multipliers": {"a": 2.0, "other": 1.0},
        }
    )
    assert math.isclose(result["total_check"], 1.0, abs_tol=TOLERANCE)
    assert result["complete_lifetime_distribution"] is True
    assert result["cause_probabilities"]["a"] > result["cause_probabilities"]["other"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", type=Path, help="Input JSON file")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--self-test", action="store_true", help="Run built-in checks")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("self-test passed")
        return 0
    if args.input is None:
        parser.error("input is required unless --self-test is used")

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = estimate(payload)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=args.pretty))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
