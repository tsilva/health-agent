---
name: unresolved-issue-review
description: Maintain repo-local unresolved issue records, action queue state, and action-plan reports for health-agent profiles. This is the lower-level stateful workflow behind the broader `what-next-report` skill. Use it when the task specifically centers on unresolved-issue tracking or when durable issue state needs to be refreshed.
---

# Unresolved Issue Review

Use this workflow when the task specifically needs durable unresolved-issue state, not as the default user-facing entrypoint.

For normal "what should I do next?" requests, prefer the `what-next-report` skill and treat this workflow as internal support.

## Goals

- persist unresolved issues under `.state/issues/`
- keep `.state/action-queue.json` ranked by decision impact
- write a single review report under `.output/`
- update the recommendation when the user returns with new evidence

## Required Session Rules

1. Follow the profile and source-validation rules from `AGENTS.md`.
2. Treat external profile-linked sources as read-only.
3. Keep all durable repo-local state under `.state/`.
4. Keep all human-readable review artifacts under `.output/`.

## Stable Artifacts

- `IssueRecord`: `.state/issues/{issue_slug}.json`
- `ActionQueue`: `.state/action-queue.json`
- `OutcomeUpdate`: `.state/outcome-updates/{YYYY-MM-DD}-{issue_slug}.json`
- `ActionPlanReport`: `.output/{profile_slug}-action-plan-{YYYY-MM-DD}.md`

Templates live under `.state/template/`. Schemas live under `schemas/`.

## Flow

### 1. Intake

Use intake when there is no durable issue state yet, or when a fresh pass over the record should create or rewrite issue files.

- identify the important unresolved issues from the record
- create one `IssueRecord` JSON file per issue under `.state/issues/`
- set `priority_context` booleans so ranking is explicit instead of implied
- run:

```bash
python3 -m health_agent intake --profile <profile-name>
```

If you generated issue drafts outside `.state/issues/`, sync them with:

```bash
python3 -m health_agent intake --profile <profile-name> --issues-from <file-or-dir>
```

### 2. Review

Use review when issue files already exist and the user wants the latest “what do I do next?” output.

- refresh the issue conclusions if the evidence changed
- keep one prescriptive next step per active or monitoring issue
- run:

```bash
python3 -m health_agent review --profile <profile-name>
```

### 3. Outcome Update

Use outcome-update when the user returns with a new lab, exam, visit, symptom change, or treatment result.

- write an `OutcomeUpdate` JSON file
- revise the corresponding `IssueRecord` if the new evidence changes the conclusion or next step
- run:

```bash
python3 -m health_agent outcome-update --profile <profile-name> --update-file <outcome.json> --revised-issue <issue.json>
```

If the new evidence should be logged immediately but the issue interpretation is still pending, omit `--revised-issue` for the first pass, then come back and update the issue record after review.

## Issue Authoring Rules

Each issue must end in a concrete operator format:

- `Do next`
- `Why`
- `What to ask for`
- `What result to return with`

Use `priority_context` to encode the ranking rule directly:

- `materially_narrows_differential`
- `changes_treatment_or_specialist_path`
- `resolves_missing_objective_evidence`
- `reduces_risk_if_delayed`
- `is_lower_value_optimization`

Prefer the earliest true bucket that honestly matches the action.

Also include `profile_slug` in every issue record so multiple live profiles do not share the same issue pool by accident.

## Output Quality

- Keep issue titles short and stable so they survive across sessions.
- Preserve prior evidence when revising an issue; do not drop older evidence just because a new visit happened.
- Mark resolved issues as `resolved` instead of deleting them.
- Use absolute file paths in `linked_sources` and outcome attachments whenever possible.
