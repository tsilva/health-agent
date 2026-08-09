#!/usr/bin/env python3
"""Validate the ranked table and required sections in a mortality report."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


REQUIRED_HEADINGS = (
    "## Probability definition",
    "## Source coverage",
    "## Ranked top 10 causes",
    "## Highest-leverage prevention priorities",
    "## Limitations",
)
ROW_RE = re.compile(
    r"^\|\s*(10|[1-9])\s*\|\s*([^|]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)%\s*\|"
)
RESIDUAL_RE = re.compile(
    r"\*\*Residual probability for all other causes:\*\*\s*([0-9]+(?:\.[0-9]+)?)%",
    re.IGNORECASE,
)


def validate(text: str) -> list[str]:
    errors: list[str] = []
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")

    ranked_heading = "## Ranked top 10 causes"
    if ranked_heading not in text:
        return errors

    ranked_section = text.split(ranked_heading, 1)[1]
    next_heading = re.search(r"^##\s+", ranked_section, flags=re.MULTILINE)
    if next_heading:
        ranked_section = ranked_section[: next_heading.start()]

    rows: list[tuple[int, str, float]] = []
    for line in ranked_section.splitlines():
        match = ROW_RE.match(line)
        if match:
            rows.append((int(match.group(1)), match.group(2).strip(), float(match.group(3))))

    if len(rows) != 10:
        errors.append(f"ranked table must contain exactly 10 data rows; found {len(rows)}")
    else:
        ranks = [row[0] for row in rows]
        if ranks != list(range(1, 11)):
            errors.append(f"ranks must be 1 through 10 in order; found {ranks}")

        names = [row[1].casefold() for row in rows]
        if len(set(names)) != len(names):
            errors.append("cause categories must be unique")
        if any("all other" in name for name in names):
            errors.append("all other causes must be an unranked residual, not a top-10 row")

        estimates = [row[2] for row in rows]
        if any(value <= 0 or value > 100 for value in estimates):
            errors.append("every top-10 estimate must be greater than 0% and at most 100%")
        if estimates != sorted(estimates, reverse=True):
            errors.append(f"estimates must be sorted from highest to lowest; found {estimates}")

    residual_match = RESIDUAL_RE.search(ranked_section)
    if not residual_match:
        errors.append("missing residual probability for all other causes")
    elif rows:
        residual = float(residual_match.group(1))
        if residual < 0 or residual > 100:
            errors.append("residual probability must be between 0% and 100%")
        total = sum(row[2] for row in rows) + residual
        if not math.isclose(total, 100.0, abs_tol=0.05):
            errors.append(f"top-10 estimates plus residual must equal 100%; found {total:g}%")

    return errors


def _self_test() -> None:
    rows = "\n".join(
        f"| {rank} | Cause {rank} | {11 - rank}% | 1–20% | differential | Test |"
        for rank in range(1, 11)
    )
    point_total = sum(range(1, 11))
    fixture = "\n".join(
        [
            *REQUIRED_HEADINGS[:2],
            "## Ranked top 10 causes",
            rows,
            f"**Residual probability for all other causes:** {100 - point_total}%",
            *REQUIRED_HEADINGS[3:],
        ]
    )
    assert validate(fixture) == []

    broken = fixture.replace("| 10 | Cause 10 | 1%", "| 10 | Cause 10 | 9%")
    assert validate(broken)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, help="Markdown report to validate")
    parser.add_argument("--self-test", action="store_true", help="Run built-in checks")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("self-test passed")
        return 0
    if args.report is None:
        parser.error("report is required unless --self-test is used")

    errors = validate(args.report.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("report validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
