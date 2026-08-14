#!/usr/bin/env python3
"""Validate the required structure of a Healthpilot treatment record."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_HEADINGS = (
    "## Regime atual em resumo",
    "## Medicação atual",
    "## Suplementos atuais",
    "## Tratamentos atuais não medicamentosos",
    "## Monitorização e seguimento atuais",
    "## Planeado ou recomendado — início não confirmado",
    "## Estado atual incerto ou contraditório",
    "## Interrompido ou concluído recentemente",
    "## Histórico de medicação e suplementos",
    "## Alertas de reconciliação",
    "## Apêndice de evidência",
    "### Cobertura das fontes",
    "### Notas sobre a evidência e limitações",
)
SECTION_RULES = {
    "## Medicação atual": "Não foi identificada medicação atual nos registos disponíveis.",
    "## Suplementos atuais": "Não foram identificados suplementos atuais nos registos disponíveis.",
    "## Tratamentos atuais não medicamentosos": (
        "Não foram identificados tratamentos atuais não medicamentosos nos registos disponíveis."
    ),
    "## Monitorização e seguimento atuais": (
        "Não foi identificado um regime atual de monitorização ou seguimento nos registos disponíveis."
    ),
    "## Histórico de medicação e suplementos": (
        "Não foram identificados medicamentos ou suplementos históricos adicionais nos registos disponíveis."
    ),
}
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}|YYYY-MM-DD")
DATA_ROW_RE = re.compile(
    r"^\|(?!\s*(?:---|Medicamento|Suplemento|Tratamento|Atividade|Item)\s*\|)", re.I
)


def _section(text: str, heading: str) -> str:
    after = text.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", after, flags=re.MULTILINE)
    return after[: next_heading.start()] if next_heading else after


def validate(text: str) -> list[str]:
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")

    if PLACEHOLDER_RE.search(text):
        errors.append("report still contains template placeholders")

    for heading, empty_statement in SECTION_RULES.items():
        if heading not in text:
            continue
        section = _section(text, heading)
        has_data_row = any(DATA_ROW_RE.match(line) for line in section.splitlines())
        if not has_data_row and empty_statement not in section:
            errors.append(
                f"{heading} must contain at least one data row or the explicit empty statement"
            )

    if "**Conclusão clara:**" not in text:
        errors.append("current regimen summary must include **Conclusão clara:**")
    if "**Próxima confirmação necessária:**" not in text:
        errors.append("current regimen summary must include **Próxima confirmação necessária:**")

    return errors


def _self_test() -> None:
    required_sections = []
    for heading, empty_statement in SECTION_RULES.items():
        required_sections.extend([heading, empty_statement])

    fixture = "\n".join(
        [
            "# Registo de tratamentos — Pessoa de teste",
            "## Regime atual em resumo",
            "- **Conclusão clara:** Nenhum item confirmado.",
            "- **Próxima confirmação necessária:** Nenhuma.",
            *required_sections,
            "## Planeado ou recomendado — início não confirmado",
            "- Nenhum.",
            "## Estado atual incerto ou contraditório",
            "- Nenhum.",
            "## Interrompido ou concluído recentemente",
            "- Nenhum.",
            "## Alertas de reconciliação",
            "- Nenhum identificado nos registos disponíveis.",
            "## Apêndice de evidência",
            "### Cobertura das fontes",
            "| Fonte | Estado |",
            "|---|---|",
            "| Registo de saúde | disponível |",
            "### Notas sobre a evidência e limitações",
            "- Foram analisadas as fontes diretas mais recentes.",
        ]
    )
    assert validate(fixture) == []
    assert validate(fixture.replace("**Conclusão clara:**", "Conclusão clara:"))
    assert validate(fixture + "\n{unfilled placeholder}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", type=Path, help="Markdown report to validate")
    parser.add_argument("--self-test", action="store_true", help="Run built-in checks")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("self-test passed")
        return 0
    if args.report is None:
        parser.error("report is required unless --self-test is used")

    errors = validate(args.report.read_text(encoding="utf-8"))
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("report validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
