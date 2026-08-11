---
name: healthpilot-profile-interview
description: Ask a selected live Healthpilot profile's highest-yield unanswered questions interactively, then write a paste-ready Markdown health-log entry under `.output/{profile_slug}/profile-interview/`. Use when the user wants profile-specific follow-up questions, wants to fill important record gaps, or wants their answers converted into a health-log entry for future Healthpilot analysis.
---

# Profile Health-Log Interview

Run an interactive interview for the selected live profile, then generate a paste-ready first-person health-log entry.

## Required session rules

1. Follow the session-start and source-validation rules in `AGENTS.md`.
2. Treat every profile-linked source as read-only.
3. Write the draft under `.output/{profile_slug}/profile-interview/`.
4. Do not create new `.state/` artifacts.
5. Never write into the configured external `health_log_path`.

## Retrieval

1. Load the selected live profile and classify every configured source as `available`, `missing`, `unreadable`, or `not configured`.
2. Check `.state/profiles/{profile_slug}/issues.json` for unresolved gaps and `actions.json` for supporting context.
3. Read `{health_log_path}/health_log.md`, recent `entries/*.processed.md`, and targeted `entries/*.raw.md` when exact wording matters.
4. Pull labs, standalone exams, and genetics only as needed to prove whether a question remains unanswered and material.

## Select questions

Ask exactly 10 questions when the record supports 10 meaningful gaps. Ask fewer rather than padding, and state why in the generated entry metadata.

Include a question only when its answer could materially:

- change diagnosis ranking
- change treatment class or specialist path
- resolve missing objective evidence
- clarify whether a concerning issue remains active
- distinguish treatment benefit from adverse effect
- establish important chronology, severity, triggers, or response

Exclude questions already answered in the record, generic wellness prompts, vague intake questions, and low-value curiosity.

Rank questions in the order above.

## Run the interview

Prefer the structured question tool when available. Ask in batches of at most three: questions 1–3, 4–6, 7–9, then 10.

For each structured prompt:

- use a stable `snake_case` answer id
- keep the header at 12 characters or fewer
- provide two or three mutually exclusive options
- tell the user to use the free-form answer for dates, severity, medication names, tests, specialist guidance, or other detail
- do not add an `Other` option when the tool supplies it automatically

Preserve answers closely enough to retain dates, qualifiers, and uncertainty. If the structured tool is unavailable, ask a numbered list and wait for the answers before writing the draft.

## Draft the entry

Read [references/report-template.md](references/report-template.md) before drafting.

Write in first person from the user's perspective. Group related answers when useful. Preserve uncertainty with phrases such as `I am unsure`, `I do not remember`, or `I have not answered`. Never invent answers, dates, severity, treatments, test results, or specialist advice.

Include `Not answered / still unclear` only for skipped, ambiguous, or uncertain answers. Keep the question list out of the final artifact unless a short appendix is necessary to explain missing answers.

## Output contract

- directory: `.output/{profile_slug}/profile-interview/`
- filename: `{YYYY-MM-DD}-{profile_slug}-health-log-entry.md`
- canonical path: `.output/{profile_slug}/profile-interview/{YYYY-MM-DD}-{profile_slug}-health-log-entry.md`

Use the local report date and canonical profile slug. Refresh the same-day canonical file instead of creating an alternate. Include profile name and source status, and explicitly disclose unavailable sources.
