"""Action ranking and state serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from healthpilot.constants import PRIORITY_BUCKETS


PRIORITY_LABELS = {
    "materially_narrows_differential": "Materially narrows the differential",
    "changes_treatment_or_specialist_path": "Could change treatment class or specialist path",
    "resolves_missing_objective_evidence": "Resolves missing objective evidence",
    "reduces_risk_if_delayed": "Reduces risk if delayed",
    "lower_value_optimization": "Lower-value optimization",
}

EXPECTED_PAYOFF = {
    "materially_narrows_differential": "High diagnostic clarification",
    "changes_treatment_or_specialist_path": "High downstream treatment impact",
    "resolves_missing_objective_evidence": "Closes a key evidence gap",
    "reduces_risk_if_delayed": "Reduces time-sensitive downside",
    "lower_value_optimization": "Optimization or monitoring value",
}


@dataclass(slots=True)
class RankedAction:
    issue_slug: str
    issue_title: str
    do_next: str
    why: str
    specialist_type: str
    what_to_ask_for: list[str]
    what_result_to_return_with: str
    priority_bucket: str
    expected_payoff: str
    related_issues: list[str]
    source_citations: list[str]

    def dedupe_key(self) -> str:
        return self.do_next.strip().lower()


def determine_priority_bucket(issue_payload: dict[str, Any]) -> str:
    context = issue_payload.get("priority_context", {}) or {}
    if context.get("materially_narrows_differential"):
        return PRIORITY_BUCKETS[0]
    if context.get("changes_treatment_or_specialist_path"):
        return PRIORITY_BUCKETS[1]
    if context.get("resolves_missing_objective_evidence"):
        return PRIORITY_BUCKETS[2]
    if context.get("reduces_risk_if_delayed"):
        return PRIORITY_BUCKETS[3]
    if context.get("is_lower_value_optimization"):
        return PRIORITY_BUCKETS[4]

    confidence = issue_payload["confidence_frame"]
    if confidence in {"differential", "open question"}:
        return PRIORITY_BUCKETS[0]
    if issue_payload["specialist_type"] and issue_payload["tests_or_discussions_to_request"]:
        return PRIORITY_BUCKETS[1]
    if issue_payload["result_that_would_change_plan"]:
        return PRIORITY_BUCKETS[2]
    return PRIORITY_BUCKETS[4]


def build_ranked_actions(issues: dict[str, dict[str, Any]]) -> list[RankedAction]:
    actions: list[RankedAction] = []
    for slug, issue in issues.items():
        if issue["status"] not in {"active", "monitoring"}:
            continue
        bucket = determine_priority_bucket(issue)
        actions.append(
            RankedAction(
                issue_slug=slug,
                issue_title=issue["title"],
                do_next=issue["next_best_action"],
                why=issue["why_this_action_now"],
                specialist_type=issue["specialist_type"],
                what_to_ask_for=issue["tests_or_discussions_to_request"],
                what_result_to_return_with=issue["result_that_would_change_plan"],
                priority_bucket=bucket,
                expected_payoff=EXPECTED_PAYOFF[bucket],
                related_issues=[slug],
                source_citations=list(issue.get("linked_sources", [])),
            )
        )

    actions.sort(
        key=lambda action: (
            PRIORITY_BUCKETS.index(action.priority_bucket),
            action.issue_title.lower(),
            action.do_next.lower(),
        )
    )
    return actions


def dedupe_actions(actions: list[RankedAction]) -> list[RankedAction]:
    deduped: list[RankedAction] = []
    seen: dict[str, RankedAction] = {}
    for action in actions:
        key = action.dedupe_key()
        if key not in seen:
            seen[key] = action
            deduped.append(action)
            continue
        existing = seen[key]
        if action.issue_slug not in existing.related_issues:
            existing.related_issues.append(action.issue_slug)
        for citation in action.source_citations:
            if citation not in existing.source_citations:
                existing.source_citations.append(citation)
    return deduped


def build_action_queue_payload(
    profile_slug: str,
    profile_name: str,
    generated_at: str,
    issues: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    ranked = dedupe_actions(build_ranked_actions(issues))
    return {
        "profile_slug": profile_slug,
        "profile_name": profile_name,
        "generated_at": generated_at,
        "actions": [
            {
                "rank": index,
                "issue_slug": action.issue_slug,
                "issue_title": action.issue_title,
                "priority_bucket": action.priority_bucket,
                "priority_label": PRIORITY_LABELS[action.priority_bucket],
                "do_next": action.do_next,
                "why": action.why,
                "specialist_type": action.specialist_type,
                "what_to_ask_for": action.what_to_ask_for,
                "what_result_to_return_with": action.what_result_to_return_with,
                "expected_payoff": action.expected_payoff,
                "owner": "user",
                "related_issues": action.related_issues,
                "source_citations": action.source_citations,
            }
            for index, action in enumerate(ranked, start=1)
        ],
    }
