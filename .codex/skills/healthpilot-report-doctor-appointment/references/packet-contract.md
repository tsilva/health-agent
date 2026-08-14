# Appointment packet content and build contract

Use this contract to draft the appointment packet and call `scripts/build_packet.py`.

## Output language

Write every rendered string in both PDFs in European Portuguese (`pt-PT`), including spec-supplied titles, facts, questions, source labels, document labels, reasons for inclusion, and all builder-generated titles, metadata, tables, callouts, footers, and index text. Preserve only proper names, original source-document titles, report-safe evidence IDs, established abbreviations, and short quotations whose original wording matters. JSON keys, `kind`, `evidence_type`, and status enum values remain in canonical English because they are machine-readable.

## Clinician handout content order

1. Patient, appointment, clinician/specialty, purpose, and record cutoff
2. `NOVO DESDE A ÚLTIMA CONSULTA` only for a confirmed repeat visit
3. `Motivo da consulta`
4. `Resultados objetivos`
5. `Tratamentos atuais relevantes e reações`
6. `Antecedentes documentados relevantes`
7. Short list of supporting records included in the patient packet

Omit empty lower sections. Keep the most decision-relevant content first. The builder uses compact typography but will fail rather than silently make a two-page clinician handout.

## Fact model

Every clinician fact must use this shape:

```json
{
  "date": "YYYY-MM-DD or a concise interval",
  "text": "One neutral factual sentence.",
  "evidence_type": "objective_record",
  "source": "Short human-readable source label"
}
```

Allowed `evidence_type` values:

- `objective_record`
- `patient_reported`
- `documented_treatment`
- `documented_history`

Use `patient_reported` for symptoms or history stated by the patient even when a health log recorded them. Use `objective_record` only for measured or observed results in a lab, exam, imaging, procedure, or clinician note. Keep `source` short; do not expose the profile's absolute filesystem paths in the PDF.

## Build spec

The spec is UTF-8 JSON:

```json
{
  "profile_name": "Patient Name",
  "report_date": "YYYY-MM-DD",
  "record_cutoff": "YYYY-MM-DD",
  "page_size": "A4",
  "appointment": {
    "date": "YYYY-MM-DD ou Data não fornecida",
    "clinician_name": "Dr. Nome ou Não fornecido",
    "specialty": "Especialidade ou Não fornecida",
    "purpose": "Motivo breve da consulta"
  },
  "repeat_visit": {
    "status": "confirmed",
    "prior_visit_date": "YYYY-MM-DD",
    "evidence": [
      {
        "date": "YYYY-MM-DD",
        "text": "Completed consultation with Dr. Name documented.",
        "source": "Processed health-log entry"
      }
    ]
  },
  "doctor": {
    "new_since_last_visit": [],
    "visit_focus": [],
    "objective_results": [],
    "current_treatments": [],
    "relevant_history": []
  },
  "patient": {
    "sections": [
      {
        "kind": "appointment_goals",
        "title": "Objetivos da consulta",
        "intro": "Parágrafo introdutório breve e opcional.",
        "items": ["Primeiro ponto de preparação", "Segundo ponto de preparação"]
      },
      {
        "kind": "situation_summary",
        "title": "Resumo da situação",
        "items": ["Resumo conciso e datado do problema e do impacto funcional."]
      },
      {
        "kind": "new_since_last_visit",
        "title": "Novidades desde a última consulta",
        "items": ["Factos relevantes posteriores à consulta anterior confirmada."]
      },
      {
        "kind": "current_status",
        "title": "Sintomas, tratamentos e reações atuais",
        "items": ["Estado atual a reconciliar durante a consulta."]
      },
      {
        "kind": "objective_evidence",
        "title": "Evidência objetiva",
        "items": ["Análises, exames, imagiologia ou procedimentos datados e relevantes para esta consulta."]
      },
      {
        "kind": "working_hypotheses",
        "title": "Hipóteses de trabalho e diagnóstico diferencial",
        "items": [
          "Diagnóstico diferencial — hipótese: evidência a favor; evidência contra; o que alteraria a avaliação."
        ]
      },
      {
        "kind": "questions_to_ask",
        "title": "Perguntas a fazer",
        "items": ["Pergunta para o médico?"]
      },
      {
        "kind": "source_coverage",
        "title": "Cobertura das fontes e limitações",
        "items": ["Fontes disponíveis e indisponíveis que afetam a confiança."]
      },
      {
        "kind": "appointment_checklist",
        "title": "Lista de verificação para a consulta",
        "items": ["Levar ambos os PDF e reconciliar a medicação atual."]
      },
      {
        "kind": "after_visit_capture",
        "title": "Registo após a consulta",
        "items": ["Diagnóstico de trabalho e confiança", "Exames pedidos e prazos", "Alterações ao tratamento", "Critério e data de seguimento"]
      }
    ]
  },
  "supporting_documents": [
    {
      "path": "/absolute/read-only/path/to/source.pdf",
      "label": "Hemograma e painel bioquímico",
      "record_date": "YYYY-MM-DD",
      "reason": "Contém o resultado objetivo referido na preparação",
      "pages": [1, 2]
    }
  ]
}
```

