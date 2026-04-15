"""CLI for the local unresolved-issue workflow."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Any

from health_agent.actions import build_action_queue_payload, render_review_report
from health_agent.issues import (
    ValidationError,
    load_issue_collection,
    load_issue_file,
    merge_issue_payloads,
    save_issue,
    validate_outcome_update,
)
from health_agent.jsonio import load_json, write_json
from health_agent.paths import ensure_repo_dirs, output_path, state_path
from health_agent.profile import load_profile_context


def _utc_now() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _read_issue_dir(repo_root: Path, *, profile_slug: str) -> dict[str, dict[str, Any]]:
    issues_dir = state_path(repo_root, "issues")
    issues: dict[str, dict[str, Any]] = {}
    if not issues_dir.exists():
        return issues
    for issue_file in sorted(issues_dir.glob("*.json")):
        issue = load_issue_file(issue_file)
        if issue.payload["profile_slug"] != profile_slug:
            continue
        issues[issue.slug] = issue.payload
    return issues


def _write_profile_cache(repo_root: Path, profile_context: Any, generated_at: str) -> Path:
    cache_payload = dict(profile_context.cache_payload)
    cache_payload["refreshed_at"] = generated_at
    cache_path = state_path(repo_root, "profile-cache", f"{profile_context.slug}.json")
    write_json(cache_path, cache_payload)
    return cache_path


def _write_action_queue_and_report(
    *,
    repo_root: Path,
    profile_context: Any,
    generated_at: str,
    issues: dict[str, dict[str, Any]],
) -> tuple[Path, Path]:
    action_queue = build_action_queue_payload(
        profile_slug=profile_context.slug,
        profile_name=profile_context.cache_payload["profile_name"],
        generated_at=generated_at,
        issues=issues,
    )
    action_queue_path = state_path(repo_root, "action-queue.json")
    write_json(action_queue_path, action_queue)

    report_body = render_review_report(
        profile_slug=profile_context.slug,
        profile_name=profile_context.cache_payload["profile_name"],
        generated_at=generated_at,
        source_status=profile_context.cache_payload["sources"],
        issues=issues,
        action_queue=action_queue,
    )
    report_name = f"{profile_context.slug}-action-plan-{generated_at[:10]}.md"
    report_path = output_path(repo_root, report_name)
    report_path.write_text(report_body, encoding="utf-8")
    return action_queue_path, report_path


def _sync_issue_inputs(repo_root: Path, source_path: Path, *, profile_slug: str) -> None:
    issues_dir = state_path(repo_root, "issues")
    for issue_file in load_issue_collection(source_path):
        payload = dict(issue_file.payload)
        payload["profile_slug"] = payload.get("profile_slug", profile_slug)
        save_issue(issues_dir.joinpath(f"{issue_file.slug}.json"), payload)


def run_intake(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    ensure_repo_dirs(repo_root)
    profile_context = load_profile_context(args.profile, home_dir=args.home_dir)
    generated_at = _utc_now()
    _write_profile_cache(repo_root, profile_context, generated_at)
    if args.issues_from:
        _sync_issue_inputs(
            repo_root,
            args.issues_from.resolve(),
            profile_slug=profile_context.slug,
        )
    issues = _read_issue_dir(repo_root, profile_slug=profile_context.slug)
    _write_action_queue_and_report(
        repo_root=repo_root,
        profile_context=profile_context,
        generated_at=generated_at,
        issues=issues,
    )
    return 0


def run_review(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    ensure_repo_dirs(repo_root)
    profile_context = load_profile_context(args.profile, home_dir=args.home_dir)
    generated_at = _utc_now()
    _write_profile_cache(repo_root, profile_context, generated_at)
    issues = _read_issue_dir(repo_root, profile_slug=profile_context.slug)
    _write_action_queue_and_report(
        repo_root=repo_root,
        profile_context=profile_context,
        generated_at=generated_at,
        issues=issues,
    )
    return 0


def run_outcome_update(args: argparse.Namespace) -> int:
    repo_root = args.repo_root.resolve()
    ensure_repo_dirs(repo_root)
    profile_context = load_profile_context(args.profile, home_dir=args.home_dir)
    generated_at = _utc_now()
    _write_profile_cache(repo_root, profile_context, generated_at)

    update_payload = validate_outcome_update(load_json(args.update_file.resolve()))
    update_filename = f"{update_payload['date']}-{update_payload['issue_slug']}.json"
    update_path = state_path(repo_root, "outcome-updates", update_filename)
    write_json(update_path, update_payload)

    issue_path = state_path(repo_root, "issues", f"{update_payload['issue_slug']}.json")
    if issue_path.exists():
        existing_issue = load_issue_file(issue_path).payload
        revised_issue = existing_issue
        if args.revised_issue:
            revised_issue = load_issue_file(args.revised_issue.resolve()).payload
        merged_issue = merge_issue_payloads(
            existing_issue,
            revised_issue,
            update_reference=str(update_path),
        )
        merged_issue["last_reviewed_at"] = generated_at
        merged_issue["linked_sources"] = list(
            dict.fromkeys(
                merged_issue["linked_sources"]
                + update_payload["attachments_or_source_refs"]
            )
        )
        merged_issue["profile_slug"] = profile_context.slug
        save_issue(issue_path, merged_issue)

    issues = _read_issue_dir(repo_root, profile_slug=profile_context.slug)
    _write_action_queue_and_report(
        repo_root=repo_root,
        profile_context=profile_context,
        generated_at=generated_at,
        issues=issues,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="health-agent",
        description="Local state and action-plan workflow for unresolved health issues.",
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

    intake = subparsers.add_parser(
        "intake",
        help="Refresh the selected profile cache, sync issue drafts into .state/issues, and render the action plan.",
    )
    intake.add_argument("--profile", required=True, help="Profile name or absolute YAML path.")
    intake.add_argument(
        "--issues-from",
        type=Path,
        help="Optional file or directory of issue JSON drafts to sync into .state/issues.",
    )
    intake.set_defaults(func=run_intake)

    review = subparsers.add_parser(
        "review",
        help="Refresh the profile cache, rebuild the action queue, and render the action plan from existing issue files.",
    )
    review.add_argument("--profile", required=True, help="Profile name or absolute YAML path.")
    review.set_defaults(func=run_review)

    outcome = subparsers.add_parser(
        "outcome-update",
        help="Archive a structured outcome update, optionally merge a revised issue record, then rerender the action plan.",
    )
    outcome.add_argument("--profile", required=True, help="Profile name or absolute YAML path.")
    outcome.add_argument("--update-file", type=Path, required=True, help="OutcomeUpdate JSON file.")
    outcome.add_argument(
        "--revised-issue",
        type=Path,
        help="Optional revised IssueRecord JSON file for the same issue slug.",
    )
    outcome.set_defaults(func=run_outcome_update)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, ValidationError) as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
