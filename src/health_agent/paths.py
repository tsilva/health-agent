"""Filesystem helpers for repo-local state and runtime profile discovery."""

from __future__ import annotations

from pathlib import Path


def expand_home(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def repo_path(repo_root: Path, *parts: str) -> Path:
    return repo_root.joinpath(*parts)


def state_path(repo_root: Path, *parts: str) -> Path:
    return repo_path(repo_root, ".state", *parts)


def output_path(repo_root: Path, *parts: str) -> Path:
    return repo_path(repo_root, ".output", *parts)


def profiles_dir(home_dir: Path) -> Path:
    return home_dir.joinpath(".config", "health-agent", "profiles")


def ensure_repo_dirs(repo_root: Path) -> None:
    state_path(repo_root, "issues").mkdir(parents=True, exist_ok=True)
    state_path(repo_root, "profile-cache").mkdir(parents=True, exist_ok=True)
    state_path(repo_root, "outcome-updates").mkdir(parents=True, exist_ok=True)
    output_path(repo_root).mkdir(parents=True, exist_ok=True)
