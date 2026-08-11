#!/usr/bin/env python3
"""Validate structure, inventory coverage, and score ordering in an organ-system report."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


SYSTEMS = (
    "Cardiovascular and vascular",
    "Respiratory",
    "Neurologic",
    "Mental and behavioral health",
    "Endocrine and metabolic",
    "Gastrointestinal",
    "Hepatic, biliary, and pancreatic",
    "Renal and urinary",
    "Hematologic",
    "Immune, inflammatory, and lymphatic",
    "Musculoskeletal and connective tissue",
    "Integumentary",
    "Reproductive and sexual",
    "Sensory",
    "Oral and dental",
    "Sleep and circadian",
)

COMPONENTS = (
    "Heart (structure, rhythm, and pump)",
    "Arterial and coronary circulation",
    "Venous and peripheral circulation",
    "Lungs and airways",
    "Brain and cognition",
    "Spinal cord and peripheral nerves",
    "Autonomic nervous system",
    "Mood, anxiety, and behavioral function",
    "Thyroid",
    "Glucose regulation and endocrine pancreas",
    "Adrenal and other endocrine function",
    "Esophagus and stomach",
    "Small intestine and absorption",
    "Colon and rectum",
    "Liver",
    "Gallbladder and biliary tract",
    "Exocrine pancreas",
    "Kidneys",
    "Bladder and lower urinary tract",
    "Red blood cells and oxygen carrying",
    "White blood cells and bone marrow",
    "Platelets and coagulation",
    "Immune and lymphatic function",
    "Bones",
    "Joints, tendons, and ligaments",
    "Skeletal muscle",
    "Spine",
    "Skin",
    "Hair and nails",
    "Reproductive organs and hormonal function",
    "Sexual function",
    "Eyes and vision",
    "Ears, hearing, and vestibular function",
    "Teeth and periodontium",
    "Oral mucosa, jaw, and salivary glands",
    "Sleep and circadian function",
)

REQUIRED_HEADINGS = (
    "## Lowest-scoring systems",
    "## Score meaning",
    "## Current status context",
    "## Ranked system scores",
    "## Detailed organ and subsystem scores",
    "## Five lowest systems",
    "## Cross-system findings",
    "## Evidence gaps",
    "## Evidence appendix",
    "### Source coverage",
    "### Safety notes",
    "### Limitations",
    "### Evidence references",
)
SYSTEM_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10\s*\|"
)
COMPONENT_ROW_RE = re.compile(
    r"^\|\s*[^|]+\|\s*([^|]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10\s*\|"
)
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}|YYYY-MM-DD|^\|\s*…\s*\|", re.MULTILINE)


def _section(text: str, heading: str) -> str:
    after = text.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", after, flags=re.MULTILINE)
    return after[: next_heading.start()] if next_heading else after


def _valid_score(score: float) -> bool:
    return 0 <= score <= 10 and math.isclose(score * 2, round(score * 2), abs_tol=1e-8)


def validate(text: str) -> list[str]:
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")
    if PLACEHOLDER_RE.search(text):
        errors.append("report still contains template placeholders")

    if "## Ranked system scores" in text:
        section = _section(text, "## Ranked system scores")
        rows = [
            (int(match.group(1)), match.group(2).strip(), float(match.group(3)))
            for line in section.splitlines()
            if (match := SYSTEM_ROW_RE.match(line))
        ]
        if len(rows) != len(SYSTEMS):
            errors.append(
                f"ranked system table must contain exactly {len(SYSTEMS)} rows; found {len(rows)}"
            )
        else:
            ranks = [row[0] for row in rows]
            if ranks != list(range(1, len(SYSTEMS) + 1)):
                errors.append(f"system ranks must be sequential; found {ranks}")

            names = [row[1] for row in rows]
            missing = sorted(set(SYSTEMS) - set(names))
            extra = sorted(set(names) - set(SYSTEMS))
            if missing:
                errors.append(f"missing canonical systems: {', '.join(missing)}")
            if extra:
                errors.append(f"unexpected canonical system names: {', '.join(extra)}")
            if len(set(names)) != len(names):
                errors.append("canonical systems must be unique")

            scores = [row[2] for row in rows]
            invalid = [score for score in scores if not _valid_score(score)]
            if invalid:
                errors.append(f"system scores must be 0–10 in 0.5 increments; found {invalid}")
            if scores != sorted(scores):
                errors.append(f"system scores must be sorted lowest to highest; found {scores}")

    if "## Detailed organ and subsystem scores" in text:
        section = _section(text, "## Detailed organ and subsystem scores")
        rows = [
            (match.group(1).strip(), float(match.group(2)))
            for line in section.splitlines()
            if (match := COMPONENT_ROW_RE.match(line))
        ]
        names = [row[0] for row in rows]
        missing = sorted(set(COMPONENTS) - set(names))
        if missing:
            errors.append(f"missing required organ/subsystem rows: {', '.join(missing)}")
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            errors.append(f"duplicate organ/subsystem rows: {', '.join(duplicates)}")
        invalid = [score for _, score in rows if not _valid_score(score)]
        if invalid:
            errors.append(f"organ/subsystem scores must be 0–10 in 0.5 increments; found {invalid}")

    return errors


def _self_test() -> None:
    system_rows = [
        f"| {rank} | {name} | 5.0/10 | 2–8 | Low | uncertainty-driven | No direct data |"
        for rank, name in enumerate(SYSTEMS, start=1)
    ]
    component_rows = [
        f"| Parent system | {name} | 5.0/10 | 2–8 | Low | uncertainty-driven | No direct data |"
        for name in COMPONENTS
    ]
    fixture = "\n".join(
        [
            "# Organ and Bodily-System Health Report — Test User",
            "## Lowest-scoring systems",
            "- Test.",
            "## Score meaning",
            "- Test.",
            "## Current status context",
            "- Test.",
            "## Ranked system scores",
            *system_rows,
            "## Detailed organ and subsystem scores",
            *component_rows,
            "## Five lowest systems",
            "- Test.",
            "## Cross-system findings",
            "- Test.",
            "## Evidence gaps",
            "- Test.",
            "## Evidence appendix",
            "### Source coverage",
            "- Test.",
            "### Safety notes",
            "- Test.",
            "### Limitations",
            "- Test.",
            "### Evidence references",
            "- Test.",
        ]
    )
    assert validate(fixture) == []
    assert validate(fixture.replace("| 1 | Cardiovascular and vascular | 5.0/10", "| 1 | Cardiovascular and vascular | 5.5/10"))
    assert validate(fixture.replace("| Parent system | Thyroid |", "| Parent system | Missing thyroid |"))


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
