---
name: healthpilot-report-organ-system-health
description: Generate a dated Healthpilot report that scores every major organ and bodily system from 0 to 10 using all available data, ranks systems from lowest to highest health score, provides organ/subsystem detail, and separates health evidence from data confidence. Use when the user asks for organ health scores, a whole-body system ranking, weakest or healthiest body systems, or a comprehensive 0–10 health assessment for a selected live profile.
---

# Organ System Health Report

Generate a whole-body, evidence-auditable snapshot of current organ and system health. Use `10` for the strongest evidenced health and `0` for acute critical failure. Sort the main system table from lowest score to highest so the most concerning or uncertain domains appear first.

Treat every score as a nonvalidated Healthpilot decision-support rating, not a diagnosis, prognosis, percentage, clinical grade, or substitute for organ-specific testing.

## Required Session Rules

1. Follow the live-profile selection and source-validation rules in `AGENTS.md`.
2. Treat all profile-linked external sources as read-only.
3. Write the report under `.output/{profile_slug}/organ-system-health/`.
4. Use `.state/` only as retrieval support; verify material conclusions in canonical sources.
5. Distinguish observed evidence, inference, and missing data.
6. Use age- and sex-appropriate interpretation from the profile. Cite current authoritative evidence when a high-impact interpretation depends on external guidelines or ranges not already supplied by the record.

## Required Inventory

Read [references/system-inventory.md](references/system-inventory.md) before retrieval and scoring.

Score all 16 canonical systems and all listed core organs/subsystems. Add extra organ rows when the record contains relevant evidence not covered by the core inventory. Do not silently omit a system because no data exists; assign the neutral uncertainty score defined by the rubric and mark confidence `Low`.

Keep system scores and organ/subsystem scores separate. A system score is an integrated judgment, not necessarily the arithmetic mean of its components.

## Complete Data Retrieval

Consider every configured source category that is `available`, and show all configured sources in a coverage ledger.

1. Load the live profile, calculate current age, and validate labs, exams, health log, genetics, lifestyle Markdown, and SelfDecode configuration.
2. Generate or refresh the factual evidence packet when helpful:

```bash
healthpilot evidence-packet --profile <profile-name>
python3 -m healthpilot evidence-packet --profile <profile-name>
```

3. Use `.state/profiles/{profile_slug}/evidence-packet.json` as an index, not sufficient evidence for high-impact scoring.
4. Scan `{labs_path}/all.csv` across all dates. Map trends, abnormalities, reference ranges, parser-review flags, and normal results to relevant systems. Use `lab_specs.json` and source pages when units, ranges, or OCR are ambiguous.
5. Inspect the complete standalone exam corpus. Retrieve diagnoses, vital signs, physical findings, imaging, pathology, procedures, functional tests, endoscopy, sleep studies, screening, and clinician assessments.
6. Read `health_log.md` and relevant processed entries for symptoms, functional capacity, quality-of-life impact, treatments, response, adverse effects, recovery, and chronology. Use raw entries when exact wording, severity, timing, or triggers affect a score.
7. Read current medication, supplement, therapy, device, monitoring, nutrition, exercise, schedule, and lifestyle-constraint evidence. Treatment can improve control or reveal disease burden, but treatment presence alone does not prove dysfunction or health.
8. Use genetics only as risk or mechanism context. A variant does not establish current organ dysfunction without phenotype evidence; give common small-effect variants little or no current-health weight.
9. Read `.state/profiles/{profile_slug}/issues.json`, `actions.json`, and prior reports when present, but verify source evidence and avoid propagating stale conclusions.
10. Search older records only far enough to determine persistence, resolution, recurrence, or trajectory.

“All available data” means every source category is considered and every clinically relevant datum is mapped. It does not mean the same cross-system signal should be counted repeatedly.

## Scoring Method

Read [references/scoring-rubric.md](references/scoring-rubric.md) and apply it consistently.

Score five dimensions from `0` to `2` in half-point increments:

1. structural integrity
2. physiologic function
3. symptoms and real-world functional impact
4. disease burden and control
5. trajectory, reserve, and resilience

Sum the five dimensions to produce the `0–10` score. If a dimension lacks evidence, assign `1.0`, not `2.0`. Therefore, a completely unassessed system receives `5.0/10`, `Low` evidence confidence, and a wide plausible range; this means indeterminate, not half-healthy or diseased.

