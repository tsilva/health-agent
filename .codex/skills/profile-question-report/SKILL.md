---
name: profile-question-report
description: Generate a dated markdown report for a selected live health-agent profile with a short ranked list of unanswered questions the user should answer in their next health-log entry to improve future agent reasoning.
---

# Profile Question Report

Generate a standalone repo-local markdown report for the selected live profile.

Use this when the user wants a profile-specific question list that will help the agent do a better job on later runs after the answers are added to the health log.

## Required Session Rules

1. Follow the session-start and source-validation rules in `AGENTS.md`.
2. Treat all profile-linked external sources as read-only.
3. Write the user-facing report under `.output/`.
4. Do not create new `.state/` artifacts for this workflow.

## Goal

Produce a short ranked list of the highest-yield unanswered questions for that profile.

The questions should help the next run by clarifying:

- diagnosis ranking
- treatment-path recommendations
- specialist direction
- important chronology or response-pattern gaps that materially change interpretation

Do not pad the report with broad intake questions, generic wellness prompts, or low-value curiosity items.

## Retrieval Order

1. Read the selected live profile and classify each configured source as `available`, `missing`, `unreadable`, or `not configured`.
2. Check repo-local memory first when available:
   - `.state/profiles/{profile_slug}/issues.json` for unresolved issue gaps
   - `.state/profiles/{profile_slug}/actions.json` only as supporting context
3. Use the latest health-log context next:
   - `{health_log_path}/health_log.md`
   - recent `entries/*.processed.md`
   - recent `entries/*.raw.md` only when exact wording matters
4. Pull labs, standalone exams, and genetics only as needed to confirm whether a question is already answered or still materially open.
5. Prefer the shortest path that can prove a question is still worth asking.

## Question Selection Rules

Include questions only when the answer would likely change future recommendations in a meaningful way.

Prefer questions that would:

- narrow a real differential
- clarify whether a symptom pattern is episodic, persistent, or triggered
- distinguish medication or supplement benefit vs side effect
- clarify whether prior testing or specialist guidance already happened
- identify missing objective data that would change the next step

Exclude questions that are already clearly answered in the record, including cases where the answer appears repeatedly across sources.

Also exclude:

- vague prompts like "How is your lifestyle?"
- generic optimization questions with no record support
- exhaustive history-taking that is unlikely to change the plan now

## Ranking Rules

Rank questions in this order:

1. answers that could materially change diagnosis ranking
2. answers that could change treatment class or specialist path
3. answers that resolve a key missing objective-evidence gap
4. answers that clarify whether a concerning issue is still active
5. foundational context questions for sparse records

Keep the final list short enough that a user is likely to answer it in one new health-log entry.

## Output

Write the report under `.output/` using this filename:

`{profile_slug}/{YYYY-MM-DD}-{profile_slug}-future-questions.md`

Use [references/report-template.md](references/report-template.md) as the starting structure.

## Report Rules

- Keep the report concise and ranked.
- Questions should be written as direct prompts the user can answer in a new health-log entry.
- Do not add a rationale block under each question.
- Add a short note near the top telling the user to answer the questions in a new health-log entry so the next run can ingest them.
- If a source is unavailable, say so explicitly and adjust the questions to that narrower evidence base.
- If the record is already strong in one area, add a brief optional section for questions that are mostly answered already so the user does not waste time repeating them.
