---
name: what-next-report
description: Generate a dated what-next report for a selected live health-agent profile. Use when the user wants a prescriptive "what should I do next?" answer, a current action report, or an updated report after new labs, exams, visit feedback, or symptom changes. The report should include both unresolved-issue actions and health-optimization actions when the data supports them.
---

# What Next Report

This is the default high-level workflow for the repo.

When the user invokes this skill, the expected output is simple:

- read the selected live profile
- validate the configured sources
- synthesize the best next actions from the record
- write one dated report under `.output/`

State files under `.state/` are implementation details. Use them when helpful, but do not make the user think about them unless they explicitly ask.

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

## Output

Write a report named:

`{profile_slug}-what-next-{YYYY-MM-DD}.md`

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

If durable issue records already exist under `.state/issues/`, use them as memory and refresh them when helpful.

If the report clearly centers on unresolved issues, you may also update:

- `.state/issues/`
- `.state/action-queue.json`
- `.state/profile-cache/{profile_slug}.json`

But the primary deliverable is always the report in `.output/`.

## Update Mode

When the user brings a new lab, exam, visit, or symptom update:

- revise the conclusions that actually changed
- keep the prior evidence that still matters
- rerank the next actions
- regenerate the dated what-next report

If internal state updates help, use them. If not, keep the task simple and just regenerate the report.
