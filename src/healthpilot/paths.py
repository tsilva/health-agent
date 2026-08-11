"""Filesystem helpers for repo-local state, reports, and profile discovery."""

from __future__ import annotations

import re
from pathlib import Path


REPORT_BUCKETS = (
    "what-next",
    "root-cause",
    "treatment-record",
    "organ-system-health",
    "mortality-risk",
    "doctor-appointment",
    "profile-interview",
    "daily-plan",
)

REPORT_TYPE_BUCKETS = {
    "what-next": "what-next",
    "root-cause": "root-cause",
    "treatment-record": "treatment-record",
    "organ-system-health": "organ-system-health",
    "mortality-risk": "mortality-risk",
}

_ARTIFACT_BUCKET_PATTERNS = (
    ("root-cause", ("root-cause",)),
    ("treatment-record", ("treatment-record", "medication-history")),
    ("organ-system-health", ("organ-system-health",)),
    ("mortality-risk", ("mortality-risk", "cause-of-death-risk")),
    ("doctor-appointment", ("appointment-",)),
    ("profile-interview", ("health-log-entry", "future-questions")),
    ("daily-plan", ("daily-plan",)),
    ("what-next", ("action-plan", "what-next", "energy-action-plan")),
)

_DATE_PREFIX_RE = re.compile(r"^(?P<date>\d{4}-\d{2}-\d{2})-")


def expand_home(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def repo_path(repo_root: Path, *parts: str) -> Path:
    return repo_root.joinpath(*parts)


def state_path(repo_root: Path, *parts: str) -> Path:
    return repo_path(repo_root, ".state", *parts)


def profiles_state_path(repo_root: Path, profile_slug: str, *parts: str) -> Path:
    return state_path(repo_root, "profiles", profile_slug, *parts)


def output_path(repo_root: Path, *parts: str) -> Path:
    return repo_path(repo_root, ".output", *parts)


def profile_output_path(repo_root: Path, profile_slug: str, *parts: str) -> Path:
    """Return a legacy profile-level output path.

    New report writers should use :func:`report_output_path`. This helper stays
    available while existing flat paths remain readable.
    """
    return output_path(repo_root, profile_slug, *parts)


def report_output_path(
    repo_root: Path,
    profile_slug: str,
    report_bucket: str,
    *parts: str,
) -> Path:
    if report_bucket not in REPORT_BUCKETS:
        allowed = ", ".join(REPORT_BUCKETS)
        raise ValueError(f"Unknown report bucket {report_bucket!r}; expected one of: {allowed}")
    return output_path(repo_root, profile_slug, report_bucket, *parts)


def report_companion_path(
    repo_root: Path,
    profile_slug: str,
    report_bucket: str,
    *,
    report_date: str,
    artifact_slug: str,
    filename: str,
    companion_count: int,
) -> Path:
    """Return the canonical location for a report companion artifact."""
    if companion_count < 1:
        raise ValueError("companion_count must be at least 1")
    dated_filename = filename if filename.startswith(f"{report_date}-") else f"{report_date}-{filename}"
    if companion_count >= 4:
        return report_output_path(
            repo_root,
            profile_slug,
            report_bucket,
            "assets",
            f"{report_date}-{artifact_slug}",
            dated_filename,
        )
    return report_output_path(
        repo_root,
        profile_slug,
        report_bucket,
        dated_filename,
    )


def classify_report_bucket(filename: str) -> str | None:
    """Classify a report artifact from its filename using the canonical registry."""
    normalized = filename.casefold().replace("_", "-")
    for bucket, markers in _ARTIFACT_BUCKET_PATTERNS:
        if any(marker in normalized for marker in markers):
            return bucket
    return None


def find_previous_report(
    repo_root: Path,
    profile_slug: str,
    report_bucket: str,
    artifact_name: str,
    *,
    before_date: str | None = None,
) -> Path | None:
    """Find the newest earlier report, preferring the bucketed layout.

    ``artifact_name`` is the filename portion after
    ``YYYY-MM-DD-{profile_slug}-``. Flat profile paths are a temporary read-only
    compatibility fallback.
    """
    candidates: list[tuple[str, Path]] = []
    roots = (
        report_output_path(repo_root, profile_slug, report_bucket),
        profile_output_path(repo_root, profile_slug),
    )
    expected_tail = f"-{profile_slug}-{artifact_name}"
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.glob(f"????-??-??-{profile_slug}-{artifact_name}"):
            match = _DATE_PREFIX_RE.match(path.name)
            if not match or not path.is_file() or not path.name.endswith(expected_tail):
                continue
            report_date = match.group("date")
            if before_date is not None and report_date >= before_date:
                continue
            candidates.append((report_date, path))
        if candidates:
            break
    return max(candidates, key=lambda item: (item[0], item[1].name))[1] if candidates else None


def profiles_dir(home_dir: Path) -> Path:
    return home_dir.joinpath(".config", "healthpilot", "profiles")


def ensure_repo_dirs(repo_root: Path, profile_slug: str) -> None:
    profiles_state_path(repo_root, profile_slug).mkdir(parents=True, exist_ok=True)
    output_path(repo_root, profile_slug).mkdir(parents=True, exist_ok=True)
