# Shared Healthpilot Report Contract

Apply this contract to every user-facing Markdown report. Doctor-appointment PDFs keep their specialized packet contract but use the same path and evidence-sanitization rules.

## Output layout

Write to `.output/{profile_slug}/{report_bucket}/`. Every filename starts with the local report date as `YYYY-MM-DD` and retains the profile slug. Same-day regeneration replaces the canonical file.

Canonical report buckets are `what-next`, `root-cause`, `treatment-record`, `organ-system-health`, `mortality-risk`, `doctor-appointment`, `profile-interview`, and `daily-plan`.

Keep up to three companion artifacts beside the report. For four or more, use `{report_bucket}/assets/{YYYY-MM-DD}-{artifact_slug}/`. Start every newly generated companion filename with the same report date.

## Required Markdown order

1. Title and metadata
2. Report-specific decision section
3. `## Changes since previous report`
4. Supporting analysis and full tables
5. `## Evidence appendix`

The first decision heading must appear within the first 40 nonblank lines. Keep source coverage and methodology inside the evidence appendix.

Required metadata labels are:

- `Report generated`
- `Record cutoff`
- `Evidence snapshot`: include packet snapshot ID and generation time
- `Previous comparable report`: report-safe filename or `none`
- `Source-gap severity`: exactly `none`, `minor`, `material`, or `critical`

Keep `confidence frame`, `evidence confidence`, and `urgency` separate. Do not use confidence language as a substitute for urgency.

## Change tracking

Compare with the latest earlier report in the same profile bucket and with the same artifact identity. Root-cause identity includes the query slug.

- First report: write exactly `Baseline report; no prior comparable artifact was found.`
- Repeat report: classify every material change as `Added`, `Changed`, `Resolved`, or `Unchanged`, and cite current canonical evidence.
- If new source material produces no material report change, state that explicitly.
- A previous report is comparison context, never clinical evidence.

## Evidence appendix and privacy

Include source coverage, unavailable sources, methodology when needed, evidence references, and limitations. Use report-safe evidence IDs from the v2 evidence packet:

- `[LAB:date:marker]`
- `[HL:date:kind:Lline]`
- `[EXAM:date:document]`
- `[GEN:rsid]`
- `[LIFE:type:Lline]`

Never print absolute paths, `file://` links, parser comments, `.DS_Store`, `.state.json`, `.review-artifacts`, `DEPS:` metadata, or placeholder snapshot text. The private citation index under `.state/` resolves report-safe IDs back to local evidence.

State unavailable sources explicitly even when the answer is otherwise well supported.

## Main-body budgets

The budget ends before `## Evidence appendix`:

- What Next: 1,800 words
- Root Cause: 2,500 words
- Treatment Record: 3,000 words
- Organ/System Health: 2,500 words
- Mortality Risk: 2,500 words

Move audit detail into the appendix rather than deleting clinically relevant evidence or uncertainty.

## Shared validation

Run before handoff:

```bash
python3 -m healthpilot validate-report \
  --type <report-type> \
  --report .output/{profile_slug}/{report_bucket}/{filename} \
  [--previous .output/{profile_slug}/{report_bucket}/{previous-filename}]
```

Fix every shared-validator error, then run any report-specific validator.
