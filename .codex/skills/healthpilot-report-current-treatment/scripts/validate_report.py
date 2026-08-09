#!/usr/bin/env python3
"""Validate the required structure of a current-treatment report."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_HEADINGS = (
    "## Reconciliation summary",
    "## Source coverage",
    "## Current medications",
    "## Current supplements",
    "## Current non-medication treatments",
    "## Current monitoring and follow-up",
    "## Planned or recommended—not confirmed started",
    "## Unclear or conflicting current status",
    "## Recently stopped or completed",
    "## Reconciliation flags",
    "## Evidence notes",
)
REQUIRED_METADATA = (
    "**Report generated:**",
    "**Profile:**",
    "**Record cutoff:**",
    "**Snapshot confidence:**",
)
ACTIVE_SECTION_RULES = {
    "## Current medications": "No current medications were identified in the available record.",
    "## Current supplements": "No current supplements were identified in the available record.",
    "## Current non-medication treatments": (
        "No current non-medication treatments were identified in the available record."
    ),
    "## Current monitoring and follow-up": (
        "No current monitoring or follow-up regimen was identified in the available record."
    ),
}
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}|YYYY-MM-DD")
DATA_ROW_RE = re.compile(r"^\|(?!\s*(?:---|Medication|Supplement|Treatment|Monitoring))", re.I)


def _section(text: str, heading: str) -> str:
    after = text.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", after, flags=re.MULTILINE)
    return after[: next_heading.start()] if next_heading else after


def validate(text: str) -> list[str]:
    errors: list[str] = []

    for label in REQUIRED_METADATA:
        if label not in text:
            errors.append(f"missing required metadata: {label}")
    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")

    if PLACEHOLDER_RE.search(text):
        errors.append("report still contains template placeholders")

    for heading, empty_statement in ACTIVE_SECTION_RULES.items():
        if heading not in text:
            continue
        section = _section(text, heading)
        has_data_row = any(DATA_ROW_RE.match(line) for line in section.splitlines())
        if not has_data_row and empty_statement not in section:
            errors.append(
                f"{heading} must contain at least one data row or the explicit empty statement"
            )

    if "### Clear conclusion" not in text:
        errors.append("reconciliation summary must include ### Clear conclusion")
    if "### Open question" not in text:
        errors.append("reconciliation summary must include ### Open question")

    return errors


def _self_test() -> None:
    active_sections = []
    for heading, empty_statement in ACTIVE_SECTION_RULES.items():
        active_sections.extend([heading, empty_statement])

    fixture = "\n".join(
        [
            "# Current Medications and Treatments — Test User",
            "**Report generated:** 2026-08-09 12:00 WEST",
            "**Profile:** Test User",
            "**Record cutoff:** 2026-08-08",
            "**Snapshot confidence:** moderate",
            "## Reconciliation summary",
            "### Clear conclusion",
            "- No confirmed items.",
            "### Open question",
            "- None.",
            "## Source coverage",
            "| Source | Status |",
            "|---|---|",
            "| Health log | available |",
            *active_sections,
            "## Planned or recommended—not confirmed started",
            "- None.",
            "## Unclear or conflicting current status",
            "- None.",
            "## Recently stopped or completed",
            "- None.",
            "## Reconciliation flags",
            "- None identified from the available record.",
            "## Evidence notes",
            "- Latest direct sources reviewed.",
        ]
    )
    assert validate(fixture) == []
    assert validate(fixture.replace("**Record cutoff:**", "Record cutoff:"))
    assert validate(fixture + "\n{unfilled placeholder}")


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