For each score, provide:

- a one-decimal score in 0.5 increments
- a plausible range clamped to 0–10
- evidence confidence: `High`, `Moderate`, or `Low`
- driver: `impairment-driven`, `uncertainty-driven`, `mixed`, or `healthy-evidenced`
- dated supporting evidence
- dated normal, protective, or contradicting evidence
- missing data most likely to change the score

## Evidence Weighting

Prioritize evidence in this order:

1. acute failure, direct pathology, definitive imaging, procedure findings, and organ-specific functional testing
2. repeated objective abnormalities or normal findings with relevant clinical context
3. diagnosed disease plus documented severity and control
4. persistent symptoms and real-world functional impairment
5. treatment response, recovery, and longitudinal trajectory
6. single mild abnormalities, indirect markers, lifestyle risk, family history, and genetics

Apply these controls:

- Weight current and persistent evidence more than old resolved episodes.
- Do not treat absence of symptoms or documentation as proof of health.
- Do not let one mild lab abnormality dominate a system without corroboration.
- Do not count a systemic finding such as anemia, inflammation, obesity, or fatigue as direct dysfunction in every affected system. Score it directly where it belongs and note cross-system effects separately.
- Do not use a normal unrelated test to clear an entire system.
- Do not infer diagnosis, severity, or treatment indication from a medication name alone.
- Score current health, not lifetime disease risk, mortality risk, athletic performance, or the importance of the organ.

## Report Requirements

Use [references/report-template.md](references/report-template.md) as the starting structure.
Read [../_shared/healthpilot-report-contract.md](../_shared/healthpilot-report-contract.md) and apply it in full.

The report must contain:

1. `Lowest-scoring systems` decision table with the bottom five, evidence confidence, driver, urgency, and next useful data point
2. `Changes since previous report`
3. score meaning and methodology
4. exactly 16 canonical system scores sorted lowest to highest
5. all core organ/subsystem scores from the inventory
6. detailed explanations for the five lowest system scores
7. cross-system findings with double-counting controls
8. missing data that would most change scores
9. an evidence appendix containing source coverage, unavailable sources, safety notes, limitations, and report-safe citations

For each of the five lowest-scoring systems, state:

- `working conclusion`
- Healthpilot `confidence frame`
- five dimension subscores
- strongest observed supporting evidence
- contradicting or reassuring evidence
- whether the low score is impairment-driven or uncertainty-driven
- next best test, monitoring step, or specialist discussion
- result that would most change the score

Use `clear conclusion` only for directly established findings, `likely diagnosis` for a best-fit diagnosis not proven, `differential` when multiple explanations remain, and `open question` when the score primarily reflects inadequate data.

## Safety and Interpretation

- Put acute red flags or possible organ failure above the ranking with appropriate urgency.
- Never tell the user to start, stop, or change prescription treatment solely because of a score.
- Do not compute a whole-body average; it can hide a severely impaired system and implies unsupported weighting.
- Do not compare scores across different people. The rubric is designed for within-profile prioritization and longitudinal refreshes.
- When refreshing a prior report, show material score changes and the evidence responsible; do not preserve old scores mechanically.

## Output Contract and Validation

Follow the common Healthpilot report convention:

- directory: `.output/{profile_slug}/organ-system-health/`
- filename: `{YYYY-MM-DD}-{profile_slug}-organ-system-health.md`
- canonical path: `.output/{profile_slug}/organ-system-health/{YYYY-MM-DD}-{profile_slug}-organ-system-health.md`

Use the local report date and canonical profile slug. If regenerating on the same date, refresh the canonical file instead of creating an alternate filename.

Validate the finished report:

```bash
python3 -m healthpilot validate-report \
  --type organ-system-health \
  --report .output/{profile_slug}/organ-system-health/{YYYY-MM-DD}-{profile_slug}-organ-system-health.md \
  [--previous .output/{profile_slug}/organ-system-health/{previous-filename}]

python3 .codex/skills/healthpilot-report-organ-system-health/scripts/validate_report.py \
  .output/{profile_slug}/organ-system-health/{YYYY-MM-DD}-{profile_slug}-organ-system-health.md
```

Fix every validator error. In the user-facing answer, link the report and summarize the lowest three systems, whether low scores reflect impairment or uncertainty, unavailable sources, and the single most valuable next data point.
