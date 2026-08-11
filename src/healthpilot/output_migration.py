"""Safe, idempotent migration to the profile/report output layout."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from healthpilot.jsonio import write_json
from healthpilot.paths import REPORT_BUCKETS, classify_report_bucket, output_path, state_path


DATE_RE = re.compile(r"(?<!\d)(\d{4}-\d{2}-\d{2})(?!\d)")
MARKDOWN_LINK_RE = re.compile(r"(?P<prefix>!?\[[^\]]*\]\()(?P<target>[^)#]+)(?P<suffix>\))")
HTML_LINK_RE = re.compile(
    r"(?P<prefix>\b(?:src|href)=[\"'])(?P<target>[^\"'#]+)(?P<suffix>[\"'])",
    re.I,
)
OS_METADATA_NAMES = {".DS_Store", "Thumbs.db"}


def _valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def _extract_date(filename: str) -> str | None:
    return next((value for value in DATE_RE.findall(filename) if _valid_date(value)), None)


def _slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def _normalized_filename(path: Path, *, profile_slug: str, report_date: str) -> str:
    suffix = path.suffix.casefold()
    stem_without_date = DATE_RE.sub("", path.stem, count=1)
    remainder = _slugify(stem_without_date)
    profile_token = _slugify(profile_slug)
    tokens = remainder.split("-")
    profile_tokens = profile_token.split("-")
    contains_profile = any(
        tokens[index : index + len(profile_tokens)] == profile_tokens
        for index in range(max(0, len(tokens) - len(profile_tokens) + 1))
    )
    if not contains_profile:
        remainder = f"{profile_token}-{remainder}" if remainder else profile_token
    return f"{report_date}-{remainder}{suffix}"


def _same_bytes(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False

    def digest(path: Path) -> str:
        hasher = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                hasher.update(block)
        return hasher.hexdigest()

    return digest(left) == digest(right)


def _conflict_path(profile_dir: Path, filename: str, claimed: set[Path]) -> Path:
    base = profile_dir / "legacy" / "conflicts" / filename
    if base not in claimed and not base.exists():
        return base
    for counter in range(2, 10_000):
        candidate = base.with_name(f"{base.stem}-conflict-{counter}{base.suffix}")
        if candidate not in claimed and not candidate.exists():
            return candidate
    raise RuntimeError(f"Unable to allocate conflict path for {filename}")


def _destination(profile_dir: Path, source: Path) -> tuple[Path, str]:
    relative = source.relative_to(profile_dir)
    first_part = relative.parts[0]
    if first_part in REPORT_BUCKETS:
        return source, "already_bucketed"
    if first_part == "legacy" and len(relative.parts) > 1 and relative.parts[1] == "conflicts":
        return source, "existing_conflict"

    bucket = classify_report_bucket(source.name)
    report_date = _extract_date(source.name)
    if bucket and report_date:
        filename = _normalized_filename(
            source,
            profile_slug=profile_dir.name,
            report_date=report_date,
        )
        return profile_dir / bucket / filename, "recognized"
    if bucket and not report_date:
        return profile_dir / "legacy" / "undated" / source.name, "undated"
    if first_part == "legacy":
        return source, "already_legacy"
    return profile_dir / "legacy" / relative, "ambiguous"


def build_migration_manifest(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    output_root = output_path(repo_root)
    operations: list[dict[str, Any]] = []
    metadata_files: list[str] = []
    unchanged = 0
    claimed: set[Path] = set()
    planned_sources: dict[Path, Path] = {}

    if output_root.is_dir():
        for path in sorted(output_root.rglob("*")):
            if path.is_file() and path.name in OS_METADATA_NAMES:
                metadata_files.append(str(path))

        for profile_dir in sorted(path for path in output_root.iterdir() if path.is_dir()):
            for source in sorted(path for path in profile_dir.rglob("*") if path.is_file()):
                if source.name in OS_METADATA_NAMES:
                    continue
                destination, reason = _destination(profile_dir, source)
                if destination == source:
                    unchanged += 1
                    continue

                operation = "move"
                existing_source = planned_sources.get(destination)
                if destination.exists():
                    if _same_bytes(source, destination):
                        operation = "deduplicate"
                    else:
                        destination = _conflict_path(profile_dir, destination.name, claimed)
                        operation = "conflict"
                elif existing_source is not None:
                    if _same_bytes(source, existing_source):
                        operation = "deduplicate"
                    else:
                        destination = _conflict_path(profile_dir, destination.name, claimed)
                        operation = "conflict"

                claimed.add(destination)
                if operation != "deduplicate":
                    planned_sources[destination] = source
                operations.append(
                    {
                        "operation": operation,
                        "reason": reason,
                        "source": str(source),
                        "destination": str(destination),
                    }
                )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "apply": apply,
        "output_root": str(output_root),
        "operations": operations,
        "os_metadata": metadata_files,
        "unchanged_file_count": unchanged,
    }


def _rewrite_links(text: str, *, source: Path, destination: Path, moves: dict[Path, Path]) -> str:
    def replace(match: re.Match[str]) -> str:
        target = match.group("target")
        if "://" in target or target.startswith(("/", "#", "mailto:")):
            return match.group(0)
        old_target = (source.parent / target).resolve()
        new_target = moves.get(old_target)
        if new_target is None:
            return match.group(0)
        relative = Path(os.path.relpath(new_target, start=destination.parent)).as_posix()
        return f"{match.group('prefix')}{relative}{match.group('suffix')}"

    return HTML_LINK_RE.sub(replace, MARKDOWN_LINK_RE.sub(replace, text))


def apply_migration_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    operations = manifest["operations"]
    moves = {
        Path(item["source"]).resolve(): Path(item["destination"]).resolve()
        for item in operations
        if item["operation"] in {"move", "conflict", "deduplicate"}
    }

    for metadata_path in manifest["os_metadata"]:
        path = Path(metadata_path)
        if path.exists():
            path.unlink()

    for item in operations:
        source = Path(item["source"])
        destination = Path(item["destination"])
        if not source.exists():
            continue
        if item["operation"] == "deduplicate":
            source.unlink()
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(destination))

    rewritten: list[str] = []
    for old_source, destination in moves.items():
        if destination.suffix.casefold() not in {".md", ".html"} or not destination.exists():
            continue
        original = destination.read_text(encoding="utf-8", errors="ignore")
        updated = _rewrite_links(
            original,
            source=old_source,
            destination=destination,
            moves=moves,
        )
        if updated != original:
            destination.write_text(updated, encoding="utf-8")
            rewritten.append(str(destination))

    output_root = Path(manifest["output_root"])
    if output_root.is_dir():
        directories = sorted(
            (path for path in output_root.rglob("*") if path.is_dir()),
            key=lambda path: len(path.parts),
            reverse=True,
        )
        for directory in directories:
            try:
                directory.rmdir()
            except OSError:
                pass

    manifest["rewritten_links"] = rewritten
    return manifest


def migrate_output_layout(repo_root: Path, *, apply: bool) -> dict[str, Any]:
    manifest = build_migration_manifest(repo_root, apply=apply)
    if apply:
        manifest = apply_migration_manifest(manifest)
    manifest_path = state_path(repo_root, "output-layout-migration.json")
    write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest
