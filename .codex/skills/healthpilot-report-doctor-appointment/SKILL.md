---
name: healthpilot-report-doctor-appointment
description: "Generate a two-PDF appointment packet for a selected live Healthpilot profile: a respectful, facts-only clinician handout constrained to exactly one page and a patient briefing of any necessary length with relevant lab, exam, imaging, or other source-document pages merged into it. Use when the user is preparing for a doctor, clinician, specialist, consultation, or follow-up appointment, especially when a named clinician appears in prior-visit evidence and changes since that visit need to stand out."
---

# Doctor Appointment Packet

Generate both PDFs and every user-facing companion artifact in European Portuguese (`pt-PT`), including titles, headings, metadata, tables, callouts, footers, and builder-generated text. Preserve original source-document titles or short quotations only when source fidelity requires it.

Create exactly two final PDFs for one appointment:

1. a one-page clinician fact summary; and
2. a patient briefing followed by the supporting documents worth printing and taking.

Read [references/packet-contract.md](references/packet-contract.md) before drafting. Also follow the available `pdf` skill for PDF generation, rendering, inspection, and delivery.
Read [../_shared/healthpilot-report-contract.md](../_shared/healthpilot-report-contract.md) for the bucketed output and evidence-sanitization rules; the Markdown ordering and validator do not apply to this two-PDF artifact.

## Session and privacy rules

1. Follow the live-profile and source-validation rules in `AGENTS.md`.
2. Treat every profile-linked source as read-only.
3. Use a clinician name only when the user supplied it or the selected profile's record identifies it. Do not recommend arbitrary named clinicians.
4. Write final artifacts only under `.output/{profile_slug}/doctor-appointment/` and temporary PDF work under `tmp/pdfs/`.
5. Distinguish objective records, documented treatments/history, and patient-reported facts. Do not silently turn a report into an objective finding.
6. Use local date, profile slug, and clinician slug in canonical paths. Refresh same-day canonical files instead of creating alternates.
7. Never put credentials, hidden source paths, unsupported diagnoses, or internal reasoning in either PDF.

## Inputs

Resolve from the prompt and record when possible:

- selected live profile
- appointment date, if known
- clinician name, if known
- specialty or clinic, if known
- purpose of the appointment

Do not block on a missing appointment date or clinician name. Use `Data não fornecida`, `Não fornecido`, or a short specialty slug when necessary. Ask only when the missing detail would make the packet unsafe or useless.

## Retrieval workflow

1. Load the selected live profile and classify every configured source as `available`, `missing`, `unreadable`, or `not configured`.
2. Search the health log and standalone exams for the clinician, close name variants, clinic, specialty, consultation, follow-up, and appointment purpose.
3. Establish whether this is a repeat visit using the rules below.
4. Set a record cutoff and retrieve evidence relevant to this appointment:
   - use standalone exams as the primary source for exams, imaging, procedures, and specialist findings;
   - use `health_log.md`, relevant processed entries, and targeted raw entries for symptoms, treatment changes, chronology, and prior visits;
   - use `all.csv` for lab trends and its `source_file` / `page_number` fields to locate printable source pages;
   - use genetics or lifestyle sources only when they materially affect this appointment.
5. Prefer recent, decision-changing evidence over exhaustive history. Verify ambiguous parser output against source pages before presenting it as fact.
6. Select only supporting documents that are likely to help during the visit. Prefer original PDFs and exact relevant pages. Avoid duplicate, unreadable, superseded, or merely tangential material.

## Repeat-visit comparison

Mark `repeat_visit.status` as `confirmed` only when the record supports a completed earlier visit with the same named clinician. Strong evidence includes a dated consultation/exam naming that clinician or a dated health-log entry clearly stating the visit occurred.

Do not confirm a repeat visit from:

- a referral, recommendation, booking, or planned appointment alone;
- the same specialty without a clinician identity match;
- a clinician name appearing only in an address or recipient field;
- an uncertain name match that could refer to someone else.

When confirmed:

1. use the latest completed visit with that clinician as the comparison cutoff;
2. identify only material facts first observed, measured, started, stopped, or changed after that cutoff;
3. place `NOVO DESDE A ÚLTIMA CONSULTA` immediately below the clinician handout header;
4. include the prior-visit date and concise dated facts;
5. if no material new facts are supported, state that rather than filling the box with old information.

When evidence is incomplete, use `uncertain`, omit the clinician-facing new-since banner, and explain the uncertainty only in the patient briefing.

## Clinician PDF rules

The clinician PDF must be exactly one page and must value the clinician's review time.

- Present facts only: the appointment focus, symptom chronology, objective results, current relevant treatments, allergies/adverse reactions, and concise documented history.
- Label evidence as `Objective record`, `Patient-reported`, `Documented treatment`, or `Documented history`.
- Use dated facts and short source labels where possible.
- Include a documented diagnosis only as an attributed record fact.
- Use neutral phrasing such as `Patient reports...`, `Lab on DATE showed...`, or `Report dated DATE documents...`.
- Do not include hypotheses, differentials, probabilities, diagnostic conclusions, requests, recommended tests, suggested treatments, or questions.
- Do not tell the clinician what to do and do not imply that undiscovered conclusions are established.
- Do not mention AI. The footer may say `Prepared by the patient from available records.`
- Curate instead of shrinking. If it does not fit legibly, remove lower-value facts from the clinician page and retain them in the patient briefing.

## Patient PDF rules

The patient PDF may be as long as necessary. It should help the patient prepare, ask good questions, and capture the outcome.

Include:

- appointment goals and a concise situation summary;
- `New since the last visit` with its comparison date when repeat status is confirmed;
- current symptoms, treatments, allergies/adverse reactions, and objective evidence;
- working hypotheses or differential with Healthpilot confidence frames when defensible;
- evidence supporting and weakening each hypothesis;
- questions to ask, and when appropriate tests or treatment classes to discuss and the data that would change the plan;
- a reconciliation/checklist section and space or prompts for after-visit notes;
- source coverage and important unavailable evidence;
- a supporting-document index followed by the selected source pages merged into this same PDF.

Keep hypotheses and requests in the patient PDF, not the clinician PDF. Frame them as preparation for discussion, not demands or diagnoses.

## Build the two PDFs

1. Load the bundled workspace dependencies and use its Python runtime.
2. Create a JSON build spec following [references/packet-contract.md](references/packet-contract.md).
3. Run:

```bash
<bundled-python> .codex/skills/healthpilot-report-doctor-appointment/scripts/build_packet.py \
  tmp/pdfs/appointment-spec.json \
  --doctor-output .output/{profile_slug}/doctor-appointment/{YYYY-MM-DD}-{profile_slug}-appointment-{clinician_slug}-doctor.pdf \
  --patient-output .output/{profile_slug}/doctor-appointment/{YYYY-MM-DD}-{profile_slug}-appointment-{clinician_slug}-patient.pdf
```

The builder rejects a clinician handout longer than one page, rejects analysis language in clinician facts, creates the patient supporting-document index, and merges selected PDF/image records into the patient PDF.

## Output contract

- directory: `.output/{profile_slug}/doctor-appointment/`
- filename: `{YYYY-MM-DD}-{profile_slug}-appointment-{clinician_slug}-doctor.pdf`
- filename: `{YYYY-MM-DD}-{profile_slug}-appointment-{clinician_slug}-patient.pdf`

Use a short lowercase filesystem-safe clinician slug. If no clinician is known, use the specialty or `doctor`. These are the only two final user-facing artifacts.

## Required QA

1. Reopen both PDFs with `pypdf`.
2. Require exactly one page in the clinician PDF.
3. Require the patient PDF page count to equal generated briefing pages plus supporting-index pages plus all selected source pages.
4. Extract text and confirm that clinician content contains no patient-only questions, hypotheses, diagnostic suggestions, or treatment requests.
5. Confirm each selected supporting document appears in the patient index and is present at its listed page range.
6. Render every page to PNG with Poppler. Inspect the clinician page and every generated patient page at high resolution; inspect representative pages from each appended source document and any page with unusual dimensions.
7. Check for clipping, overlap, unreadable fonts, broken glyphs, poor contrast, accidental blank pages, wrong rotation, and illegible source scans.
8. If a supporting page is unreadable, replace it with a better source or disclose the omission in the patient briefing. Do not pretend it is included.
9. Delete temporary specs, split pages, and rendered QA images after validation.

Do not deliver until both PDFs pass structural and visual QA.
