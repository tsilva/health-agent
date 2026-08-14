"""Shared structural and privacy validation for user-facing Markdown reports."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from healthpilot.paths import REPORT_TYPE_BUCKETS


BASELINE_CHANGE_TEXT = (
    "Relatório de referência; não foi encontrado nenhum artefacto comparável anterior."
)

REPORT_CONTRACTS = {
    "what-next": {
        "decision_headings": ("## Estado atual", "## Agora / A seguir / Mais tarde"),
        "word_limit": 1800,
        "artifact_pattern": r"action-plan\.md",
    },
    "root-cause": {
        "decision_headings": ("## Principais hipóteses",),
        "word_limit": 2500,
        "artifact_pattern": r"root-cause-[a-z0-9][a-z0-9-]*\.md",
    },
    "treatment-record": {
        "decision_headings": ("## Regime atual em resumo",),
        "word_limit": 3000,
        "artifact_pattern": r"treatment-record\.md",
    },
    "organ-system-health": {
        "decision_headings": ("## Sistemas com pontuação mais baixa",),
        "word_limit": 2500,
        "artifact_pattern": r"organ-system-health\.md",
    },
    "mortality-risk": {
        "decision_headings": ("## Principais riscos e medidas preventivas",),
        "word_limit": 2500,
        "artifact_pattern": r"mortality-risk\.md",
    },
}

REQUIRED_METADATA = (
    "Relatório gerado",
    "Data-limite dos registos",
    "Instantâneo de evidência",
    "Relatório comparável anterior",
    "Gravidade das lacunas nas fontes",
)

FORBIDDEN_PATTERNS = {
    "absolute macOS path": re.compile(r"(?<!\w)/Users/[^\s|)>]+"),
    "absolute Linux home path": re.compile(r"(?<!\w)/home/[^\s|)>]+"),
    "absolute Windows user path": re.compile(r"[A-Za-z]:\\Users\\[^\s|)>]+", re.I),
    "file URI": re.compile(r"file://", re.I),
    "HTML/parser comment": re.compile(r"<!--|-->"),
    "OS metadata": re.compile(r"\.DS_Store", re.I),
    "parser state": re.compile(r"\.state\.json", re.I),
    "review artifact": re.compile(r"\.review-artifacts", re.I),
    "dependency metadata": re.compile(r"\bDEPS\s*:", re.I),
    "snapshot placeholder": re.compile(r"No additional snapshot details", re.I),
}

PLACEHOLDER_RE = re.compile(r"\{[^{}\n]+\}")
SAFE_CITATION_RE = re.compile(
    r"\[(?:LAB|HL|EXAM|GEN|LIFE):[A-Za-z0-9][A-Za-z0-9:-]*\]"
)
EVIDENCE_LIKE_RE = re.compile(r"\[(?:LAB|HL|EXAM|GEN|LIFE):[^\]]*\]")
WORD_RE = re.compile(r"\b[\w][\w'’/-]*\b", re.UNICODE)
CHANGE_TERMS_RE = re.compile(
    r"\b(?:adicionado|adicionada|alterado|alterada|resolvido|resolvida|inalterado|inalterada)\b",
    re.I,
)


def _section(text: str, heading: str) -> str:
    if heading not in text:
        return ""
    section = text.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", section, flags=re.MULTILINE)
    return section[: next_heading.start()] if next_heading else section


def _validate_path(report_path: Path, report_type: str) -> list[str]:
    errors: list[str] = []
    expected_bucket = REPORT_TYPE_BUCKETS[report_type]
    if report_path.parent.name != expected_bucket:
        errors.append(
            f"report must be inside the {expected_bucket!r} bucket; found {report_path.parent.name!r}"
        )
        return errors

    profile_slug = report_path.parent.parent.name
    artifact_pattern = REPORT_CONTRACTS[report_type]["artifact_pattern"]
    filename_re = re.compile(
        rf"^(?P<date>\d{{4}}-\d{{2}}-\d{{2}})-{re.escape(profile_slug)}-{artifact_pattern}$"
    )
    match = filename_re.fullmatch(report_path.name)
    if not match:
        errors.append(
            "report filename must start with YYYY-MM-DD, include the profile slug, "
            f"and match the {report_type} artifact contract"
        )
    else:
        try:
            datetime.strptime(match.group("date"), "%Y-%m-%d")
        except ValueError:
            errors.append("report filename contains an invalid calendar date")
    return errors


def validate_report(
    text: str,
    *,
    report_type: str,
    report_path: Path | None = None,
    previous_path: Path | None = None,
) -> list[str]:
    if report_type not in REPORT_CONTRACTS:
        return [f"unknown report type: {report_type}"]

    errors: list[str] = []
    contract = REPORT_CONTRACTS[report_type]
    if report_path is not None:
        errors.extend(_validate_path(report_path, report_type))

    for label in REQUIRED_METADATA:
        if not re.search(rf"\*\*{re.escape(label)}:\*\*\s*\S+", text):
            errors.append(f"missing metadata: {label}")

    severity = re.search(
        r"\*\*Gravidade das lacunas nas fontes:\*\*\s*(nenhuma|ligeira|material|crítica)\b",
        text,
        flags=re.I,
    )
    if not severity:
        errors.append(
            "a gravidade das lacunas nas fontes deve ser nenhuma, ligeira, material ou crítica"
        )

    nonblank_lines = [line.strip() for line in text.splitlines() if line.strip()]
    decision_positions: list[int] = []
    for heading in contract["decision_headings"]:
        if heading not in text:
            errors.append(f"missing decision heading: {heading}")
            continue
        decision_positions.append(text.index(heading))
        line_position = next(
            (index for index, line in enumerate(nonblank_lines, start=1) if line == heading),
            None,
        )
        if line_position is None or line_position > 40:
            errors.append(f"decision heading must appear within first 40 nonblank lines: {heading}")

    changes_heading = "## Alterações desde o relatório anterior"
    appendix_heading = "## Apêndice de evidência"
    for heading in (changes_heading, appendix_heading):
        if heading not in text:
            errors.append(f"missing required heading: {heading}")

    if decision_positions and changes_heading in text and appendix_heading in text:
        if max(decision_positions) >= text.index(changes_heading):
            errors.append("decision section must appear before change tracking")
        if text.index(changes_heading) >= text.index(appendix_heading):
            errors.append("change tracking must appear before the evidence appendix")

    changes = _section(text, changes_heading)
    has_baseline = BASELINE_CHANGE_TEXT in changes
    if previous_path is not None:
        if not previous_path.exists():
            errors.append(f"previous report does not exist: {previous_path}")
        if has_baseline:
            errors.append("repeat report cannot use the baseline change statement")
        if not CHANGE_TERMS_RE.search(changes):
            errors.append("repeat report must classify changes as added, changed, resolved, or unchanged")
    elif not has_baseline and not CHANGE_TERMS_RE.search(changes):
        errors.append("change section must contain the baseline statement or a classified change")

    if appendix_heading in text:
        main_body = text.split(appendix_heading, 1)[0]
        word_count = len(WORD_RE.findall(main_body))
        if word_count > contract["word_limit"]:
            errors.append(
                f"main body exceeds {contract['word_limit']} words; found {word_count}"
            )
        appendix = text.split(appendix_heading, 1)[1]
        if "Cobertura das fontes" not in appendix:
            errors.append("o apêndice de evidência deve incluir Cobertura das fontes")
        if "Fontes indisponíveis" not in appendix:
            errors.append("o apêndice de evidência deve indicar Fontes indisponíveis")

    for label, pattern in FORBIDDEN_PATTERNS.items():
        if pattern.search(text):
            errors.append(f"report contains forbidden {label}")
    if PLACEHOLDER_RE.search(text):
        errors.append("report contains an unresolved template placeholder")

    for candidate in EVIDENCE_LIKE_RE.findall(text):
        if not SAFE_CITATION_RE.fullmatch(candidate):
            errors.append(f"malformed evidence reference: {candidate}")

    return errors
