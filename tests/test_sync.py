from __future__ import annotations

import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC_SCRIPT = REPO_ROOT / "sync.sh"
PARSERS = ("parselabs", "parsemedicalexams", "parsehealthlog")


def _write_fake_parsers(bin_dir: Path) -> None:
    bin_dir.mkdir()
    for parser in PARSERS:
        parser_path = bin_dir / parser
        parser_path.write_text(
            '#!/usr/bin/env bash\nprintf "%s %s\\n" "$(basename "$0")" "$*" >> "$SYNC_LOG"\n'
        )
        parser_path.chmod(0o755)


def _run_sync(tmp_path: Path, *args: str) -> tuple[subprocess.CompletedProcess[str], Path]:
    bin_dir = tmp_path / "bin"
    profile_dir = tmp_path / "profiles"
    sync_log = tmp_path / "sync.log"
    _write_fake_parsers(bin_dir)
    profile_dir.mkdir()

    env = os.environ.copy()
    env.update(
        {
            "HEALTHPILOT_PROFILE_DIR": str(profile_dir),
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "SYNC_LOG": str(sync_log),
        }
    )
    result = subprocess.run(
        [str(SYNC_SCRIPT), *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    return result, sync_log


def test_sync_without_profile_runs_every_parser_for_every_live_profile(
    tmp_path: Path,
) -> None:
    profile_dir = tmp_path / "profiles"
    profile_dir.mkdir(parents=True)
    (profile_dir / "beta.yaml").touch()
    (profile_dir / "alpha.yaml").touch()

    bin_dir = tmp_path / "bin"
    sync_log = tmp_path / "sync.log"
    _write_fake_parsers(bin_dir)
    env = os.environ.copy()
    env.update(
        {
            "HEALTHPILOT_PROFILE_DIR": str(profile_dir),
            "PATH": f"{bin_dir}{os.pathsep}{env['PATH']}",
            "SYNC_LOG": str(sync_log),
        }
    )

    result = subprocess.run(
        [str(SYNC_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert sync_log.read_text().splitlines() == [
        "parselabs --profile alpha",
        "parselabs --profile beta",
        "parsemedicalexams --profile alpha",
        "parsemedicalexams --profile beta",
        "parsehealthlog --profile alpha",
        "parsehealthlog --profile beta",
    ]


def test_sync_with_profile_only_runs_requested_profile(tmp_path: Path) -> None:
    result, sync_log = _run_sync(tmp_path, "--profile", "beta")

    assert result.returncode == 0, result.stderr
    assert sync_log.read_text().splitlines() == [
        "parselabs --profile beta",
        "parsemedicalexams --profile beta",
        "parsehealthlog --profile beta",
    ]


def test_sync_without_live_profiles_fails_clearly(tmp_path: Path) -> None:
    result, sync_log = _run_sync(tmp_path)

    assert result.returncode == 1
    assert "no live profiles found" in result.stderr
    assert not sync_log.exists()
