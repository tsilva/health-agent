---
name: healthpilot-medication-sheet
description: Create or update a one-page, colour-coded current-medication PDF for a specified live Healthpilot profile. Use when the user asks for a printable medication table, medication-box schedule, colour-coded medication sheet, or an updated version of an existing medication-table PDF; do not use for a full treatment-history report alone.
---

# Healthpilot Medication Sheet

Create one practical A4 PDF in European Portuguese (`pt-PT`) showing the selected profile's reconciled current medication schedule. Preserve the visual language of the Lígia reference sheet: clear metadata, time-of-day colour bands, dose and administration columns, a monitoring callout when relevant, and a small reconciliation note.

## Required companion skills and rules

1. Follow the live-profile selection and source-validation rules in the project `AGENTS.md`.
2. Apply the retrieval, status-precedence, and safety rules from `healthpilot-report-treatment-record`. Generate its Markdown report only if the user also asks for it.
3. Load and follow the available `pdf:pdf` skill before authoring. Run its artifact-operation marker exactly once, render the final PDF to PNG, inspect the complete page, and use its final output-citation format.
4. Treat every profile-linked source as read-only. A named existing sheet is a visual/retrieval reference, never an output target.

## Reconcile before rendering

- Start with the latest explicit current-medication list, then apply later starts, dose changes, pauses, restarts, stops, and clinician instructions.
- Put only `confirmed active`, `likely active`, and `active PRN/intermittent` items in the schedule.
- Omit completed finite courses. Put unresolved current candidates in the confirmation note instead of silently including or excluding them.
- A medicine taken at multiple times may appear in multiple schedule rows.
- In `DOSE`, show the amount actually administered. In `COMO TOMAR`, preserve the tablet/capsule strength and fraction when needed, for example `1/2 comprimido de 20 mg` with dose `10 mg`.
- Do not infer a strength, formulation, route, indication, or start/stop status. Surface the ambiguity in `CONFIRMAR`.
- Include treatment-linked monitoring thresholds and finite trial dates prominently when they affect safe daily use.

## Layout decisions

Use these default sections when supported by the regimen:

- morning / breakfast: yellow
- a fixed afternoon time: pink
- dinner / night: blue
- SOS, intermittent, or monthly: grey

Create additional sections only when the schedule requires them. Keep the sheet to one A4 page. If the renderer reports overflow, shorten explanatory prose and confirmations without removing any medication name, administered dose, timing, route, or safety threshold. If the complete regimen still cannot fit safely, stop and ask whether a two-page version is acceptable.

## Build workflow

1. Read [references/spec-schema.md](references/spec-schema.md).
2. Write the private intermediate JSON to `tmp/pdfs/{profile_slug}-medication-sheet-{YYYYMMDD}/spec.json`.
3. Use the local report date and write the PDF to:

   `.output/{profile_slug}/treatment-record/{YYYY-MM-DD}-{profile_slug}-tabela-medicacao-atualizada-colorida.pdf`

4. Load the bundled workspace dependencies and run the renderer with its Python executable:

```bash
"$BUNDLED_PYTHON" .codex/skills/healthpilot-medication-sheet/scripts/render_medication_sheet.py \
  --spec tmp/pdfs/{profile_slug}-medication-sheet-{YYYYMMDD}/spec.json \
  --output .output/{profile_slug}/treatment-record/{YYYY-MM-DD}-{profile_slug}-tabela-medicacao-atualizada-colorida.pdf
```

5. Validate the PDF and its content:

```bash
"$BUNDLED_PYTHON" .codex/skills/healthpilot-medication-sheet/scripts/validate_medication_sheet.py \
  --spec tmp/pdfs/{profile_slug}-medication-sheet-{YYYYMMDD}/spec.json \
  --pdf .output/{profile_slug}/treatment-record/{YYYY-MM-DD}-{profile_slug}-tabela-medicacao-atualizada-colorida.pdf
```

6. Render at least at 150 DPI and visually inspect the final page. Fix clipped text, overlaps, weak contrast, ambiguous fractions, and unreadably small type. Re-run validation after the final change.

## Handoff

Deliver exactly one PDF unless the user requested another artifact. State that the original source was preserved, summarize material medication changes and any confirmation flags, and cite the final PDF exactly once using the PDF skill's output citation.
