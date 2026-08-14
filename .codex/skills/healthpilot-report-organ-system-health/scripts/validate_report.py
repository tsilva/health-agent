#!/usr/bin/env python3
"""Validate structure, inventory coverage, and score ordering in an organ-system report."""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path


SYSTEMS = (
    "Cardiovascular e vascular",
    "Respiratório",
    "Neurológico",
    "Saúde mental e comportamental",
    "Endócrino e metabólico",
    "Gastrointestinal",
    "Hepático, biliar e pancreático",
    "Renal e urinário",
    "Hematológico",
    "Imunitário, inflamatório e linfático",
    "Musculoesquelético e tecido conjuntivo",
    "Tegumentar",
    "Reprodutivo e sexual",
    "Sensorial",
    "Oral e dentário",
    "Sono e ritmo circadiano",
)

COMPONENTS = (
    "Coração (estrutura, ritmo e função de bomba)",
    "Circulação arterial e coronária",
    "Circulação venosa e periférica",
    "Pulmões e vias respiratórias",
    "Cérebro e cognição",
    "Medula espinal e nervos periféricos",
    "Sistema nervoso autónomo",
    "Humor, ansiedade e função comportamental",
    "Tiroide",
    "Regulação da glicose e pâncreas endócrino",
    "Função suprarrenal e outras funções endócrinas",
    "Esófago e estômago",
    "Intestino delgado e absorção",
    "Cólon e reto",
    "Fígado",
    "Vesícula biliar e vias biliares",
    "Pâncreas exócrino",
    "Rins",
    "Bexiga e trato urinário inferior",
    "Glóbulos vermelhos e transporte de oxigénio",
    "Glóbulos brancos e medula óssea",
    "Plaquetas e coagulação",
    "Função imunitária e linfática",
    "Ossos",
    "Articulações, tendões e ligamentos",
    "Músculo esquelético",
    "Coluna vertebral",
    "Pele",
    "Cabelo e unhas",
    "Órgãos reprodutores e função hormonal",
    "Função sexual",
    "Olhos e visão",
    "Ouvidos, audição e função vestibular",
    "Dentes e periodonto",
    "Mucosa oral, maxilar e glândulas salivares",
    "Sono e função circadiana",
)

REQUIRED_HEADINGS = (
    "## Sistemas com pontuação mais baixa",
    "## Significado das pontuações",
    "## Contexto do estado atual",
    "## Pontuações dos sistemas por ordem",
    "## Pontuações detalhadas dos órgãos e subsistemas",
    "## Cinco sistemas com pontuação mais baixa",
    "## Achados transversais aos sistemas",
    "## Lacunas de evidência",
    "## Apêndice de evidência",
    "### Cobertura das fontes",
    "### Notas de segurança",
    "### Limitações",
    "### Referências de evidência",
)
SYSTEM_ROW_RE = re.compile(
    r"^\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10\s*\|"
)
COMPONENT_ROW_RE = re.compile(
    r"^\|\s*[^|]+\|\s*([^|]+?)\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10\s*\|"
)
PLACEHOLDER_RE = re.compile(r"\{[^{}]+\}|YYYY-MM-DD|^\|\s*…\s*\|", re.MULTILINE)


def _section(text: str, heading: str) -> str:
    after = text.split(heading, 1)[1]
    next_heading = re.search(r"^##\s+", after, flags=re.MULTILINE)
    return after[: next_heading.start()] if next_heading else after


def _valid_score(score: float) -> bool:
    return 0 <= score <= 10 and math.isclose(score * 2, round(score * 2), abs_tol=1e-8)


