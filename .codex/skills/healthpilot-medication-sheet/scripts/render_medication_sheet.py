#!/usr/bin/env python3
"""Render a one-page Healthpilot colour-coded medication sheet from JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    from pypdf import PdfReader
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Paragraph, Table, TableStyle
except ImportError as exc:  # pragma: no cover - environment failure
    raise SystemExit(
        "Missing PDF dependency. Run with the bundled Codex workspace Python runtime "
        "containing reportlab and pypdf."
    ) from exc


class SpecError(ValueError):
    """Raised when the medication-sheet specification is invalid."""


PAGE_W, PAGE_H = A4
MARGIN = 14 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

TEAL = colors.HexColor("#0B5E68")
META_BG = colors.HexColor("#D9D9D9")
GRID = colors.HexColor("#AAB8BC")
ALERT_BG = colors.HexColor("#FFF3D5")
ALERT_BORDER = colors.HexColor("#D88A17")
PENDING_BG = colors.HexColor("#F4F4F4")

PALETTES = {
    "yellow": ("#DEC326", "#FFF0A6"),
    "pink": ("#C886A4", "#F1D4DF"),
    "blue": ("#59A9C0", "#C8E5EE"),
    "grey": ("#7D8589", "#E5EAEC"),
    "green": ("#4F8B69", "#DDEEE4"),
    "orange": ("#C97932", "#F6E2CF"),
    "purple": ("#7963A7", "#E7E0F3"),
}
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
PRIVATE_TEXT = re.compile(
    r"(?:/Users/|file://|\.state\.json|\.DS_Store|\.review-artifacts|DEPS:)",
    re.IGNORECASE,
)


def _required_string(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"{path} must be a non-empty string")
    text = value.strip()
    if PRIVATE_TEXT.search(text):
        raise SpecError(f"{path} contains a private path or parser artifact")
    return text


def _optional_string(value: Any, path: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise SpecError(f"{path} must be a string")
    text = value.strip()
    if PRIVATE_TEXT.search(text):
        raise SpecError(f"{path} contains a private path or parser artifact")
    return text


def _iso_date(value: Any, path: str) -> date:
    text = _required_string(value, path)
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise SpecError(f"{path} must use YYYY-MM-DD") from exc


def _palette(value: Any, path: str) -> tuple[Any, Any]:
    if isinstance(value, str):
        if value not in PALETTES:
            raise SpecError(f"{path} must be a supported palette name or custom colour object")
        bar, background = PALETTES[value]
        return colors.HexColor(bar), colors.HexColor(background)
    if not isinstance(value, dict):
        raise SpecError(f"{path} must be a palette name or object")
    bar = _required_string(value.get("bar"), f"{path}.bar")
    background = _required_string(value.get("background"), f"{path}.background")
    if not HEX_COLOR.fullmatch(bar) or not HEX_COLOR.fullmatch(background):
        raise SpecError(f"{path} colours must use #RRGGBB")
    return colors.HexColor(bar), colors.HexColor(background)


def _validate_spec(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise SpecError("specification must be a JSON object")
    profile = raw.get("profile")
    if not isinstance(profile, dict):
        raise SpecError("profile must be an object")
    slug = _required_string(profile.get("slug"), "profile.slug")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise SpecError("profile.slug must be lowercase hyphen-case")
    name = _required_string(profile.get("name"), "profile.name")
    born = _iso_date(profile.get("date_of_birth"), "profile.date_of_birth")
    updated = _iso_date(raw.get("updated_on"), "updated_on")
    cutoff = _iso_date(raw.get("record_cutoff"), "record_cutoff")
    if cutoff > updated:
        raise SpecError("record_cutoff cannot be later than updated_on")
    if born > updated:
        raise SpecError("profile.date_of_birth cannot be later than updated_on")

    alert = raw.get("monitoring_alert")
    normalized_alert = None
    if alert is not None:
        if not isinstance(alert, dict):
            raise SpecError("monitoring_alert must be an object")
        normalized_alert = {
            "title": _required_string(alert.get("title"), "monitoring_alert.title"),
            "text": _required_string(alert.get("text"), "monitoring_alert.text"),
        }

    sections = raw.get("sections")
    if not isinstance(sections, list) or not sections:
        raise SpecError("sections must be a non-empty list")
    normalized_sections = []
    for section_index, section in enumerate(sections):
        path = f"sections[{section_index}]"
        if not isinstance(section, dict):
            raise SpecError(f"{path} must be an object")
        items = section.get("items")
        if not isinstance(items, list) or not items:
            raise SpecError(f"{path}.items must be a non-empty list")
        normalized_items = []
        for item_index, item in enumerate(items):
            item_path = f"{path}.items[{item_index}]"
            if not isinstance(item, dict):
                raise SpecError(f"{item_path} must be an object")
            normalized_items.append(
                {
                    "name": _required_string(item.get("name"), f"{item_path}.name"),
                    "brand": _optional_string(item.get("brand"), f"{item_path}.brand"),
                    "form": _optional_string(item.get("form"), f"{item_path}.form"),
                    "dose": _required_string(item.get("dose"), f"{item_path}.dose"),
                    "instructions": _required_string(
                        item.get("instructions"), f"{item_path}.instructions"
                    ),
                    "reason": _required_string(item.get("reason"), f"{item_path}.reason"),
                }
            )
        normalized_sections.append(
            {
                "title": _required_string(section.get("title"), f"{path}.title"),
                "palette": _palette(section.get("color"), f"{path}.color"),
                "items": normalized_items,
            }
        )

    confirmations = raw.get("confirmations", [])
    if not isinstance(confirmations, list):
        raise SpecError("confirmations must be a list")
    normalized_confirmations = [
        _required_string(value, f"confirmations[{index}]")
        for index, value in enumerate(confirmations)
    ]
    footer_note = _optional_string(raw.get("footer_note"), "footer_note") or (
        "Documento de apoio à organização da medicação. Em caso de dúvida, "
        "confirmar com a médica, o médico ou o farmacêutico."
    )
    return {
        "profile": {"slug": slug, "name": name, "date_of_birth": born},
        "updated_on": updated,
        "record_cutoff": cutoff,
        "monitoring_alert": normalized_alert,
        "sections": normalized_sections,
        "confirmations": normalized_confirmations,
        "footer_note": footer_note,
    }


def _age_on(born: date, on_date: date) -> int:
    return on_date.year - born.year - ((on_date.month, on_date.day) < (born.month, born.day))


def _pt_date(value: date) -> str:
    return value.strftime("%d/%m/%Y")


def _markup(text: str) -> str:
    return html.escape(text).replace("\n", "<br/>")


def _paragraph(
    text: str,
    *,
    size: float,
    leading: float,
    color: Any = colors.black,
    bold: bool = False,
    align: int = TA_LEFT,
    markup: bool = False,
) -> Paragraph:
    return Paragraph(
        text if markup else _markup(text),
        ParagraphStyle(
            name=f"p-{size}-{leading}-{bold}-{align}",
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=size,
            leading=leading,
            textColor=color,
            alignment=align,
            spaceBefore=0,
            spaceAfter=0,
        ),
    )


def _build_medication_table(spec: dict[str, Any], scale: float) -> Table:
    body_size = 8.3 * scale
    body_leading = 9.4 * scale
    header_size = 9.1 * scale
    section_size = 9.4 * scale
    rows: list[list[Any]] = [
        [
            _paragraph("MEDICAMENTO", size=header_size, leading=header_size + 1, color=colors.white, bold=True, align=TA_CENTER),
            _paragraph("DOSE", size=header_size, leading=header_size + 1, color=colors.white, bold=True, align=TA_CENTER),
            _paragraph("COMO TOMAR", size=header_size, leading=header_size + 1, color=colors.white, bold=True, align=TA_CENTER),
            _paragraph("MOTIVO DA TOMA", size=header_size, leading=header_size + 1, color=colors.white, bold=True, align=TA_CENTER),
        ]
    ]
    styles: list[tuple[Any, ...]] = [("BACKGROUND", (0, 0), (-1, 0), TEAL)]

    for section in spec["sections"]:
        section_index = len(rows)
        bar, background = section["palette"]
        rows.append(
            [
                _paragraph(
                    section["title"],
                    size=section_size,
                    leading=section_size + 1,
                    color=colors.white,
                    bold=True,
                ),
                "",
                "",
                "",
            ]
        )
        styles.extend(
            [
                ("SPAN", (0, section_index), (-1, section_index)),
                ("BACKGROUND", (0, section_index), (-1, section_index), bar),
            ]
        )
        for item in section["items"]:
            item_index = len(rows)
            secondary = []
            if item["brand"]:
                secondary.append(f"({item['brand']})")
            if item["form"]:
                secondary.append(item["form"])
            name_markup = _markup(item["name"])
            if secondary:
                name_markup += "<br/><font color='#5A6C70'>" + _markup(" - ".join(secondary)) + "</font>"
            rows.append(
                [
                    _paragraph(name_markup, size=body_size, leading=body_leading, markup=True),
                    _paragraph(item["dose"], size=body_size, leading=body_leading),
                    _paragraph(item["instructions"], size=body_size * 0.98, leading=body_leading),
                    _paragraph(item["reason"], size=body_size * 0.98, leading=body_leading),
                ]
            )
            styles.append(("BACKGROUND", (0, item_index), (-1, item_index), background))

    table = Table(
        rows,
        colWidths=[CONTENT_W * 0.252, CONTENT_W * 0.128, CONTENT_W * 0.294, CONTENT_W * 0.326],
    )
    pad = max(2.2, 4.2 * scale)
    table.setStyle(
        TableStyle(
            styles
            + [
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), pad),
                ("RIGHTPADDING", (0, 0), (-1, -1), pad),
                ("TOPPADDING", (0, 0), (-1, -1), max(2, 3.2 * scale)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), max(2, 3.2 * scale)),
            ]
        )
    )
    return table


def render(spec_path: Path, output_path: Path) -> Path:
    raw = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = _validate_spec(raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle(f"Medicação Atual - {spec['profile']['name']}")
    c.setAuthor("Healthpilot")
    c.setSubject(f"Tabela de medicação atualizada em {_pt_date(spec['updated_on'])}")

    c.setFillColor(TEAL)
    c.setFont("Helvetica", 25)
    c.drawCentredString(PAGE_W / 2, PAGE_H - 24 * mm, "Medicação Atual")

    name = spec["profile"]["name"].upper()
    born = spec["profile"]["date_of_birth"]
    age = _age_on(born, spec["updated_on"])
    meta = [
        [
            _paragraph("UTENTE", size=9.2, leading=10, color=TEAL, bold=True),
            _paragraph(name, size=9.2, leading=10),
            _paragraph("ATUALIZADO EM", size=9.2, leading=10, color=TEAL, bold=True),
            _paragraph(_pt_date(spec["updated_on"]), size=9.2, leading=10),
        ],
        [
            _paragraph("DATA DE\nNASCIMENTO", size=9.2, leading=10, color=TEAL, bold=True),
            _paragraph(f"{_pt_date(born)} ({age} anos)", size=9.2, leading=10),
            _paragraph("ÚLTIMO REGISTO\nCLÍNICO", size=9.2, leading=10, color=TEAL, bold=True),
            _paragraph(_pt_date(spec["record_cutoff"]), size=9.2, leading=10),
        ],
    ]
    meta_table = Table(
        meta,
        colWidths=[CONTENT_W * 0.18, CONTENT_W * 0.35, CONTENT_W * 0.24, CONTENT_W * 0.23],
        rowHeights=[26, 36],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), META_BG),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    meta_table.wrapOn(c, CONTENT_W, 62)
    meta_table.drawOn(c, MARGIN, PAGE_H - 50 * mm)

    table_top = PAGE_H - 53 * mm
    if spec["monitoring_alert"]:
        alert_data = spec["monitoring_alert"]
        alert_markup = f"<b>{_markup(alert_data['title'])}</b><br/>{_markup(alert_data['text'])}"
        alert = Table(
            [[_paragraph(alert_markup, size=8.3, leading=10.1, markup=True)]],
            colWidths=[CONTENT_W],
        )
        alert.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), ALERT_BG),
                    ("BOX", (0, 0), (-1, -1), 1, ALERT_BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        _, alert_height = alert.wrap(CONTENT_W, 80)
        alert_bottom = PAGE_H - 52 * mm - alert_height
        alert.drawOn(c, MARGIN, alert_bottom)
        table_top = alert_bottom - 1.5

    confirmation_top = 14 * mm
    pending = None
    confirmation_height = 0.0
    if spec["confirmations"]:
        cleaned_confirmations = [
            re.sub(r"^confirmar\s+", "", value, flags=re.IGNORECASE).rstrip(" .;")
            for value in spec["confirmations"]
        ]
        confirmation_text = "CONFIRMAR: " + "; ".join(cleaned_confirmations) + "."
        pending = Table(
            [[_paragraph(confirmation_text, size=7.2, leading=8.6)]],
            colWidths=[CONTENT_W],
        )
        pending.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), PENDING_BG),
                    ("BOX", (0, 0), (-1, -1), 0.5, GRID),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        _, confirmation_height = pending.wrap(CONTENT_W, 90)
        confirmation_bottom = 11.5 * mm
        confirmation_top = confirmation_bottom + confirmation_height + 4

    available_height = table_top - confirmation_top
    table = None
    table_height = None
    for scale in (1.15, 1.10, 1.05, 1.0, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70):
        candidate = _build_medication_table(spec, scale)
        _, candidate_height = candidate.wrap(CONTENT_W, available_height)
        if candidate_height <= available_height:
            table = candidate
            table_height = candidate_height
            break
    if table is None or table_height is None:
        raise SpecError(
            "complete medication content does not fit on one A4 page; shorten nonessential prose "
            "without removing names, doses, timing, routes, or safety thresholds"
        )
    table_bottom = table_top - table_height
    table.drawOn(c, MARGIN, table_bottom)
    if pending is not None:
        pending.drawOn(c, MARGIN, table_bottom - confirmation_height - 4)

    c.setFillColor(colors.HexColor("#5A6C70"))
    c.setFont("Helvetica", 6.3)
    c.drawString(MARGIN, 6.5 * mm, spec["footer_note"][:118])
    c.drawRightString(PAGE_W - MARGIN, 6.5 * mm, f"Healthpilot - {_pt_date(spec['updated_on'])}")
    c.showPage()
    c.save()

    reader = PdfReader(output_path)
    if len(reader.pages) != 1:
        raise SpecError(f"renderer produced {len(reader.pages)} pages; exactly one is required")
    return output_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, type=Path, help="UTF-8 JSON specification")
    parser.add_argument("--output", required=True, type=Path, help="output PDF path")
    args = parser.parse_args()
    try:
        result = render(args.spec, args.output)
    except (OSError, json.JSONDecodeError, SpecError) as exc:
        raise SystemExit(f"ERROR: {exc}") from exc
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
