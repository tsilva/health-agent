from __future__ import annotations

import subprocess
from pathlib import Path

from healthpilot.cli import main
from healthpilot.output_migration import migrate_output_layout
from healthpilot.paths import (
    classify_report_bucket,
    find_previous_report,
    report_companion_path,
    report_output_path,
)
from healthpilot.report_validation import BASELINE_CHANGE_TEXT, validate_report


def _valid_what_next_report() -> str:
    return "\n".join(
        [
            "# Plano de ação",
            "",
            "**Relatório gerado:** 2026-08-11T10:00:00+01:00",
            "**Data-limite dos registos:** 2026-08-10",
            "**Instantâneo de evidência:** abc123 às 2026-08-11T09:00:00Z",
            "**Relatório comparável anterior:** nenhum",
            "**Gravidade das lacunas nas fontes:** ligeira",
            "",
            "## Estado atual",
            "Diagnóstico provável, confiança moderada na evidência, urgência de rotina.",
            "",
            "## Agora / A seguir / Mais tarde",
            "| Prioridade | Horizonte | Estado | Ação | Concluída quando | Trazer como resultado |",
            "|---|---|---|---|---|---|",
            "| 1 | Agora | Pronta | Repetir hemograma | Resultado recebido | Valores do hemograma [HL:2026-08-10:processed:L4] |",
            "",
            "## Alterações desde o relatório anterior",
            BASELINE_CHANGE_TEXT,
            "",
            "## Análise de suporte",
            "A ação reduz o diagnóstico diferencial.",
            "",
            "## Apêndice de evidência",
            "### Cobertura das fontes",
            "Fontes indisponíveis: nenhuma.",
        ]
    )


def _minimal_report(decision_heading: str) -> str:
    return "\n".join(
        [
            "# Relatório",
            "**Relatório gerado:** 2026-08-11T10:00:00+01:00",
            "**Data-limite dos registos:** 2026-08-10",
            "**Instantâneo de evidência:** abc123 às 2026-08-11T09:00:00Z",
            "**Relatório comparável anterior:** nenhum",
            "**Gravidade das lacunas nas fontes:** nenhuma",
            decision_heading,
            "Conteúdo da decisão [LAB:2026-08-10:ferritin-R2].",
            "## Alterações desde o relatório anterior",
            BASELINE_CHANGE_TEXT,
            "## Análise de suporte",
            "A evidência observada e a inferência estão separadas.",
            "## Apêndice de evidência",
            "### Cobertura das fontes",
            "Fontes indisponíveis: nenhuma.",
        ]
    )


def test_report_output_paths_and_previous_report_lookup(tmp_path: Path) -> None:
    report_dir = report_output_path(tmp_path, "alice", "root-cause")
    report_dir.mkdir(parents=True)
    older = report_dir / "2026-08-01-alice-root-cause-fatigue.md"
    newest = report_dir / "2026-08-08-alice-root-cause-fatigue.md"
    unrelated = report_dir / "2026-08-09-alice-root-cause-rash.md"
    for path in (older, newest, unrelated):
        path.write_text(path.name, encoding="utf-8")

    assert classify_report_bucket(newest.name) == "root-cause"
    assert (
        find_previous_report(
            tmp_path,
            "alice",
            "root-cause",
            "root-cause-fatigue.md",
            before_date="2026-08-10",
        )
        == newest
    )
    assert report_companion_path(
        tmp_path,
        "alice",
        "root-cause",
        report_date="2026-08-10",
        artifact_slug="root-cause-fatigue",
        filename="chart.png",
        companion_count=4,
    ) == (
        tmp_path
        / ".output"
        / "alice"
        / "root-cause"
        / "assets"
        / "2026-08-10-root-cause-fatigue"
        / "2026-08-10-chart.png"
    )


