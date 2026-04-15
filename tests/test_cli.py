from __future__ import annotations

import json
from pathlib import Path

from health_agent.cli import main


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_profile(
    home_dir: Path,
    *,
    slug: str = "test-user",
    display_name: str = "Test User",
    missing_exams: bool = False,
) -> dict[str, Path]:
    config_dir = home_dir / ".config" / "health-agent" / "profiles"
    config_dir.mkdir(parents=True, exist_ok=True)

    profile_root = home_dir / "data" / slug

    labs_dir = profile_root / "labs"
    labs_dir.mkdir(parents=True, exist_ok=True)
    (labs_dir / "all.csv").write_text(
        "\n".join(
            [
                "date,lab_name,value,lab_unit,is_above_limit,is_below_limit,review_needed",
                "2026-04-10,Ferritin,18,ng/mL,false,true,false",
                "2026-04-12,Hemoglobin,11.6,g/dL,false,true,true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    health_log_dir = profile_root / "health-log"
    entries_dir = health_log_dir / "entries"
    entries_dir.mkdir(parents=True, exist_ok=True)
    (health_log_dir / "health_log.md").write_text(
        "# Health log overview\nRecent fatigue and follow-up labs.\n",
        encoding="utf-8",
    )
    (entries_dir / "2026-04-12.processed.md").write_text(
        "Processed summary for 2026-04-12.\n",
        encoding="utf-8",
    )

    genetics_file = profile_root / "23andme.txt"
    genetics_file.parent.mkdir(parents=True, exist_ok=True)
    genetics_file.write_text(
        "# raw 23andme export\nrs123\t1\t12345\tAA\nrs456\t2\t54321\tGG\n",
        encoding="utf-8",
    )

    exams_dir = profile_root / "exams"
    if not missing_exams:
        exams_dir.mkdir(parents=True, exist_ok=True)
        (exams_dir / "summary.md").write_text("# exam summary\n", encoding="utf-8")

    profile = f"""
name: "{display_name}"
demographics:
  date_of_birth: "1990-01-15"
  gender: "female"

data_sources:
  labs_path: "{labs_dir}"
  exams_path: "{exams_dir}"
  health_log_path: "{health_log_dir}"
  genetics_23andme_path: "{genetics_file}"
"""
    (config_dir / f"{slug}.yaml").write_text(profile.strip() + "\n", encoding="utf-8")
    return {
        "labs_dir": labs_dir,
        "exams_dir": exams_dir,
        "health_log_dir": health_log_dir,
        "entries_dir": entries_dir,
        "genetics_file": genetics_file,
    }


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


def _write_issue_store(
    repo_root: Path,
    *,
    profile_slug: str,
    profile_name: str = "Test User",
    issues: dict[str, dict],
) -> None:
    _write_json(
        repo_root / ".state" / "profiles" / profile_slug / "issues.json",
        {
            "profile_slug": profile_slug,
            "profile_name": profile_name,
            "generated_at": "2026-04-15T00:00:00Z",
            "issues": [{"slug": slug, **payload} for slug, payload in issues.items()],
        },
    )


def test_plan_creates_per_profile_state_and_report_on_first_run(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    profile_state_dir = repo_root / ".state" / "profiles" / "test-user"
    assert (profile_state_dir / "sources.json").exists()
    assert (profile_state_dir / "issues.json").exists()
    assert (profile_state_dir / "actions.json").exists()

    sources = json.loads((profile_state_dir / "sources.json").read_text())
    assert (
        sources["sources"]["health_log_path"]["details"]["recent_processed_entries"]
        == ["2026-04-12.processed.md"]
    )
    actions = json.loads((profile_state_dir / "actions.json").read_text())
    assert actions["actions"] == []

    report = next((repo_root / ".output" / "test-user").glob("????-??-??-test-user-action-plan.md"))
    report_text = report.read_text(encoding="utf-8")
    assert "Current Evidence Snapshot" in report_text
    assert "No active actions. All tracked issues are resolved or parked." in report_text


def test_plan_uses_profile_issue_store_and_dedupes_actions(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    shared_action = "Book a targeted hematology visit."
    _write_issue_store(
        repo_root,
        profile_slug="test-user",
        issues={
            "issue-a": _issue_payload(
                title="Issue A",
                confidence_frame="differential",
                next_best_action=shared_action,
                why="This materially narrows the differential.",
            ),
            "issue-b": _issue_payload(
                title="Issue B",
                confidence_frame="open question",
                next_best_action=shared_action,
                why="This is still the best next step.",
            ),
        },
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    actions = json.loads((repo_root / ".state" / "profiles" / "test-user" / "actions.json").read_text())
    assert len(actions["actions"]) == 1
    assert sorted(actions["actions"][0]["related_issues"]) == ["issue-a", "issue-b"]


def test_plan_reports_missing_sources(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir, missing_exams=True)

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    report = next((repo_root / ".output" / "test-user").glob("????-??-??-test-user-action-plan.md"))
    report_text = report.read_text(encoding="utf-8")
    assert "`exams_path`: missing" in report_text


def test_plan_rescans_updated_sources(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    paths = _write_profile(home_dir)

    first_exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "test-user",
        ]
    )
    assert first_exit_code == 0

    (paths["entries_dir"] / "2026-04-15.processed.md").write_text(
        "Processed summary for 2026-04-15.\n",
        encoding="utf-8",
    )
    (paths["labs_dir"] / "all.csv").write_text(
        "\n".join(
            [
                "date,lab_name,value,lab_unit,is_above_limit,is_below_limit,review_needed",
                "2026-04-10,Ferritin,18,ng/mL,false,true,false",
                "2026-04-12,Hemoglobin,11.6,g/dL,false,true,true",
                "2026-04-15,CRP,9.1,mg/L,true,false,true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    second_exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "test-user",
        ]
    )
    assert second_exit_code == 0

    sources = json.loads((repo_root / ".state" / "profiles" / "test-user" / "sources.json").read_text())
    assert "2026-04-15.processed.md" in sources["sources"]["health_log_path"]["details"]["recent_processed_entries"]
    flagged = sources["sources"]["labs_path"]["details"]["recent_abnormal_results"]
    assert any(item["label"] == "CRP" for item in flagged)


def test_plan_migrates_legacy_flat_issue_state_per_profile(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir, slug="alpha", display_name="Alpha User")
    _write_profile(home_dir, slug="beta", display_name="Beta User")

    _write_json(
        repo_root / ".state" / "issues" / "alpha-issue.json",
        _issue_payload(
            profile_slug="alpha",
            title="Alpha Issue",
            confidence_frame="differential",
            next_best_action="Book hematology.",
            why="High-yield next step.",
        ),
    )
    _write_json(
        repo_root / ".state" / "issues" / "beta-issue.json",
        _issue_payload(
            profile_slug="beta",
            title="Beta Issue",
            confidence_frame="likely diagnosis",
            next_best_action="Book gastroenterology.",
            why="Profile-specific follow-up.",
        ),
    )

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "plan",
            "--profile",
            "alpha",
        ]
    )

    assert exit_code == 0
    issues = json.loads((repo_root / ".state" / "profiles" / "alpha" / "issues.json").read_text())
    assert [issue["slug"] for issue in issues["issues"]] == ["alpha-issue"]
    actions = json.loads((repo_root / ".state" / "profiles" / "alpha" / "actions.json").read_text())
    assert actions["actions"][0]["issue_slug"] == "alpha-issue"


def test_outcome_update_alias_rescans_without_manual_event_file(
    tmp_path: Path, capsys
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    home_dir = tmp_path / "home"
    _write_profile(home_dir)

    exit_code = main(
        [
            "--repo-root",
            str(repo_root),
            "--home-dir",
            str(home_dir),
            "outcome-update",
            "--profile",
            "test-user",
        ]
    )

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "deprecated" in captured.out
    assert (repo_root / ".state" / "profiles" / "test-user" / "sources.json").exists()


def test_docs_match_skill_first_workflow() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    readme = (repo_root / "README.md").read_text(encoding="utf-8")
    agents = (repo_root / "AGENTS.md").read_text(encoding="utf-8")
    skill = (
        repo_root / ".codex" / "skills" / "what-next-report" / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "Use the what-next-report skill for profile myname" in readme
    assert "The canonical interface is the `what-next-report` skill through the agent." in readme
    assert "The normal user-facing entrypoint for this repo is the agent invoking the relevant project skill" in agents
    assert "The skill itself is the primary interface." in skill

    for content in (readme, agents, skill):
        assert "outcome-update --profile" not in content
        assert "health-agent review --profile" not in content