def validate(text: str) -> list[str]:
    errors: list[str] = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing required heading: {heading}")
    if PLACEHOLDER_RE.search(text):
        errors.append("report still contains template placeholders")

    if "## Pontuações dos sistemas por ordem" in text:
        section = _section(text, "## Pontuações dos sistemas por ordem")
        rows = [
            (int(match.group(1)), match.group(2).strip(), float(match.group(3)))
            for line in section.splitlines()
            if (match := SYSTEM_ROW_RE.match(line))
        ]
        if len(rows) != len(SYSTEMS):
            errors.append(
                f"ranked system table must contain exactly {len(SYSTEMS)} rows; found {len(rows)}"
            )
        else:
            ranks = [row[0] for row in rows]
            if ranks != list(range(1, len(SYSTEMS) + 1)):
                errors.append(f"system ranks must be sequential; found {ranks}")

            names = [row[1] for row in rows]
            missing = sorted(set(SYSTEMS) - set(names))
            extra = sorted(set(names) - set(SYSTEMS))
            if missing:
                errors.append(f"missing canonical systems: {', '.join(missing)}")
            if extra:
                errors.append(f"unexpected canonical system names: {', '.join(extra)}")
            if len(set(names)) != len(names):
                errors.append("canonical systems must be unique")

            scores = [row[2] for row in rows]
            invalid = [score for score in scores if not _valid_score(score)]
            if invalid:
                errors.append(f"system scores must be 0–10 in 0.5 increments; found {invalid}")
            if scores != sorted(scores):
                errors.append(f"system scores must be sorted lowest to highest; found {scores}")

    if "## Pontuações detalhadas dos órgãos e subsistemas" in text:
        section = _section(text, "## Pontuações detalhadas dos órgãos e subsistemas")
        rows = [
            (match.group(1).strip(), float(match.group(2)))
            for line in section.splitlines()
            if (match := COMPONENT_ROW_RE.match(line))
        ]
        names = [row[0] for row in rows]
        missing = sorted(set(COMPONENTS) - set(names))
        if missing:
            errors.append(f"missing required organ/subsystem rows: {', '.join(missing)}")
        duplicates = sorted({name for name in names if names.count(name) > 1})
        if duplicates:
            errors.append(f"duplicate organ/subsystem rows: {', '.join(duplicates)}")
        invalid = [score for _, score in rows if not _valid_score(score)]
        if invalid:
            errors.append(f"organ/subsystem scores must be 0–10 in 0.5 increments; found {invalid}")

    return errors


def _self_test() -> None:
    system_rows = [
        f"| {rank} | {name} | 5.0/10 | 2–8 | Baixa | incerteza | Sem dados diretos |"
        for rank, name in enumerate(SYSTEMS, start=1)
    ]
    component_rows = [
        f"| Sistema principal | {name} | 5.0/10 | 2–8 | Baixa | incerteza | Sem dados diretos |"
        for name in COMPONENTS
    ]
    fixture = "\n".join(
        [
            "# Relatório de saúde dos órgãos e sistemas — Pessoa de teste",
            "## Sistemas com pontuação mais baixa",
            "- Teste.",
            "## Significado das pontuações",
            "- Teste.",
            "## Contexto do estado atual",
            "- Teste.",
            "## Pontuações dos sistemas por ordem",
            *system_rows,
            "## Pontuações detalhadas dos órgãos e subsistemas",
            *component_rows,
            "## Cinco sistemas com pontuação mais baixa",
            "- Teste.",
            "## Achados transversais aos sistemas",
            "- Teste.",
            "## Lacunas de evidência",
            "- Teste.",
            "## Apêndice de evidência",
            "### Cobertura das fontes",
            "- Teste.",
            "### Notas de segurança",
            "- Teste.",
            "### Limitações",
            "- Teste.",
            "### Referências de evidência",
            "- Teste.",
        ]
    )
    assert validate(fixture) == []
    assert validate(fixture.replace("| 1 | Cardiovascular e vascular | 5.0/10", "| 1 | Cardiovascular e vascular | 5.5/10"))
    assert validate(fixture.replace("| Sistema principal | Tiroide |", "| Sistema principal | Tiroide em falta |"))


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