def test_output_migration_is_safe_and_idempotent(tmp_path: Path) -> None:
    profile_dir = tmp_path / ".output" / "alice"
    legacy_dir = profile_dir / "legacy"
    legacy_dir.mkdir(parents=True)

    canonical_source = profile_dir / "2026-08-01-alice-action-plan.md"
    canonical_source.write_text("current clinical content", encoding="utf-8")
    conflicting_source = legacy_dir / "alice-action-plan-2026-08-01.md"
    conflicting_source.write_text("older conflicting clinical content", encoding="utf-8")
    treatment_source = legacy_dir / "alice-medication-history-2026-07-20.md"
    treatment_source.write_text("treatment history", encoding="utf-8")
    ambiguous_source = profile_dir / "2026-08-01-alice-chart.png"
    ambiguous_source.write_bytes(b"chart")
    metadata = tmp_path / ".output" / ".DS_Store"
    metadata.write_bytes(b"metadata")

    dry_run = migrate_output_layout(tmp_path, apply=False)
    assert canonical_source.exists()
    assert any(item["operation"] == "conflict" for item in dry_run["operations"])
    assert Path(dry_run["manifest_path"]).exists()

    applied = migrate_output_layout(tmp_path, apply=True)
    action = profile_dir / "what-next" / "2026-08-01-alice-action-plan.md"
    treatment = (
        profile_dir
        / "treatment-record"
        / "2026-07-20-alice-medication-history.md"
    )
    conflict = profile_dir / "legacy" / "conflicts" / "2026-08-01-alice-action-plan.md"
    assert action.read_text(encoding="utf-8") == "current clinical content"
    assert treatment.read_text(encoding="utf-8") == "treatment history"
    assert conflict.read_text(encoding="utf-8") == "older conflicting clinical content"
    assert (profile_dir / "legacy" / ambiguous_source.name).read_bytes() == b"chart"
    assert not metadata.exists()
    assert applied["apply"] is True

    second_run = migrate_output_layout(tmp_path, apply=True)
    assert second_run["operations"] == []


def test_output_migration_deduplicates_identical_collisions(tmp_path: Path) -> None:
    profile_dir = tmp_path / ".output" / "alice"
    legacy_dir = profile_dir / "legacy"
    legacy_dir.mkdir(parents=True)
    first = profile_dir / "2026-08-01-alice-action-plan.md"
    duplicate = legacy_dir / "alice-action-plan-2026-08-01.md"
    first.write_text("same", encoding="utf-8")
    duplicate.write_text("same", encoding="utf-8")

    manifest = migrate_output_layout(tmp_path, apply=True)

    destination = profile_dir / "what-next" / "2026-08-01-alice-action-plan.md"
    assert destination.read_text(encoding="utf-8") == "same"
    assert not duplicate.exists()
    assert sum(item["operation"] == "deduplicate" for item in manifest["operations"]) == 1


def test_output_migration_repairs_relative_companion_links(tmp_path: Path) -> None:
    profile_dir = tmp_path / ".output" / "alice"
    profile_dir.mkdir(parents=True)
    report = profile_dir / "2026-08-01-alice-action-plan.md"
    chart = profile_dir / "2026-08-01-alice-chart.png"
    report.write_text(
        "Clinical text.\n\n![Trend](2026-08-01-alice-chart.png)\n",
        encoding="utf-8",
    )
    chart.write_bytes(b"chart")

    migrate_output_layout(tmp_path, apply=True)

    migrated = profile_dir / "what-next" / report.name
    assert "Clinical text." in migrated.read_text(encoding="utf-8")
    assert "../legacy/2026-08-01-alice-chart.png" in migrated.read_text(
        encoding="utf-8"
    )


def test_shared_report_validation_accepts_contract_and_rejects_leaks(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / ".output"
        / "alice"
        / "what-next"
        / "2026-08-11-alice-action-plan.md"
    )
    report_path.parent.mkdir(parents=True)
    report_text = _valid_what_next_report()
    report_path.write_text(report_text, encoding="utf-8")

    assert validate_report(
        report_text,
        report_type="what-next",
        report_path=report_path,
    ) == []

    leaked = report_text.replace(
        "A ação reduz o diagnóstico diferencial.",
        "Evidence: /Users/alice/private/health.md <!-- DEPS: internal -->",
    )
    errors = validate_report(leaked, report_type="what-next", report_path=report_path)
    assert any("absolute macOS path" in error for error in errors)
    assert any("HTML/parser comment" in error for error in errors)

    english_metadata = report_text.replace(
        "**Relatório gerado:**", "**Report generated:**"
    )
    errors = validate_report(
        english_metadata, report_type="what-next", report_path=report_path
    )
    assert "missing metadata: Relatório gerado" in errors


