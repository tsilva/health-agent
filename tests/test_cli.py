from __future__ import annotations

import json
from pathlib import Path

from health_agent.cli import main


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_profile(home_dir: Path, *, missing_exams: bool = False) -> None:
    config_dir = home_dir / ".config" / "health-agent" / "profiles"
    config_dir.mkdir(parents=True, exist_ok=True)

    labs_dir = home_dir / "data" / "labs"
    labs_dir.mkdir(parents=True, exist_ok=True)
    (labs_dir / "all.csv").write_text("date,lab_name,value\n", encoding="utf-8")

    health_log_dir = home_dir / "data" / "health-log"
    health_log_dir.mkdir(parents=True, exist_ok=True)
    (health_log_dir / "health_log.md").write_text("# health log\n", encoding="utf-8")

    genetics_file = home_dir / "data" / "23andme.txt"
    genetics_file.parent.mkdir(parents=True, exist_ok=True)
    genetics_file.write_text("# raw 23andme export\n", encoding="utf-8")

    exams_dir = home_dir / "data" / "exams"
    if not missing_exams:
        exams_dir.mkdir(parents=True, exist_ok=True)
        (exams_dir / "summary.md").write_text("# exam summary\n", encoding="utf-8")

    profile = f"""
name: "Test User"
demographics:
  date_of_birth: "1990-01-15"
  gender: "female"

data_sources:
  labs_path: "{labs_dir}"
  exams_path: "{exams_dir}"
  health_log_path: "{health_log_dir}"
  genetics_23andme_path: "{genetics_file}"
"""
    (config_dir / "test-user.yaml").write_text(profile.strip() + "\n", encoding="utf-8")


def _issue_payload(
    *,
    profile_slug: str = "test-user",
    title: str,
    confidence_frame: str,
    next_best_action: str,
    why: str,
    status: str = "active",
    priority_context: dict | None = None,
) -> dict:
    return {
        "profile_slug": profile_slug,
        "title": title,
        "status": status,
        "working_conclusion": "Working conclusion for test coverage.",
        "confidence_frame": confidence_frame,
        "supporting_evidence": ["Supporting evidence"],
        "contradicting_evidence": ["Contradicting evidence"],
        "next_best_action": next_best_action,
        "why_this_action_now": why,
        "specialist_type": "hematology",
        "tests_or_discussions_to_request": ["Discuss a targeted next test"],
        "result_that_would_change_plan": "Return with the new result so the plan can be updated.",
        "last_reviewed_at": "2026-04-15T00:00:00Z",
        "linked_sources": ["/tmp/source.md"],
        "priority_context": priority_context
        or {
            "materially_narrows_differential": False,
            "changes_treatment_or_specialist_path": False,
            "resolves_missing_objective_evidence": False,
            "reduces_risk_if_delayed": False,
            "is_lower_value_optimization": False,
        },
        "recent_updates": [],
    }


def test_intake_creates_state_and_action_plan(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    drafts_dir = tmp_path / "drafts"
    _write_json(
        drafts_dir / "issue-a.json",
        _issue_payload(
            title="Issue A",
            confidence_frame="differential",
            next_best_action="Book a targeted hematology visit.",
            why="This materially narrows the differential.",
        ),
    )
    _write_json(
        drafts_dir / "issue-b.json",
        _issue_payload(
            title="Issue B",
            confidence_frame="likely diagnosis",
            next_best_action="Repeat ferritin and CBC.",
            why="This closes a missing evidence gap.",
            priority_context={
                "materially_narrows_differential": False,
                "changes_treatment_or_specialist_path": False,
                "resolves_missing_objective_evidence": True,
                "reduces_risk_if_delayed": False,
                "is_lower_value_optimization": False,
            },
        ),
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "intake",
            "--profile",
            "test-user",
            "--issues-from",
            str(drafts_dir),
        ]
    )

    assert exit_code == 0
    assert (repo_root / ".state" / "issues" / "issue-a.json").exists()
    assert (repo_root / ".state" / "profile-cache" / "test-user.json").exists()
    action_queue = json.loads((repo_root / ".state" / "action-queue.json").read_text())
    assert action_queue["actions"][0]["issue_slug"] == "issue-a"
    report = next((repo_root / ".output").glob("test-user-action-plan-*.md"))
    report_text = report.read_text(encoding="utf-8")
    assert "Top 3 Ranked Actions" in report_text
    assert "Do next: Book a targeted hematology visit." in report_text


