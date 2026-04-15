---
name: unresolved-issue-review
description: Maintain repo-local per-profile issue memory and action-plan state for health-agent profiles. This is an internal support workflow behind `what-next-report`, not the default user-facing entrypoint.
---

# Unresolved Issue Review

Use this workflow only when the task specifically needs durable per-profile issue memory refreshed, not as the default user-facing entrypoint.

For normal "what should I do next?" requests, prefer the `what-next-report` skill and treat this workflow as internal support.

## Goals

- persist unresolved issues under `.state/profiles/{profile_slug}/issues.json`
- keep `.state/profiles/{profile_slug}/actions.json` ranked by decision impact
- write a single review report under `.output/`
- update the recommendation when parsed source folders change

## Required Session Rules

1. Follow the profile and source-validation rules from `AGENTS.md`.
2. Treat external profile-linked sources as read-only.
3. Keep all durable repo-local state under `.state/`.
4. Keep all human-readable review artifacts under `.output/`.

## Stable Artifacts

- `IssueStore`: `.state/profiles/{profile_slug}/issues.json`
- `ActionStore`: `.state/profiles/{profile_slug}/actions.json`
- `SourceSnapshot`: `.state/profiles/{profile_slug}/sources.json`
- `ActionPlanReport`: `.output/{profile_slug}/{YYYY-MM-DD}-{profile_slug}-action-plan.md`

## Flow

### 1. Rescan

Use a rescan whenever the parsed source folders changed or when a fresh pass over the record should rewrite the issue memory.

- identify the important unresolved issues from the record
- update `.state/profiles/{profile_slug}/issues.json`
- set `priority_context` booleans so ranking is explicit instead of implied
- run:

```bash
python3 -m health_agent plan --profile <profile-name>
```

Treat the parsed source folders as the canonical input. Do not ask the user to create a separate repo-local outcome JSON file.

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
- Preserve prior evidence when revising an issue; do not drop older evidence just because new parsed data arrived.
- Mark resolved issues as `resolved` instead of deleting them.
- Use absolute file paths in `linked_sources` whenever possible.
