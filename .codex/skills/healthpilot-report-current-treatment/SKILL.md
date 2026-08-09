---
name: healthpilot-report-current-treatment
description: Generate a dated, evidence-reconciled snapshot of the medications, supplements, therapies, devices, lifestyle treatments, monitoring, and other treatments a selected live Healthpilot profile is currently doing. Use when the user asks for current meds, an active treatment list, a current regimen, medication reconciliation, or a present-tense treatment report rather than a historical timeline.
---

# Current Treatment Report

Generate a concise present-tense snapshot of what the selected person is actually taking or doing now. Keep planned, merely recommended, uncertain, and completed treatments separate from the confirmed current regimen.

## Required Session Rules

1. Follow the live-profile selection and source-validation rules in `AGENTS.md`.
2. Treat all profile-linked external sources as read-only.
3. Write the report under `.output/{profile_slug}/`.
4. Use `.state/` as retrieval support only; verify current status in canonical sources.
5. Distinguish observed evidence from inference. Do not invent dose, route, frequency, indication, prescriber, adherence, response, or stop date.
6. Produce a reconciliation snapshot, not new treatment advice, unless the user separately asks for recommendations.

## Scope

Include current items from these categories when supported by the record:

- prescription medications
- over-the-counter medications and as-needed rescue medicines
- vitamins, minerals, herbal products, performance products, and other supplements
- psychotherapy, physiotherapy, rehabilitation, injections, infusions, wound care, and other ongoing clinical therapies
- devices such as CPAP, braces, compression garments, glucose monitors, or prescribed assistive equipment
- clinician-directed or clearly active nutrition, exercise, sleep, recovery, and behavioral treatments
- self-directed experiments that are still running, labeled as self-directed
- ongoing monitoring or surveillance that is part of the current care plan

Do not treat an isolated behavior, ordinary food, historical procedure, diagnosis, lab test, or future appointment as a treatment unless the record explicitly makes it part of an active regimen.

## Retrieval Workflow

1. Load the selected live profile and classify every configured source as `available`, `missing`, `unreadable`, or `not configured`.
2. Generate or refresh the factual evidence packet when helpful:

```bash
healthpilot evidence-packet --profile <profile-name>
python3 -m healthpilot evidence-packet --profile <profile-name>
```

3. Start with explicit current-stack or current-regimen sections in `{health_log_path}/health_log.md`.
4. Read the latest relevant `entries/*.processed.md` and `entries/*.raw.md` to confirm starts, stops, dose changes, adherence, PRN use, response, adverse effects, and whether a planned trial actually began.
5. Inspect the standalone exam corpus for recent medication lists, prescriptions, clinician treatment plans, device use, therapies, monitoring, and documented discontinuations. Treat imported visit medication lists as evidence, not automatic proof of adherence.
6. Use `entries/*.exams.md` as supporting context, not a substitute for an available standalone exam corpus.
7. Read configured nutrition, exercise, schedule, and lifestyle-constraint Markdown. Treat them as templates or intended plans unless the health log or another current source supports actual ongoing use.
8. Use labs only to document treatment monitoring, response, or a dose-linked timeline. A lab result alone does not prove that a treatment is active.
9. Use genetics only when the record explicitly links a genotype to current treatment selection or dosing. Do not perform speculative pharmacogenomic interpretation for this snapshot.
10. Read `.state/profiles/{profile_slug}/evidence-packet.json`, `issues.json`, and `actions.json` when present, but treat planned actions as planned until canonical evidence confirms execution.
11. Add every configured source category to the coverage ledger, even when it contributed no current treatment evidence.

Prefer targeted retrieval with `rg`, dated file ordering, and small direct reads. Read broader history only far enough back to resolve whether a current item was started, stopped, replaced, or never begun.

## Status Rules

Assign exactly one reconciliation status to every item:

- `confirmed active`: the latest reliable evidence explicitly states current use or continuation
- `likely active`: recent repeated evidence supports use, but no current-state statement fully confirms it
- `active PRN/intermittent`: current access or intended episodic use is supported; record last known use when available
- `planned/recommended—not confirmed started`: discussed, prescribed, ordered, or proposed without evidence of execution
- `unclear—needs reconciliation`: evidence is stale, incomplete, or conflicting
- `recently stopped/completed`: a discontinuation or completed course is supported

Only the first three statuses belong in the current medication, supplement, or non-medication treatment tables.

Apply these precedence rules:

1. Prefer the latest explicit start, continuation, dose-change, stop, or nonadherence statement over older lists.
2. Prefer a patient's dated statement of actual use over a copied-forward medication list when they conflict, while preserving the conflict.
3. Do not assume that `prescribed`, `recommended`, `consider`, `discuss`, `ordered`, or `plan to start` means started.
4. Treat a finite course as completed after its documented end or duration unless later evidence supports continuation.
5. Treat `PRN` as current only when the record supports continued intended availability or use; do not convert one historical dose into an active PRN regimen.
6. Preserve unresolved dose, route, frequency, brand/generic, and stop-date conflicts verbatim in the uncertainty column.
7. Deduplicate clear synonyms and brand/generic pairs, but do not merge products with materially different ingredients or formulations.
8. Label origin as `prescribed`, `clinician-directed`, `self-directed`, or `unclear` only when supported.

Use Healthpilot confidence framing narrowly: place directly supported current-state conclusions under `clear conclusion` and uncertain status under `open question`. Do not force `likely diagnosis` or `differential` labels onto medication reconciliation.

## Report Requirements

Use [references/report-template.md](references/report-template.md) as the starting structure.

For every current medication or supplement, include when available:

- normalized name plus recorded brand
- reconciliation status
- dose/strength, formulation, route, frequency, and timing
- prescribed, clinician-directed, self-directed, or unclear origin
- indication or target, explicitly labeled `inferred` if not directly stated
- start date or earliest supported current use
- latest confirmation date
- adherence, response, and adverse effects
- direct source citation

For non-medication treatments, include the category, protocol or schedule, target, origin, latest confirmation, adherence, response, and evidence.

Include planned/recommended treatments, unclear items, and recent stops in their own sections so they cannot be mistaken for active treatment. Keep historical context brief; direct full timeline requests to `healthpilot-report-medication-history`.

## Reconciliation and Safety

- Surface dose conflicts, duplicate active listings, unclear ingredient overlap, recorded allergies, documented adverse effects, missed monitoring, and ambiguous stop instructions as `reconciliation flags`.
- Do not independently diagnose an interaction or contraindication without researching it and clearly labeling that additional analysis. A simple current-regimen request does not require external medical research.
- Never tell the user to start, stop, taper, or change a medication in this snapshot.
- If the canonical record documents an acute severe reaction or dangerous administration error, include a concise urgent safety note and identify the appropriate care level.
- If no active items are supported, say so explicitly; do not turn older mentions into a current regimen to fill the report.

## Output Contract and Validation

Follow the common Healthpilot report convention:

- directory: `.output/{profile_slug}/`
- filename: `{YYYY-MM-DD}-{profile_slug}-current-treatment.md`
- canonical path: `.output/{profile_slug}/{YYYY-MM-DD}-{profile_slug}-current-treatment.md`

Use the local report date and canonical profile slug. If regenerating on the same date, refresh the canonical file instead of creating an alternate filename.

Validate the finished report:

```bash
python3 .codex/skills/healthpilot-report-current-treatment/scripts/validate_report.py \
  .output/{profile_slug}/{YYYY-MM-DD}-{profile_slug}-current-treatment.md
```

Fix every validator error. In the user-facing answer, link the report and summarize the number of current items, the record cutoff date, source gaps, and the most important reconciliation question.
