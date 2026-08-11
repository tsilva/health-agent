"""Shared filters for parser metadata and private evidence references."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from pathlib import Path


INTERNAL_PATH_NAMES = {
    ".ds_store",
    ".state.json",
    ".review-artifacts",
    "__pycache__",
}

INTERNAL_LINE_MARKERS = (
    "deps:",
    ".ds_store",
    ".state.json",
    ".review-artifacts",
    "no additional snapshot details",
)


def is_internal_path(path: Path, *, source_root: Path | None = None) -> bool:
    try:
        parts = path.relative_to(source_root).parts if source_root else path.parts
    except ValueError:
        parts = path.parts
    return any(
        part.startswith(".") or part.casefold() in INTERNAL_PATH_NAMES
        for part in parts
    )


def is_internal_line(value: str) -> bool:
    normalized = " ".join(value.strip().casefold().split())
    return any(marker in normalized for marker in INTERNAL_LINE_MARKERS)


def visible_lines(lines: Iterable[str]) -> Iterator[tuple[int, str]]:
    """Yield source line numbers and text with HTML comments removed."""
    in_comment = False
    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\n")
        visible_parts: list[str] = []
        cursor = 0
        while cursor < len(line):
            if in_comment:
                end = line.find("-->", cursor)
                if end < 0:
                    cursor = len(line)
                    continue
                in_comment = False
                cursor = end + 3
                continue
            start = line.find("<!--", cursor)
            if start < 0:
                visible_parts.append(line[cursor:])
                break
            visible_parts.append(line[cursor:start])
            in_comment = True
            cursor = start + 4

        visible = "".join(visible_parts).strip()
        if visible and not is_internal_line(visible):
            yield line_number, visible


def slug_token(value: str, *, fallback: str = "item", limit: int = 56) -> str:
    token = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return (token or fallback)[:limit].rstrip("-")


def evidence_reference(
    source_type: str,
    *,
    observed_at: str = "",
    label: str = "",
    line: int | None = None,
) -> str:
    source = source_type.upper()
    parts = [source]
    if observed_at:
        parts.append(slug_token(observed_at, fallback="undated"))
    if label:
        parts.append(slug_token(label))
    if line is not None:
        parts.append(f"L{line}")
    return f"[{':'.join(parts)}]"
