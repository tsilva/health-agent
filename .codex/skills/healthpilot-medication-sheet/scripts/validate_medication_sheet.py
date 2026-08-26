#!/usr/bin/env python3
"""Validate a rendered Healthpilot medication sheet against its JSON spec."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Iterable

try:
    from pypdf import PdfReader
    from reportlab.lib.pagesizes import A4
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit(
        "Missing PDF dependency. Run with the bundled Codex workspace Python runtime "
        "containing reportlab and pypdf."
    ) from exc


PRIVATE_TEXT = re.compile(
    r"(?:/Users/|file://|\.state\.json|\.DS_Store|\.review-artifacts|DEPS:)",
    re.IGNORECASE,
)


def _strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


def _pt_date(value: str) -> str:
    year, month, day = value.split("-")
    return f"{day}/{month}/{year}"


def validate(spec_path: Path, pdf_path: Path) -> None:
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    for value in _strings(spec):
        if PRIVATE_TEXT.search(value):
            raise ValueError("specification contains a private path or parser artifact")

    reader = PdfReader(pdf_path)
    if reader.is_encrypted:
        raise ValueError("PDF must not be encrypted")
    if len(reader.pages) != 1:
        raise ValueError(f"expected exactly one page, found {len(reader.pages)}")
    if reader.get_fields():
        raise ValueError("medication sheet must be a static PDF without form fields")

    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    if abs(width - A4[0]) > 1 or abs(height - A4[1]) > 1:
        raise ValueError(f"expected A4 page size, found {width:.1f} x {height:.1f} pt")

    text = page.extract_text() or ""
    if not text.strip():
        raise ValueError("PDF text is not extractable")
    if PRIVATE_TEXT.search(text):
        raise ValueError("PDF exposes a private path or parser artifact")
    normalized_pdf = _normalize(text)

    expected = [
        spec["profile"]["name"],
        _pt_date(spec["updated_on"]),
        _pt_date(spec["record_cutoff"]),
    ]
    for section in spec["sections"]:
        expected.append(section["title"])
        for item in section["items"]:
            expected.extend([item["name"], item["dose"], item["instructions"], item["reason"]])
    alert = spec.get("monitoring_alert")
    if alert:
        expected.extend([alert["title"], alert["text"]])
    expected.extend(
        re.sub(r"^confirmar\s+", "", value, flags=re.IGNORECASE).rstrip(" .;")
        for value in spec.get("confirmations", [])
    )

    missing = [value for value in expected if _normalize(value) not in normalized_pdf]
    if missing:
        preview = "; ".join(missing[:8])
        raise ValueError(f"PDF is missing expected content: {preview}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    args = parser.parse_args()
    try:
        validate(args.spec, args.pdf)
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print("medication sheet validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
