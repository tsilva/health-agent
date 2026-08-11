# Appointment packet content and build contract

Use this contract to draft the appointment packet and call `scripts/build_packet.py`.

## Clinician handout content order

1. Patient, appointment, clinician/specialty, purpose, and record cutoff
2. `NEW SINCE LAST VISIT` only for a confirmed repeat visit
3. `Visit focus`
4. `Objective results`
5. `Current relevant treatments and reactions`
6. `Relevant documented history`
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
    "date": "YYYY-MM-DD or Date not provided",
    "clinician_name": "Dr. Name or Not provided",
    "specialty": "Specialty or Not provided",
    "purpose": "Short appointment purpose"
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
        "title": "Appointment goals",
        "intro": "Optional short paragraph.",
        "items": ["First preparation item", "Second preparation item"]
      },
      {
        "kind": "situation_summary",
        "title": "Situation summary",
        "items": ["Concise dated summary of the issue and functional impact."]
      },
      {
        "kind": "new_since_last_visit",
        "title": "New since the last visit",
        "items": ["Material facts after the confirmed prior-visit cutoff."]
      },
      {
        "kind": "current_status",
        "title": "Current symptoms, treatments, and reactions",
        "items": ["Current status to reconcile during the visit."]
      },
      {
        "kind": "objective_evidence",
        "title": "Objective evidence",
        "items": ["Dated labs, exams, imaging, or procedures relevant to this visit."]
      },
      {
        "kind": "working_hypotheses",
        "title": "Working hypotheses and differential",
        "items": [
          "Differential - Hypothesis: evidence for; evidence against; what would change the assessment."
        ]
      },
      {
        "kind": "questions_to_ask",
        "title": "Questions to ask",
        "items": ["Question for the clinician?"]
      },
      {
        "kind": "source_coverage",
        "title": "Source coverage and limitations",
        "items": ["Available and unavailable sources that affect confidence."]
      },
      {
        "kind": "appointment_checklist",
        "title": "Appointment checklist",
        "items": ["Bring both PDFs and reconcile current medications."]
      },
      {
        "kind": "after_visit_capture",
        "title": "After-visit capture",
        "items": ["Working diagnosis and confidence", "Tests ordered and timing", "Treatment changes", "Follow-up trigger and date"]
      }
    ]
  },
  "supporting_documents": [
    {
      "path": "/absolute/read-only/path/to/source.pdf",
      "label": "CBC and chemistry panel",
      "record_date": "YYYY-MM-DD",
      "reason": "Contains the objective result discussed in the briefing",
      "pages": [1, 2]
    }
  ]
}
```

Use `repeat_visit.status` as `confirmed`, `uncertain`, or `not_found`. A confirmed repeat requires a clinician name, a prior-visit date, and at least one evidence item. `pages` are one-based PDF page numbers; omit `pages` to include the full PDF. PNG, JPEG, TIFF, BMP, and WebP images are supported as one-page attachments and must not specify `pages`.

Every section needs a unique lowercase `kind` for structural validation and a human-facing `title` that may be localized. The patient `sections` list is flexible, but normally use this order:

1. Appointment goals
2. Situation summary
3. New since the last visit
4. Current symptoms and functional impact
5. Current medications, supplements, treatments, allergies, and adverse reactions
6. Objective evidence
7. Working hypotheses and differential
8. Questions to ask
9. Tests or treatment classes to discuss
10. What findings would change the plan
11. Source coverage and limitations
12. Appointment checklist
13. After-visit capture

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

Use Healthpilot's confidence frames exactly: `clear conclusion`, `likely diagnosis`, `differential`, or `open question`. Attribute every clinically material assertion to a dated record or clearly mark it as inference. For rendered `source` values and patient text, use report-safe evidence IDs or human-readable labels; never place absolute paths or parser metadata in either PDF. Absolute paths are permitted only in the non-rendered `supporting_documents[].path` build field.

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

The builder rejects clinician fact text containing common analysis or request language, including `hypothesis`, `differential`, `likely`, `consider`, `rule out`, `recommend`, `request`, `question`, or `should`. Rewrite these as attributed facts or move them to the patient briefing.

Acceptable:

- `2026-07-21 - Patient reports nightly calf pain beginning after the medication dose increased.`
- `2026-07-28 - MRI report documents a 6 mm finding.`
- `Since 2026-07-30 - Medication X 10 mg nightly is documented as active.`

Patient briefing only:

- `Could medication X explain the timing of the calf pain?`
- `Differential: medication effect versus mechanical pain.`
- `Ask whether repeat imaging would change management.`