def test_review_reports_missing_sources(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir, missing_exams=True)

    issue_path = repo_root / ".state" / "issues" / "issue-a.json"
    _write_json(
        issue_path,
        _issue_payload(
            title="Issue A",
            confidence_frame="open question",
            next_best_action="Order confirmatory testing.",
            why="This is still unresolved.",
        ),
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "review",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    report = next((repo_root / ".output").glob("test-user-action-plan-*.md"))
    report_text = report.read_text(encoding="utf-8")
    assert "`exams_path`: missing" in report_text


def test_outcome_update_merges_evidence_and_reorders_queue(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    issues_dir = repo_root / ".state" / "issues"
    _write_json(
        issues_dir / "issue-a.json",
        _issue_payload(
            title="Issue A",
            confidence_frame="differential",
            next_best_action="Book a targeted hematology visit.",
            why="This materially narrows the differential.",
        ),
    )
    _write_json(
        issues_dir / "issue-b.json",
        _issue_payload(
            title="Issue B",
            confidence_frame="likely diagnosis",
            next_best_action="Repeat ferritin and CBC.",
            why="This closes a missing evidence gap.",
            priority_context={
                "materially_narrows_differential": False,
                "changes_treatment_or_specialist_path": False,
                "resolves_missing_objective_evidence": True,
                "reduces_risk_if_delayed": False,
                "is_lower_value_optimization": False,
            },
        ),
    )

    update_file = tmp_path / "outcome.json"
    _write_json(
        update_file,
        {
            "issue_slug": "issue-a",
            "event_type": "visit",
            "summary": "Hematology resolved the issue after confirmatory testing.",
            "date": "2026-04-15",
            "attachments_or_source_refs": ["/tmp/visit-note.md"],
        },
    )
    revised_issue = tmp_path / "issue-a-revised.json"
    _write_json(
        revised_issue,
        _issue_payload(
            title="Issue A",
            confidence_frame="clear conclusion",
            next_best_action="No further diagnostic workup needed.",
            why="The confirmatory testing closed the loop.",
            status="resolved",
            priority_context={
                "materially_narrows_differential": False,
                "changes_treatment_or_specialist_path": False,
                "resolves_missing_objective_evidence": False,
                "reduces_risk_if_delayed": False,
                "is_lower_value_optimization": True,
            },
        ),
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "outcome-update",
            "--profile",
            "test-user",
            "--update-file",
            str(update_file),
            "--revised-issue",
            str(revised_issue),
        ]
    )

    assert exit_code == 0
    updated_issue = json.loads((issues_dir / "issue-a.json").read_text())
    assert "/tmp/source.md" in updated_issue["linked_sources"]
    assert "/tmp/visit-note.md" in updated_issue["linked_sources"]
    assert updated_issue["status"] == "resolved"

    action_queue = json.loads((repo_root / ".state" / "action-queue.json").read_text())
    assert action_queue["actions"][0]["issue_slug"] == "issue-b"
    report = next((repo_root / ".output").glob("test-user-action-plan-*.md"))
    assert "Issue B (`issue-b`)" in report.read_text(encoding="utf-8")


def test_review_dedupes_duplicate_actions(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    issues_dir = repo_root / ".state" / "issues"
    shared_action = "Book a targeted hematology visit."
    _write_json(
        issues_dir / "issue-a.json",
        _issue_payload(
            title="Issue A",
            confidence_frame="differential",
            next_best_action=shared_action,
            why="This materially narrows the differential.",
        ),
    )
    _write_json(
        issues_dir / "issue-b.json",
        _issue_payload(
            title="Issue B",
            confidence_frame="open question",
            next_best_action=shared_action,
            why="This is still the best next step.",
        ),
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "review",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    action_queue = json.loads((repo_root / ".state" / "action-queue.json").read_text())
    assert len(action_queue["actions"]) == 1
    assert sorted(action_queue["actions"][0]["related_issues"]) == ["issue-a", "issue-b"]