def test_shared_report_validation_covers_every_report_type(tmp_path: Path) -> None:
    fixtures = {
        "root-cause": (
            "root-cause",
            "2026-08-11-alice-root-cause-fatigue.md",
            "## Principais hipóteses",
        ),
        "treatment-record": (
            "treatment-record",
            "2026-08-11-alice-treatment-record.md",
            "## Regime atual em resumo",
        ),
        "organ-system-health": (
            "organ-system-health",
            "2026-08-11-alice-organ-system-health.md",
            "## Sistemas com pontuação mais baixa",
        ),
        "mortality-risk": (
            "mortality-risk",
            "2026-08-11-alice-mortality-risk.md",
            "## Principais riscos e medidas preventivas",
        ),
    }
    for report_type, (bucket, filename, decision_heading) in fixtures.items():
        path = tmp_path / ".output" / "alice" / bucket / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        text = _minimal_report(decision_heading)
        assert validate_report(
            text,
            report_type=report_type,
            report_path=path,
        ) == []


def test_shared_report_validation_enforces_word_budget_and_calendar_date(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / ".output"
        / "alice"
        / "what-next"
        / "2026-99-99-alice-action-plan.md"
    )
    oversized = _valid_what_next_report().replace(
        "A ação reduz o diagnóstico diferencial.",
        "word " * 1900,
    )
    errors = validate_report(
        oversized,
        report_type="what-next",
        report_path=report_path,
    )
    assert "report filename contains an invalid calendar date" in errors
    assert any("main body exceeds 1800 words" in error for error in errors)


def test_repeat_report_requires_classified_change(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / ".output"
        / "alice"
        / "what-next"
        / "2026-08-11-alice-action-plan.md"
    )
    previous = report_path.with_name("2026-08-01-alice-action-plan.md")
    report_path.parent.mkdir(parents=True)
    previous.write_text("prior", encoding="utf-8")
    report_text = _valid_what_next_report()

    errors = validate_report(
        report_text,
        report_type="what-next",
        report_path=report_path,
        previous_path=previous,
    )
    assert "repeat report cannot use the baseline change statement" in errors

    updated = report_text.replace(
        BASELINE_CHANGE_TEXT,
        "Alterado: o hemograma é agora a ação de maior prioridade [HL:2026-08-10:processed:L4].",
    )
    assert validate_report(
        updated,
        report_type="what-next",
        report_path=report_path,
        previous_path=previous,
    ) == []


def test_reporting_cli_exposes_validation_and_migration(tmp_path: Path) -> None:
    report_path = (
        tmp_path
        / ".output"
        / "alice"
        / "what-next"
        / "2026-08-11-alice-action-plan.md"
    )
    report_path.parent.mkdir(parents=True)
    report_path.write_text(_valid_what_next_report(), encoding="utf-8")

    assert main(
        [
            "--repo-root",
            str(tmp_path),
            "validate-report",
            "--type",
            "what-next",
            "--report",
            str(report_path),
        ]
    ) == 0
    assert main(
        [
            "--repo-root",
            str(tmp_path),
            "migrate-output-layout",
        ]
    ) == 0


def test_gitignore_protects_private_outputs_without_hiding_templates() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    def ignored(path: str) -> bool:
        return (
            subprocess.run(
                ["git", "check-ignore", "--no-index", "-q", path],
                cwd=repo_root,
                check=False,
            ).returncode
            == 0
        )

    assert ignored(".output/alice/what-next/2026-08-11-alice-action-plan.md")
    assert ignored(".state/profiles/alice/evidence-packet.json")
    assert ignored(".state/output-layout-migration.json")
    assert ignored("profiles/alice.yaml")
    assert ignored("tmp/pdfs/appointment-spec.json")

    assert not ignored(".state/_template/issues.json")
    assert not ignored(".state/template/issues.json")
    assert not ignored("profiles/template.yaml.example")
    assert not ignored("src/healthpilot/report_validation.py")
    assert not ignored(".codex/skills/_shared/healthpilot-report-contract.md")
