"""CLI for the rescan-driven health-agent planning workflow."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from health_agent.actions import build_action_queue_payload, render_plan_report
from health_agent.evidence import build_evidence_snapshot
from health_agent.issues import (
    ValidationError,
    load_issue_collection,
    load_issue_store,
    save_issue_store,
)
from health_agent.jsonio import write_json
from health_agent.paths import (
    ensure_repo_dirs,
    profile_output_path,
    profiles_state_path,
    state_path,
)
from health_agent.profile import load_profile_context


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _read_legacy_issue_dir(repo_root: Path, *, profile_slug: str) -> dict[str, dict[str, Any]]:
    legacy_dir = state_path(repo_root, "issues")
    if not legacy_dir.exists():
        return {}

    issues: dict[str, dict[str, Any]] = {}
    for issue_file in load_issue_collection(legacy_dir):
        if issue_file.payload["profile_slug"] != profile_slug:
            continue
        issues[issue_file.slug] = issue_file.payload
    return issues


def _load_profile_issues(repo_root: Path, *, profile_slug: str) -> dict[str, dict[str, Any]]:
    issues_path = profiles_state_path(repo_root, profile_slug, "issues.json")
    issues = load_issue_store(issues_path)
    if issues:
        return issues
    return _read_legacy_issue_dir(repo_root, profile_slug=profile_slug)


def _write_profile_state(
    *,
    repo_root: Path,
    profile_context: Any,
    generated_at: str,
    evidence_snapshot: dict[str, Any],
    issues: dict[str, dict[str, Any]],
) -> tuple[Path, Path]:
    actions_payload = build_action_queue_payload(
        profile_slug=profile_context.slug,
        profile_name=profile_context.cache_payload["profile_name"],
        generated_at=generated_at,
        issues=issues,
    )
    profile_state_dir = profiles_state_path(repo_root, profile_context.slug)
    sources_path = profile_state_dir / "sources.json"
    issues_path = profile_state_dir / "issues.json"
    actions_path = profile_state_dir / "actions.json"

    write_json(sources_path, evidence_snapshot)
    save_issue_store(
        issues_path,
        profile_slug=profile_context.slug,
        profile_name=profile_context.cache_payload["profile_name"],
        generated_at=generated_at,
        issues=issues,
    )
    write_json(actions_path, actions_payload)

    report_body = render_plan_report(
        profile_slug=profile_context.slug,
        profile_name=profile_context.cache_payload["profile_name"],
        generated_at=generated_at,
        evidence_snapshot=evidence_snapshot,
        issues=issues,
        action_queue=actions_payload,
    )
    report_name = f"{generated_at[:10]}-{profile_context.slug}-action-plan.md"
    report_path = profile_output_path(repo_root, profile_context.slug, report_name)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_body, encoding="utf-8")
    return actions_path, report_path


def _sync_issue_inputs(
    repo_root: Path,
    source_path: Path,
    *,
    profile_slug: str,
    profile_name: str,
    generated_at: str,
) -> dict[str, dict[str, Any]]:
    issues = _load_profile_issues(repo_root, profile_slug=profile_slug)
    for issue_file in load_issue_collection(source_path):
        payload = dict(issue_file.payload)
        payload["profile_slug"] = profile_slug
        issues[issue_file.slug] = payload

    save_issue_store(
        profiles_state_path(repo_root, profile_slug, "issues.json"),
        profile_slug=profile_slug,
        profile_name=profile_name,
        generated_at=generated_at,
        issues=issues,
    )
    return issues


def run_plan(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    profile_context = load_profile_context(args.profile, home_dir=args.home_dir)
    ensure_repo_dirs(repo_root, profile_context.slug)
    generated_at = _utc_now()
    evidence_snapshot = build_evidence_snapshot(profile_context, generated_at=generated_at)

    issues = _load_profile_issues(repo_root, profile_slug=profile_context.slug)
    if args.issues_from:
        issues = _sync_issue_inputs(
            repo_root,
            args.issues_from.resolve(),
            profile_slug=profile_context.slug,
            profile_name=profile_context.cache_payload["profile_name"],
            generated_at=generated_at,
        )
    _write_profile_state(
        repo_root=repo_root,
        profile_context=profile_context,
        generated_at=generated_at,
        evidence_snapshot=evidence_snapshot,
        issues=issues,
    )
    return 0


def _run_deprecated_alias(args: argparse.Namespace, alias: str) -> int:
    message = (
        f"warning: `health-agent {alias}` is deprecated; use "
        f"`health-agent plan --profile {args.profile}`.\n"
    )
    print(message, end="")
    return run_plan(args)


def run_intake(args: argparse.Namespace) -> int:
    return _run_deprecated_alias(args, "intake")


def run_review(args: argparse.Namespace) -> int:
    return _run_deprecated_alias(args, "review")


def run_outcome_update(args: argparse.Namespace) -> int:
    if args.update_file or args.revised_issue:
        print(
            "warning: manual outcome update files are deprecated; rescan the parsed sources and rerun `health-agent plan`.\n",
            end="",
        )
    return _run_deprecated_alias(args, "outcome-update")


def _add_profile_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--profile", required=True, help="Profile name or absolute YAML path.")


def _add_optional_issues_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--issues-from",
        type=Path,
        help="Deprecated compatibility input for issue JSON drafts; imported into the per-profile issue store before planning.",
    )


def _add_deprecated_outcome_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--update-file",
        type=Path,
        help="Deprecated compatibility argument. Parsed source folders are now the canonical input.",
    )
    parser.add_argument(
        "--revised-issue",
        type=Path,
        help="Deprecated compatibility argument. Parsed source folders are now the canonical input.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="health-agent",
        description="Rescan parsed health data sources and render the current action plan.",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root where .state/ and .output/ live.",
    )
    parser.add_argument(
        "--home-dir",
        type=Path,
        default=Path.home(),
        help="Home directory used to resolve ~/.config/health-agent profiles.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser(
        "plan",
        help="Rescan parsed source folders, refresh per-profile state, and render the current action plan.",
    )
    _add_profile_argument(plan)
    _add_optional_issues_argument(plan)
    plan.set_defaults(func=run_plan)

    intake = subparsers.add_parser(
        "intake",
        help="Deprecated alias for `plan`.",
    )
    _add_profile_argument(intake)
    _add_optional_issues_argument(intake)
    intake.set_defaults(func=run_intake)

    review = subparsers.add_parser(
        "review",
        help="Deprecated alias for `plan`.",
    )
    _add_profile_argument(review)
    _add_optional_issues_argument(review)
    review.set_defaults(func=run_review)

    outcome = subparsers.add_parser(
        "outcome-update",
        help="Deprecated alias for `plan`. Parsed source folders are now the canonical input.",
    )
    _add_profile_argument(outcome)
    _add_optional_issues_argument(outcome)
    _add_deprecated_outcome_arguments(outcome)
    outcome.set_defaults(func=run_outcome_update)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValidationError) as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
