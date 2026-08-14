#!/usr/bin/env python3
"""Build and validate a Healthpilot doctor-appointment PDF pair from JSON."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from PIL import Image
    from pypdf import PdfReader, PdfWriter
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, LETTER
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        BaseDocTemplate,
        Frame,
        KeepTogether,
        PageTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError as exc:  # pragma: no cover - exercised only outside the PDF runtime
    raise SystemExit(
        "Missing PDF dependency. Run with the bundled Codex workspace Python runtime "
        "containing reportlab, pypdf, and Pillow."
    ) from exc


PAGE_SIZES = {"A4": A4, "LETTER": LETTER}
FACT_SECTIONS = (
    ("new_since_last_visit", "NOVO DESDE A ÚLTIMA CONSULTA"),
    ("visit_focus", "Motivo da consulta"),
    ("objective_results", "Resultados objetivos"),
    ("current_treatments", "Tratamentos atuais relevantes e reações"),
    ("relevant_history", "Antecedentes documentados relevantes"),
)
EVIDENCE_LABELS = {
    "objective_record": "Registo objetivo",
    "patient_reported": "Relatado pelo doente",
    "documented_treatment": "Tratamento documentado",
    "documented_history": "Antecedente documentado",
}
PROHIBITED_DOCTOR_LANGUAGE = re.compile(
    r"\b(hypothes(?:is|es)|differential|likely|possibly|perhaps|consider|"
    r"rule(?:d)?\s+out|recommend(?:ed|ation)?|request(?:ed)?|questions?|should|"
    r"could\s+be|may\s+be|potential(?:ly)?|probabl(?:e|y)|suspect(?:ed|s)?|"
    r"suggest(?:s|ed|ing)?|appear(?:s|ed)?|favou?rs?|consistent\s+with|"
    r"compatible\s+with|risk\s+of|hipóteses?|diferencial|prováv(?:el|eis)|provavelmente|"
    r"possív(?:el|eis)|possivelmente|talvez|considerar|a\s+excluir|recomend(?:ar|ado|ada|ação)|"
    r"pedir|pedido|pedida|solicitar|perguntas?|questões?|deveria|deve|poderá\s+ser|"
    r"pode\s+ser|potencial(?:mente)?|suspeit[ao]|sugere|aparenta|favorece|"
    r"compatível\s+com|consistente\s+com|risco\s+de)\b",
    re.IGNORECASE,
)
SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
REQUIRED_PATIENT_SECTION_KINDS = {
    "appointment_goals",
    "situation_summary",
    "current_status",
    "objective_evidence",
    "questions_to_ask",
    "source_coverage",
    "appointment_checklist",
    "after_visit_capture",
}
SECTION_KIND_RE = re.compile(r"^[a-z][a-z0-9_]*$")


class PacketError(ValueError):
    """Raised when a packet spec or output violates the contract."""


@dataclass(frozen=True)
class PreparedAttachment:
    label: str
    record_date: str
    reason: str
    source_path: Path
    prepared_pdf: Path
    source_pages: tuple[int, ...]
    page_count: int


class NumberedDocTemplate(BaseDocTemplate):
    """Small report template with unobtrusive generated-page footers."""

    def __init__(
        self,
        filename: str | Path,
        *,
        pagesize: tuple[float, float],
        title: str,
        page_offset: int = 0,
    ):
        self.document_title = title
        self.page_offset = page_offset
        super().__init__(
            str(filename),
            pagesize=pagesize,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=14 * mm,
            bottomMargin=14 * mm,
            title=title,
            author="Preparado pelo doente a partir dos registos de saúde disponíveis",
        )
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(PageTemplate(id="content", frames=[frame], onPage=self._footer))

    def _footer(self, canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#59636E"))
        canvas.drawString(15 * mm, 7 * mm, "Informação clínica privada")
        canvas.drawRightString(
            self.pagesize[0] - 15 * mm,
            7 * mm,
            f"Página {doc.page + self.page_offset}",
        )
        canvas.restoreState()


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PacketError(f"{label} must be an object")
    return value


def _require_list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise PacketError(f"{label} must be a list")
    return value


def _required_text(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PacketError(f"{label}.{key} must be a non-empty string")
    return value.strip()


def _optional_text(mapping: dict[str, Any], key: str, default: str = "") -> str:
    value = mapping.get(key, default)
    if value is None:
        return default
    if not isinstance(value, str):
        raise PacketError(f"{key} must be a string")
    return value.strip()


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


PRIVATE_OUTPUT_RE = re.compile(
    r"(?:/Users/|/home/|[A-Za-z]:\\Users\\|file://|<!--|-->|\.DS_Store|"
    r"\.state\.json|\.review-artifacts|\bDEPS\s*:|No additional snapshot details)",
    re.IGNORECASE,
)


def _report_safe_text(value: str, label: str) -> str:
    match = PRIVATE_OUTPUT_RE.search(value)
    if match:
        raise PacketError(
            f"{label} contains a private path or parser artifact {match.group(0)!r}; "
            "use a report-safe evidence ID or human-readable source label"
        )
    return value


def _page_size(spec: dict[str, Any]) -> tuple[float, float]:
    name = str(spec.get("page_size", "A4")).upper()
    if name not in PAGE_SIZES:
        raise PacketError(f"page_size must be one of {sorted(PAGE_SIZES)}")
    return PAGE_SIZES[name]


def _validate_fact(value: Any, label: str) -> dict[str, str]:
    fact = _require_mapping(value, label)
    normalized = {
        "date": _required_text(fact, "date", label),
        "text": _required_text(fact, "text", label),
        "evidence_type": _required_text(fact, "evidence_type", label),
        "source": _required_text(fact, "source", label),
    }
    if normalized["evidence_type"] not in EVIDENCE_LABELS:
        raise PacketError(
            f"{label}.evidence_type must be one of {sorted(EVIDENCE_LABELS)}"
        )
    for key, item in normalized.items():
        _report_safe_text(item, f"{label}.{key}")
    match = PROHIBITED_DOCTOR_LANGUAGE.search(normalized["text"])
    if match:
        raise PacketError(
            f"{label}.text contains clinician-analysis/request language {match.group(0)!r}; "
            "move it to the patient briefing"
        )
    return normalized


def _validate_spec(raw: Any) -> dict[str, Any]:
    spec = _require_mapping(raw, "spec")
    for key in ("profile_name", "report_date", "record_cutoff"):
        _required_text(spec, key, "spec")
    _page_size(spec)

    appointment = _require_mapping(spec.get("appointment"), "appointment")
    for key in ("date", "clinician_name", "specialty", "purpose"):
        _required_text(appointment, key, "appointment")
    purpose_match = PROHIBITED_DOCTOR_LANGUAGE.search(appointment["purpose"])
    if purpose_match:
        raise PacketError(
            "appointment.purpose must be a neutral fact, not a question, request, or analysis; "
            f"found {purpose_match.group(0)!r}"
        )

    repeat = _require_mapping(spec.get("repeat_visit"), "repeat_visit")
    status = _required_text(repeat, "status", "repeat_visit")
    if status not in {"confirmed", "uncertain", "not_found"}:
        raise PacketError("repeat_visit.status must be confirmed, uncertain, or not_found")
    evidence = _require_list(repeat.get("evidence", []), "repeat_visit.evidence")
    if status == "confirmed":
        _required_text(repeat, "prior_visit_date", "repeat_visit")
        if appointment["clinician_name"].strip().lower() in {"not provided", "unknown"}:
            raise PacketError("a confirmed repeat visit requires a named clinician")
        if not evidence:
            raise PacketError("a confirmed repeat visit requires prior-visit evidence")
    for index, item in enumerate(evidence):
        item = _require_mapping(item, f"repeat_visit.evidence[{index}]")
        for key in ("date", "text", "source"):
            value = _required_text(item, key, f"repeat_visit.evidence[{index}]")
            _report_safe_text(value, f"repeat_visit.evidence[{index}].{key}")

    doctor = _require_mapping(spec.get("doctor"), "doctor")
    normalized_doctor: dict[str, list[dict[str, str]]] = {}
    for section_key, _ in FACT_SECTIONS:
        values = _require_list(doctor.get(section_key, []), f"doctor.{section_key}")
        normalized_doctor[section_key] = [
            _validate_fact(item, f"doctor.{section_key}[{index}]")
            for index, item in enumerate(values)
        ]
    if status != "confirmed" and normalized_doctor["new_since_last_visit"]:
        raise PacketError(
            "doctor.new_since_last_visit must be empty unless repeat_visit.status is confirmed"
        )
    if not any(normalized_doctor.values()):
        raise PacketError("doctor must contain at least one fact")
    spec["doctor"] = normalized_doctor

    patient = _require_mapping(spec.get("patient"), "patient")
    sections = _require_list(patient.get("sections"), "patient.sections")
    if not sections:
        raise PacketError("patient.sections must contain at least one section")
    section_kinds: list[str] = []
    for index, section_value in enumerate(sections):
        section = _require_mapping(section_value, f"patient.sections[{index}]")
        kind = _required_text(section, "kind", f"patient.sections[{index}]")
        if not SECTION_KIND_RE.fullmatch(kind):
            raise PacketError(
                f"patient.sections[{index}].kind must use lowercase letters, digits, and underscores"
            )
        section_kinds.append(kind)
        title = _required_text(section, "title", f"patient.sections[{index}]")
        _report_safe_text(title, f"patient.sections[{index}].title")
        intro = _optional_text(section, "intro")
        items = _require_list(section.get("items", []), f"patient.sections[{index}].items")
        if not intro and not items:
            raise PacketError(f"patient.sections[{index}] must contain intro or items")
        if any(not isinstance(item, str) or not item.strip() for item in items):
            raise PacketError(f"patient.sections[{index}].items must be non-empty strings")
        if intro:
            _report_safe_text(intro, f"patient.sections[{index}].intro")
        for item_index, item in enumerate(items):
            _report_safe_text(item, f"patient.sections[{index}].items[{item_index}]")
    duplicate_kinds = sorted({kind for kind in section_kinds if section_kinds.count(kind) > 1})
    if duplicate_kinds:
        raise PacketError(f"patient section kinds must be unique: {', '.join(duplicate_kinds)}")
    missing_kinds = sorted(REQUIRED_PATIENT_SECTION_KINDS - set(section_kinds))
    if status == "confirmed" and "new_since_last_visit" not in section_kinds:
        missing_kinds.append("new_since_last_visit")
    if missing_kinds:
        raise PacketError(f"patient sections missing required kinds: {', '.join(missing_kinds)}")

    attachments = _require_list(spec.get("supporting_documents", []), "supporting_documents")
    attachment_paths: set[Path] = set()
    for index, attachment_value in enumerate(attachments):
        attachment = _require_mapping(attachment_value, f"supporting_documents[{index}]")
        for key in ("path", "label", "record_date", "reason"):
            _required_text(attachment, key, f"supporting_documents[{index}]")
        for key in ("label", "record_date", "reason"):
            _report_safe_text(
                str(attachment[key]),
                f"supporting_documents[{index}].{key}",
            )
        path = Path(attachment["path"]).expanduser()
        if not path.is_absolute():
            raise PacketError(f"supporting_documents[{index}].path must be absolute")
        if not path.exists() or not path.is_file():
            raise PacketError(f"supporting document does not exist: {path}")
        if path.suffix.lower() != ".pdf" and path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES:
            raise PacketError(f"unsupported supporting document type: {path.suffix}")
        pages = attachment.get("pages")
        if pages is not None:
            if path.suffix.lower() != ".pdf":
                raise PacketError("pages can only be specified for PDF supporting documents")
            if (
                not isinstance(pages, list)
                or not pages
                or any(not isinstance(page, int) or isinstance(page, bool) or page < 1 for page in pages)
                or len(set(pages)) != len(pages)
            ):
                raise PacketError("supporting document pages must be unique one-based integers")
            if pages != sorted(pages):
                raise PacketError("supporting document pages must preserve ascending source order")
        resolved_path = path.resolve()
        if resolved_path in attachment_paths:
            raise PacketError(f"duplicate supporting document: {path}")
        attachment_paths.add(resolved_path)

    return spec


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PacketTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=21,
            textColor=colors.HexColor("#17324D"),
            alignment=TA_LEFT,
            spaceAfter=5,
        ),
        "doctor_title": ParagraphStyle(
            "DoctorTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=16,
            textColor=colors.HexColor("#17324D"),
            alignment=TA_LEFT,
            spaceAfter=3,
        ),
        "subtitle": ParagraphStyle(
            "PacketSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.5,
            textColor=colors.HexColor("#34495E"),
        ),
        "heading": ParagraphStyle(
            "PacketHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=colors.HexColor("#17324D"),
            spaceBefore=7,
            spaceAfter=3,
        ),
        "doctor_heading": ParagraphStyle(
            "DoctorHeading",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=9.2,
            leading=10.5,
            textColor=colors.HexColor("#17324D"),
            spaceBefore=4,
            spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "PacketBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=12.5,
            textColor=colors.HexColor("#202B33"),
            spaceAfter=3,
        ),
        "doctor_body": ParagraphStyle(
            "DoctorBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10.1,
            textColor=colors.HexColor("#202B33"),
            leftIndent=7,
            firstLineIndent=-6,
            spaceAfter=1.4,
        ),
        "bullet": ParagraphStyle(
            "PacketBullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.3,
            leading=12.2,
            leftIndent=12,
            firstLineIndent=-7,
            textColor=colors.HexColor("#202B33"),
            spaceAfter=2.5,
        ),
        "small": ParagraphStyle(
            "PacketSmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
            textColor=colors.HexColor("#59636E"),
        ),
        "banner": ParagraphStyle(
            "PacketBanner",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=10.5,
            textColor=colors.HexColor("#17324D"),
        ),
        "banner_body": ParagraphStyle(
            "PacketBannerBody",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=10,
            leftIndent=6,
            firstLineIndent=-5,
            textColor=colors.HexColor("#202B33"),
            spaceAfter=1.2,
        ),
        "index_title": ParagraphStyle(
            "IndexTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=19,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#17324D"),
            spaceAfter=8,
        ),
    }


def _meta_table(spec: dict[str, Any], *, compact: bool) -> Table:
    styles = _styles()
    appointment = spec["appointment"]
    rows = [
        ["Doente", _escape(spec["profile_name"]), "Consulta", _escape(appointment["date"])],
        ["Médico", _escape(appointment["clinician_name"]), "Especialidade", _escape(appointment["specialty"])],
        ["Motivo", _escape(appointment["purpose"]), "Data-limite dos registos", _escape(spec["record_cutoff"])],
    ]
    body_style = styles["doctor_body"] if compact else styles["body"]
    formatted = []
    for row in rows:
        formatted.append(
            [
                Paragraph(f"<b>{row[0]}</b>", body_style),
                Paragraph(row[1], body_style),
                Paragraph(f"<b>{row[2]}</b>", body_style),
                Paragraph(row[3], body_style),
            ]
        )
    table = Table(formatted, colWidths=[23 * mm, 58 * mm, 25 * mm, 63 * mm], hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EEF3F7")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#EEF3F7")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5DF")),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2 if compact else 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 if compact else 3),
            ]
        )
    )
    return table


def _fact_paragraph(fact: dict[str, str], style: ParagraphStyle) -> Paragraph:
    label = EVIDENCE_LABELS[fact["evidence_type"]]
    content = (
        f"- <b>{_escape(fact['date'])}</b> - {_escape(label)}: {_escape(fact['text'])} "
        f"<font color='#59636E'>(Fonte: {_escape(fact['source'])})</font>"
    )
    return Paragraph(content, style)


def _doctor_story(spec: dict[str, Any], attachment_labels: list[str]) -> list[Any]:
    styles = _styles()
    story: list[Any] = [
        Paragraph("Resumo factual para a consulta", styles["doctor_title"]),
        Paragraph(
            "Preparado para consulta rápida a partir dos registos disponíveis. Cada item identifica o tipo de evidência.",
            styles["subtitle"],
        ),
        Spacer(1, 2.5 * mm),
        _meta_table(spec, compact=True),
    ]
    repeat = spec["repeat_visit"]
    doctor = spec["doctor"]
    if repeat["status"] == "confirmed":
        new_facts = doctor["new_since_last_visit"]
        banner_content: list[Any] = [
            Paragraph(
                f"NOVO DESDE A ÚLTIMA CONSULTA — comparação com {_escape(repeat['prior_visit_date'])}",
                styles["banner"],
            )
        ]
        if new_facts:
            banner_content.extend(_fact_paragraph(fact, styles["banner_body"]) for fact in new_facts)
        else:
            banner_content.append(
                Paragraph(
                    "Não foram identificados factos novos relevantes nos registos disponíveis após a consulta anterior.",
                    styles["banner_body"],
                )
            )
        banner = Table([[banner_content]], colWidths=[169 * mm], hAlign="LEFT")
        banner.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFF4CC")),
                    ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#C68A00")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        story.extend([Spacer(1, 3 * mm), banner])

    for key, title in FACT_SECTIONS[1:]:
        facts = doctor[key]
        if not facts:
            continue
        content: list[Any] = [Paragraph(title, styles["doctor_heading"])]
        content.extend(_fact_paragraph(fact, styles["doctor_body"]) for fact in facts)
        story.append(KeepTogether(content))

    if attachment_labels:
        shown = attachment_labels[:5]
        suffix = f"; mais {len(attachment_labels) - 5}" if len(attachment_labels) > 5 else ""
        story.extend(
            [
                Paragraph("Registos incluídos no pacote do doente", styles["doctor_heading"]),
                Paragraph("- " + _escape("; ".join(shown) + suffix), styles["doctor_body"]),
            ]
        )
    story.extend(
        [
            Spacer(1, 2 * mm),
            Paragraph(
                "Preparado pelo doente a partir dos registos disponíveis.",
                styles["small"],
            ),
        ]
    )
    return story


def _patient_story(spec: dict[str, Any]) -> list[Any]:
    styles = _styles()
    appointment = spec["appointment"]
    story: list[Any] = [
        Paragraph("Preparação do doente para a consulta", styles["title"]),
        Paragraph(
            f"Preparado em {_escape(spec['report_date'])} para {_escape(appointment['clinician_name'])} "
            f"({_escape(appointment['specialty'])}). Este documento ajuda a preparar a consulta; não constitui um diagnóstico nem uma prescrição médica.",
            styles["subtitle"],
        ),
        Spacer(1, 4 * mm),
        _meta_table(spec, compact=False),
        Spacer(1, 3 * mm),
    ]
    repeat = spec["repeat_visit"]
    if repeat["status"] == "confirmed":
        story.append(
            Paragraph(
                f"Data de referência para comparação com a consulta anterior: {_escape(repeat['prior_visit_date'])}",
                styles["body"],
            )
        )
    elif repeat["status"] == "uncertain":
        story.append(
            Paragraph(
                "Não foi possível confirmar uma consulta anterior com este médico nos registos disponíveis; não foi feita uma comparação de novos factos para o resumo clínico.",
                styles["body"],
            )
        )

    for section_value in spec["patient"]["sections"]:
        section = _require_mapping(section_value, "patient section")
        block: list[Any] = [Paragraph(_escape(section["title"]), styles["heading"])]
        intro = _optional_text(section, "intro")
        if intro:
            block.append(Paragraph(_escape(intro).replace("\n", "<br/>") , styles["body"]))
        for item in section.get("items", []):
            block.append(Paragraph("- " + _escape(item), styles["bullet"]))
        story.extend(block)

    story.extend(
        [
            Spacer(1, 4 * mm),
            Paragraph(
                "Levar o resumo de uma página para o médico e este pacote. Antes de sair, registar as decisões, instruções exatas sobre medicação, exames pedidos e prazo de seguimento.",
                styles["small"],
            ),
        ]
    )
    return story


def _build_pdf(
    path: Path,
    story: list[Any],
    *,
    pagesize: tuple[float, float],
    title: str,
    page_offset: int = 0,
) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = NumberedDocTemplate(
        path,
        pagesize=pagesize,
        title=title,
        page_offset=page_offset,
    )
    doc.build(story)
    count = len(PdfReader(str(path)).pages)
    if count < 1:
        raise PacketError(f"generated PDF has no pages: {path}")
    return count


def _read_pdf(path: Path) -> PdfReader:
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        result = reader.decrypt("")
        if not result:
            raise PacketError(f"supporting PDF is encrypted and cannot be opened: {path}")
    return reader


def _image_to_pdf(source: Path, destination: Path, pagesize: tuple[float, float]) -> None:
    from reportlab.pdfgen import canvas

    with Image.open(source) as image:
        image.verify()
    with Image.open(source) as image:
        width, height = image.size
    if width <= 0 or height <= 0:
        raise PacketError(f"image has invalid dimensions: {source}")

    page_width, page_height = pagesize
    margin = 12 * mm
    available_width = page_width - (2 * margin)
    available_height = page_height - (2 * margin)
    scale = min(available_width / width, available_height / height)
    draw_width = width * scale
    draw_height = height * scale

    pdf = canvas.Canvas(str(destination), pagesize=pagesize, pageCompression=1)
    pdf.setTitle(source.name)
    pdf.drawImage(
        str(source),
        (page_width - draw_width) / 2,
        (page_height - draw_height) / 2,
        width=draw_width,
        height=draw_height,
        preserveAspectRatio=True,
        mask="auto",
    )
    pdf.showPage()
    pdf.save()


def _prepare_attachments(
    spec: dict[str, Any], temp_dir: Path, pagesize: tuple[float, float]
) -> list[PreparedAttachment]:
    prepared: list[PreparedAttachment] = []
    for index, item_value in enumerate(spec["supporting_documents"], start=1):
        item = _require_mapping(item_value, f"supporting_documents[{index - 1}]")
        source = Path(item["path"]).expanduser().resolve()
        prepared_path = temp_dir / f"attachment-{index:03d}.pdf"
        if source.suffix.lower() == ".pdf":
            reader = _read_pdf(source)
            if not reader.pages:
                raise PacketError(f"supporting PDF has no pages: {source}")
            selected = tuple(item.get("pages") or range(1, len(reader.pages) + 1))
            invalid = [page for page in selected if page > len(reader.pages)]
            if invalid:
                raise PacketError(
                    f"supporting document {source} has {len(reader.pages)} pages; invalid selections: {invalid}"
                )
            writer = PdfWriter()
            for page_number in selected:
                writer.add_page(reader.pages[page_number - 1])
            with prepared_path.open("wb") as handle:
                writer.write(handle)
        else:
            selected = (1,)
            _image_to_pdf(source, prepared_path, pagesize)
        page_count = len(_read_pdf(prepared_path).pages)
        prepared.append(
            PreparedAttachment(
                label=item["label"].strip(),
                record_date=item["record_date"].strip(),
                reason=item["reason"].strip(),
                source_path=source,
                prepared_pdf=prepared_path,
                source_pages=selected,
                page_count=page_count,
            )
        )
    return prepared


def _page_range(start: int, count: int) -> str:
    return str(start) if count == 1 else f"{start}-{start + count - 1}"


def _index_story(
    attachments: list[PreparedAttachment], *, briefing_pages: int, index_pages: int
) -> list[Any]:
    styles = _styles()
    story: list[Any] = [
        Paragraph("Documentos de apoio", styles["index_title"]),
        Paragraph(
            "As páginas-fonte seguintes estão anexadas a este pacote. Os intervalos de páginas referem-se ao PDF final combinado.",
            styles["body"],
        ),
        Spacer(1, 3 * mm),
    ]
    if not attachments:
        story.append(
            Paragraph(
                "Não foram selecionados documentos-fonte de apoio dos registos disponíveis para esta consulta.",
                styles["body"],
            )
        )
        return story

    rows: list[list[Any]] = [
        [
            Paragraph("Documento", styles["small"]),
            Paragraph("Data", styles["small"]),
            Paragraph("Motivo da inclusão", styles["small"]),
            Paragraph("Páginas no pacote", styles["small"]),
        ]
    ]
    next_page = briefing_pages + index_pages + 1
    for attachment in attachments:
        original_pages = ", ".join(str(page) for page in attachment.source_pages)
        label = (
            f"{_escape(attachment.label)}<br/>"
            f"<font color='#59636E'>{_escape(attachment.source_path.name)}; "
            f"páginas da fonte {_escape(original_pages)}</font>"
        )
        rows.append(
            [
                Paragraph(label, styles["small"]),
                Paragraph(_escape(attachment.record_date), styles["small"]),
                Paragraph(_escape(attachment.reason), styles["small"]),
                Paragraph(_page_range(next_page, attachment.page_count), styles["small"]),
            ]
        )
        next_page += attachment.page_count
    table = Table(rows, colWidths=[51 * mm, 23 * mm, 73 * mm, 22 * mm], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE7EF")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#17324D")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7C4CF")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    return story


def _build_index_pdf(
    destination: Path,
    attachments: list[PreparedAttachment],
    *,
    briefing_pages: int,
    pagesize: tuple[float, float],
) -> int:
    assumed_pages = 1
    for _ in range(5):
        actual_pages = _build_pdf(
            destination,
            _index_story(
                attachments,
                briefing_pages=briefing_pages,
                index_pages=assumed_pages,
            ),
            pagesize=pagesize,
            title="Índice de documentos de apoio",
            page_offset=briefing_pages,
        )
        if actual_pages == assumed_pages:
            return actual_pages
        assumed_pages = actual_pages
    raise PacketError("supporting-document index page count did not stabilize")


def _merge_pdfs(inputs: Iterable[Path], destination: Path, *, title: str) -> int:
    writer = PdfWriter()
    for input_path in inputs:
        reader = _read_pdf(input_path)
        for page in reader.pages:
            writer.add_page(page)
    writer.add_metadata({"/Title": title, "/Author": "Preparado pelo doente"})
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as handle:
        writer.write(handle)
    return len(_read_pdf(destination).pages)


def _staging_path(target: Path) -> Path:
    with tempfile.NamedTemporaryFile(
        prefix=f".{target.stem}-", suffix=".pdf", dir=target.parent, delete=False
    ) as handle:
        return Path(handle.name)


def build_packet(spec_path: Path, doctor_output: Path, patient_output: Path) -> dict[str, Any]:
    try:
        raw = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PacketError(f"could not read JSON spec {spec_path}: {exc}") from exc
    spec = _validate_spec(raw)
    pagesize = _page_size(spec)

    doctor_output = doctor_output.resolve()
    patient_output = patient_output.resolve()
    if doctor_output == patient_output:
        raise PacketError("doctor and patient outputs must be different files")
    if doctor_output.suffix.lower() != ".pdf" or patient_output.suffix.lower() != ".pdf":
        raise PacketError("both outputs must use the .pdf extension")

    with tempfile.TemporaryDirectory(prefix="healthpilot-appointment-") as temp_name:
        temp_dir = Path(temp_name)
        attachments = _prepare_attachments(spec, temp_dir, pagesize)
        source_paths = {item.source_path for item in attachments}
        if doctor_output in source_paths or patient_output in source_paths:
            raise PacketError("an output path cannot overwrite a supporting source document")
        attachment_labels = [item.label for item in attachments]

        doctor_temp = temp_dir / "doctor.pdf"
        doctor_pages = _build_pdf(
            doctor_temp,
            _doctor_story(spec, attachment_labels),
            pagesize=pagesize,
            title="Resumo factual para a consulta",
        )
        if doctor_pages != 1:
            raise PacketError(
                f"clinician handout rendered to {doctor_pages} pages; curate lower-value facts until it fits exactly one page"
            )

        patient_briefing = temp_dir / "patient-briefing.pdf"
        briefing_pages = _build_pdf(
            patient_briefing,
            _patient_story(spec),
            pagesize=pagesize,
            title="Preparação do doente para a consulta",
        )
        index_pdf = temp_dir / "supporting-index.pdf"
        index_pages = _build_index_pdf(
            index_pdf,
            attachments,
            briefing_pages=briefing_pages,
            pagesize=pagesize,
        )
        expected_patient_pages = briefing_pages + index_pages + sum(
            item.page_count for item in attachments
        )
        patient_temp = temp_dir / "patient.pdf"
        patient_pages = _merge_pdfs(
            [patient_briefing, index_pdf, *(item.prepared_pdf for item in attachments)],
            patient_temp,
            title="Pacote do doente para a consulta com documentos de apoio",
        )
        if patient_pages != expected_patient_pages:
            raise PacketError(
                f"patient packet has {patient_pages} pages; expected {expected_patient_pages}"
            )

        doctor_output.parent.mkdir(parents=True, exist_ok=True)
        patient_output.parent.mkdir(parents=True, exist_ok=True)
        doctor_stage = _staging_path(doctor_output)
        patient_stage = _staging_path(patient_output)
        try:
            shutil.copyfile(doctor_temp, doctor_stage)
            shutil.copyfile(patient_temp, patient_stage)
            os.replace(doctor_stage, doctor_output)
            os.replace(patient_stage, patient_output)
        finally:
            doctor_stage.unlink(missing_ok=True)
            patient_stage.unlink(missing_ok=True)

    verified_doctor_pages = len(_read_pdf(doctor_output).pages)
    verified_patient_pages = len(_read_pdf(patient_output).pages)
    if verified_doctor_pages != 1 or verified_patient_pages != expected_patient_pages:
        raise PacketError("written outputs failed final page-count verification")

    return {
        "doctor_output": str(doctor_output),
        "doctor_pages": verified_doctor_pages,
        "patient_output": str(patient_output),
        "patient_pages": verified_patient_pages,
        "patient_briefing_pages": briefing_pages,
        "supporting_index_pages": index_pages,
        "supporting_document_pages": sum(item.page_count for item in attachments),
        "supporting_documents": len(attachments),
    }


def _self_test() -> None:
    from reportlab.pdfgen import canvas

    with tempfile.TemporaryDirectory(prefix="healthpilot-appointment-selftest-") as temp_name:
        temp_dir = Path(temp_name)
        source_pdf = temp_dir / "source.pdf"
        pdf = canvas.Canvas(str(source_pdf), pagesize=A4)
        pdf.drawString(72, 760, "Relatório laboratorial de apoio — página 1")
        pdf.showPage()
        pdf.drawString(72, 760, "Relatório laboratorial de apoio — página 2")
        pdf.showPage()
        pdf.save()
        source_image = temp_dir / "source-image.png"
        Image.new("RGB", (900, 600), color=(232, 239, 245)).save(source_image)

        fact = {
            "date": "2026-08-01",
            "text": "O doente refere um novo sintoma com início após a consulta anterior.",
            "evidence_type": "patient_reported",
            "source": "Entrada processada do registo de saúde",
        }
        objective = {
            "date": "2026-08-02",
            "text": "O relatório laboratorial regista o marcador X em 12 unidades.",
            "evidence_type": "objective_record",
            "source": "Relatório laboratorial",
        }
        spec = {
            "profile_name": "Doente de teste",
            "report_date": "2026-08-09",
            "record_cutoff": "2026-08-08",
            "page_size": "A4",
            "appointment": {
                "date": "2026-08-10",
                "clinician_name": "Dr. Teste",
                "specialty": "Medicina interna",
                "purpose": "Seguimento",
            },
            "repeat_visit": {
                "status": "confirmed",
                "prior_visit_date": "2026-07-01",
                "evidence": [
                    {
                        "date": "2026-07-01",
                        "text": "Consulta concluída e documentada.",
                        "source": "Conjunto de exames",
                    }
                ],
            },
            "doctor": {
                "new_since_last_visit": [fact, objective],
                "visit_focus": [fact],
                "objective_results": [objective],
                "current_treatments": [],
                "relevant_history": [],
            },
            "patient": {
                "sections": [
                    {
                        "kind": "appointment_goals",
                        "title": "Objetivos da consulta",
                        "items": ["Compreender o novo sintoma e acordar os passos seguintes."],
                    },
                    {
                        "kind": "situation_summary",
                        "title": "Resumo da situação",
                        "items": ["Um resumo conciso para o doente."],
                    },
                    {
                        "kind": "new_since_last_visit",
                        "title": "Novidades desde a última consulta",
                        "items": ["Foram registados um novo sintoma e um novo resultado laboratorial."],
                    },
                    {
                        "kind": "current_status",
                        "title": "Sintomas, tratamentos e reações atuais",
                        "items": ["Estado atual a reconciliar na consulta."],
                    },
                    {
                        "kind": "objective_evidence",
                        "title": "Evidência objetiva",
                        "items": ["Relatório laboratorial datado de 2026-08-02."],
                    },
                    {
                        "kind": "working_hypotheses",
                        "title": "Hipóteses de trabalho e diagnóstico diferencial",
                        "items": ["Diagnóstico diferencial — efeito do tratamento ou alteração não relacionada."],
                    },
                    {
                        "kind": "questions_to_ask",
                        "title": "Perguntas a fazer",
                        "items": ["Que achado alteraria o plano de tratamento?"],
                    },
                    {
                        "kind": "source_coverage",
                        "title": "Cobertura das fontes e limitações",
                        "items": ["Foram analisados resultados laboratoriais, exames e o registo de saúde."],
                    },
                    {
                        "kind": "appointment_checklist",
                        "title": "Lista de verificação para a consulta",
                        "items": ["Levar ambos os PDF e as embalagens da medicação atual."],
                    },
                    {
                        "kind": "after_visit_capture",
                        "title": "Registo após a consulta",
                        "items": ["Registar decisões, exames, alterações à medicação e prazo de seguimento."],
                    },
                ]
            },
            "supporting_documents": [
                {
                    "path": str(source_pdf),
                    "label": "Relatório laboratorial",
                    "record_date": "2026-08-02",
                    "reason": "Sustenta o resultado objetivo",
                    "pages": [2],
                },
                {
                    "path": str(source_image),
                    "label": "Imagem de exame",
                    "record_date": "2026-08-03",
                    "reason": "Sustenta o achado documentado no exame",
                }
            ],
        }
        spec_path = temp_dir / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        result = build_packet(
            spec_path,
            temp_dir / "doctor.pdf",
            temp_dir / "patient.pdf",
        )
        assert result["doctor_pages"] == 1
        assert result["supporting_documents"] == 2
        assert result["supporting_document_pages"] == 2
        assert result["patient_pages"] == (
            result["patient_briefing_pages"] + result["supporting_index_pages"] + 2
        )
        doctor_text = "\n".join(
            page.extract_text() or "" for page in PdfReader(result["doctor_output"]).pages
        )
        assert "NOVO DESDE A ÚLTIMA CONSULTA" in doctor_text
        assert "Hipóteses de trabalho" not in doctor_text
        assert "Perguntas a fazer" not in doctor_text

        first_visit = json.loads(json.dumps(spec))
        first_visit["repeat_visit"] = {"status": "not_found", "evidence": []}
        first_visit["doctor"]["new_since_last_visit"] = []
        first_visit["patient"]["sections"] = [
            section
            for section in first_visit["patient"]["sections"]
            if section["kind"] != "new_since_last_visit"
        ]
        first_visit["supporting_documents"] = []
        first_visit_path = temp_dir / "first-visit-spec.json"
        first_visit_path.write_text(json.dumps(first_visit), encoding="utf-8")
        first_visit_result = build_packet(
            first_visit_path,
            temp_dir / "first-visit-doctor.pdf",
            temp_dir / "first-visit-patient.pdf",
        )
        first_visit_doctor_text = "\n".join(
            page.extract_text() or ""
            for page in PdfReader(first_visit_result["doctor_output"]).pages
        )
        assert "NOVO DESDE A ÚLTIMA CONSULTA" not in first_visit_doctor_text
        assert first_visit_result["supporting_documents"] == 0

        broken = json.loads(json.dumps(spec))
        broken["doctor"]["visit_focus"][0]["text"] = "Considerar um diagnóstico provável."
        try:
            _validate_spec(broken)
        except PacketError:
            pass
        else:  # pragma: no cover - defensive assertion
            raise AssertionError("analysis language should be rejected from clinician facts")

        leaked = json.loads(json.dumps(spec))
        leaked["doctor"]["visit_focus"][0]["source"] = "/Users/test/private/source.md"
        try:
            _validate_spec(leaked)
        except PacketError as exc:
            assert "private path or parser artifact" in str(exc)
        else:  # pragma: no cover - defensive assertion
            raise AssertionError("private source paths should be rejected from rendered output")

        oversized = json.loads(json.dumps(spec))
        oversized["doctor"]["objective_results"] = [objective] * 120
        oversized_path = temp_dir / "oversized-spec.json"
        oversized_path.write_text(json.dumps(oversized), encoding="utf-8")
        try:
            build_packet(
                oversized_path,
                temp_dir / "oversized-doctor.pdf",
                temp_dir / "oversized-patient.pdf",
            )
        except PacketError as exc:
            assert "rendered to" in str(exc) and "exactly one page" in str(exc)
        else:  # pragma: no cover - defensive assertion
            raise AssertionError("an oversized clinician handout should be rejected")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", nargs="?", type=Path, help="UTF-8 JSON packet specification")
    parser.add_argument("--doctor-output", type=Path, help="one-page clinician PDF")
    parser.add_argument("--patient-output", type=Path, help="patient briefing and supporting records PDF")
    parser.add_argument("--self-test", action="store_true", help="run built-in end-to-end checks")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        print("self-test passed")
        return 0
    if args.spec is None or args.doctor_output is None or args.patient_output is None:
        parser.error("spec, --doctor-output, and --patient-output are required")

    try:
        result = build_packet(args.spec, args.doctor_output, args.patient_output)
    except PacketError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
