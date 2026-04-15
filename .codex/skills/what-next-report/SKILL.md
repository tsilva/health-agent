---
name: what-next-report
description: Generate a dated what-next report for a selected live health-agent profile. Use when the user wants a prescriptive "what should I do next?" answer, a current action report, or an updated report after new labs, exams, visit feedback, or symptom changes. The report should include both unresolved-issue actions and health-optimization actions when the data supports them.
---

# What Next Report

This is the canonical high-level workflow for the repo.

When the user invokes this skill, the expected output is simple:

- read the selected live profile
- validate the configured sources
- rescan the current parsed source folders
- synthesize the best next actions from the record
- write one dated report under `.output/`

State files under `.state/` are implementation details. Use them when helpful, but do not make the user think about them unless they explicitly ask.

The expected user experience is simple: they ask the agent for next steps, this skill does the end-to-end work, and the report appears under `.output/`.

## Goals

- generate a single prescriptive report that answers "what should I do next?"
- include unresolved-issue actions when the record supports them
- also include broader health-optimization actions when they are actionable and evidence-backed
- keep outputs concise, ranked, and easy to follow

## Required Session Rules

1. Follow the profile and source-validation rules from `AGENTS.md`.
2. Treat external profile-linked sources as read-only.
3. Write the user-facing report under `.output/`.
4. Use `.state/` only as internal memory or ranking support.

## Working Order

Default to the shortest path that still produces a defensible current report.

1. Start with a focused current-evidence pass:
   - latest relevant labs from `all.csv`
   - latest relevant standalone exam summaries
   - latest relevant `health_log.md` and `entries/*.processed.md` updates
2. If `.state/profiles/{profile_slug}/issues.json` and `.state/profiles/{profile_slug}/actions.json` already exist, use them as internal memory and refresh them when the current evidence changes the plan.
3. If that state does not exist yet, do a first-run synthesis directly from the parsed record:
   - identify the main unresolved issues from the current evidence
   - write the report anyway on that first pass
   - optionally create `.state/profiles/{profile_slug}/issues.json`, `.state/profiles/{profile_slug}/actions.json`, and `.state/profiles/{profile_slug}/sources.json` after the reasoning is complete
   - do not stop just because repo-local state is empty
4. Pull older landmark findings only when they still change the current plan.
5. Do not detour into a broad historical reread unless the current evidence is too thin to rank next actions.
6. Use the built-in repo helper only as internal support when it reduces deterministic file work:

```bash
health-agent plan --profile <profile-name>
python3 -m health_agent plan --profile <profile-name>
```

Do not frame the CLI as the primary user interface. The skill itself is the primary interface.

## Output

Write a report named:

`{profile_slug}/{YYYY-MM-DD}-{profile_slug}-action-plan.md`

The durable repo-local artifacts for this workflow are:

- `IssueStore`: `.state/profiles/{profile_slug}/issues.json`
- `ActionStore`: `.state/profiles/{profile_slug}/actions.json`
- `SourceSnapshot`: `.state/profiles/{profile_slug}/sources.json`
- `ActionPlanReport`: `.output/{profile_slug}/{YYYY-MM-DD}-{profile_slug}-action-plan.md`

The report should usually contain:

1. Title
2. `Report generated`
3. `Profile`
4. `Source status`
5. `Top next actions`
6. `Unresolved issues`
7. `Optimization opportunities`
8. `What to return with`

## Report Content Rules

### Top Next Actions

Rank the best actions across both categories:

- unresolved diagnosis or workup actions
- follow-up or surveillance actions
- treatment-discussion actions
- optimization actions for sleep, GI function, exercise, recovery, diet, or other high-value areas

Do not include vague filler. Prefer a short ranked list of concrete actions.

For each ranked action, include:

- `Do next`
- `Why`
- `What to ask for` or `What to do`
- `What to return with`

### Unresolved Issues

Include the important unresolved issues that materially affect health or decision-making.

For each issue, state:

- `working conclusion`
- `confidence frame`
- the strongest supporting evidence
- the next step that would most change the plan

### Optimization Opportunities

Include only if they are supported by the record and worth acting on now.

Examples:

- sleep optimization based on symptoms, sleep studies, or diary patterns
- GI optimization based on recurring symptoms and response patterns
- exercise or biomechanics changes when the record suggests a likely mechanical driver
- supplement or medication timing or trial cleanups when the record shows confusion or repeated unclear reactions

Do not pad the report with generic lifestyle advice.

## Prioritization Rules

Rank actions in this order:

1. actions that materially narrow a differential
2. actions that could change treatment class or specialist path
3. actions that resolve missing objective evidence
4. actions that reduce risk if delayed
5. high-value optimization actions supported by the record
6. lower-value curiosity or cleanup actions

## Using Repo State

If durable issue records already exist under `.state/profiles/{profile_slug}/issues.json`, use them as memory and refresh them when helpful.

If repo state does not exist yet, the skill must still complete the task from the parsed source folders alone. Empty `.state/` is a normal first-run condition, not a blocker.

If the report clearly centers on unresolved issues, you may also update:

- `.state/profiles/{profile_slug}/issues.json`
- `.state/profiles/{profile_slug}/actions.json`
- `.state/profiles/{profile_slug}/sources.json`

But the primary deliverable is always the report in `.output/`.

When refreshing issue memory:

- identify the important unresolved issues from the current record
- keep `priority_context` explicit so ranking is encoded rather than implied
- preserve older evidence that still affects the current plan
- mark resolved issues as `resolved` instead of deleting them

Each issue record should:

- include `profile_slug`
- keep `linked_sources` as absolute file paths when possible
- end in an operator-friendly format:
  - `Do next`
  - `Why`
  - `What to ask for`
  - `What result to return with`

Use `priority_context` to encode the ranking bucket directly:

- `materially_narrows_differential`
- `changes_treatment_or_specialist_path`
- `resolves_missing_objective_evidence`
- `reduces_risk_if_delayed`
- `is_lower_value_optimization`

## Update Mode

When the user brings a new lab, exam, or health-log update:

- revise the conclusions that actually changed
- keep the prior evidence that still matters
- rerank the next actions
- regenerate the dated what-next report

Treat the parsed source folders as the canonical input. Do not ask the user to create a separate repo-local outcome JSON file.