Use `repeat_visit.status` as `confirmed`, `uncertain`, or `not_found`. A confirmed repeat requires a clinician name, a prior-visit date, and at least one evidence item. `pages` are one-based PDF page numbers; omit `pages` to include the full PDF. PNG, JPEG, TIFF, BMP, and WebP images are supported as one-page attachments and must not specify `pages`.

Every section needs a unique lowercase `kind` for structural validation and a human-facing `title` written in `pt-PT`. The patient `sections` list is flexible, but normally use this order:

1. Objetivos da consulta
2. Resumo da situação
3. Novidades desde a última consulta
4. Sintomas atuais e impacto funcional
5. Medicação, suplementos, tratamentos, alergias e reações adversas atuais
6. Evidência objetiva
7. Hipóteses de trabalho e diagnóstico diferencial
8. Perguntas a fazer
9. Exames ou classes terapêuticas a discutir
10. Achados que alterariam o plano
11. Cobertura das fontes e limitações
12. Lista de verificação para a consulta
13. Registo após a consulta

Required `kind` values are:

- `appointment_goals`
- `situation_summary`
- `current_status`
- `objective_evidence`
- `questions_to_ask`
- `source_coverage`
- `appointment_checklist`
- `after_visit_capture`

Also require `new_since_last_visit` for a confirmed repeat visit. Useful optional kinds include `working_hypotheses`, `tests_treatments_to_discuss`, and `plan_changers`. Other lowercase underscore-separated kinds are allowed.

Render Healthpilot's confidence frames as `conclusão clara`, `diagnóstico provável`, `diagnóstico diferencial`, or `questão em aberto`; internal state may retain the canonical English enum values. Attribute every clinically material assertion to a dated record or clearly mark it as inference. For rendered `source` values and patient text, use report-safe evidence IDs or human-readable labels; never place absolute paths or parser metadata in either PDF. Absolute paths are permitted only in the non-rendered `supporting_documents[].path` build field.

## Supporting-document selection

Include a document only if it supports a fact, question, or decision likely to arise at this appointment.

- Prefer the original report over a parser summary.
- For lab PDFs, use `all.csv` source and page fields to select the relevant original page when reliable; include adjacent interpretation/range pages when needed.
- For exams and imaging, include the signed/final report and only useful images. Do not append hundreds of raw images by default.
- Preserve original page content and order.
- If the only usable evidence is CSV, Markdown, or structured JSON, render a clearly labeled derived excerpt to PDF first and identify its source and generation date.
- Do not append the same source twice under different filenames.
- If no defensible supporting document exists, use an empty list. The generated index will say so.

## Clinician-language guardrail

The builder rejects clinician fact text containing common analysis or request language in Portuguese or English, including `hipótese`, `diagnóstico diferencial`, `provável`, `considerar`, `a excluir`, `recomendar`, `pedir`, `pergunta`, and their English equivalents. Rewrite these as attributed facts or move them to the patient briefing.

Acceptable:

- `2026-07-21 — O doente refere dor noturna na barriga da perna desde o aumento da dose da medicação.`
- `2026-07-28 — O relatório da RM documenta um achado de 6 mm.`
- `Desde 2026-07-30 — A medicação X 10 mg à noite está documentada como ativa.`

Patient briefing only:

- `A medicação X poderá explicar a cronologia da dor na barriga da perna?`
- `Diagnóstico diferencial: efeito da medicação ou dor mecânica.`
- `Perguntar se repetir a imagiologia alteraria a orientação clínica.`
