"""Issue and outcome-update validation plus merge helpers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from health_agent.constants import (
    CONFIDENCE_FRAMES,
    EVENT_TYPES,
    ISSUE_STATUSES,
    PRIORITY_CONTEXT_FIELDS,
    REQUIRED_ISSUE_FIELDS,
    REQUIRED_OUTCOME_UPDATE_FIELDS,
)
from health_agent.jsonio import load_json, write_json


class ValidationError(ValueError):
    """Raised when a state artifact does not match the expected structure."""


@dataclass(slots=True)
class IssueFile:
    slug: str
    path: Path
    payload: dict[str, Any]


def _expect_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Field '{field}' must be a non-empty string.")
    return value.strip()


def _expect_enum(payload: dict[str, Any], field: str, allowed: set[str]) -> str:
    value = _expect_string(payload, field)
    if value not in allowed:
        raise ValidationError(
            f"Field '{field}' must be one of {sorted(allowed)}, got '{value}'."
        )
    return value


def _expect_string_list(payload: dict[str, Any], field: str) -> list[str]:
    value = payload.get(field)
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValidationError(f"Field '{field}' must be a list of non-empty strings.")
    return [item.strip() for item in value]


def _normalize_priority_context(payload: dict[str, Any]) -> dict[str, bool]:
    raw_context = payload.get("priority_context", {}) or {}
    if not isinstance(raw_context, dict):
        raise ValidationError("Field 'priority_context' must be an object when present.")

    normalized: dict[str, bool] = {}
    for field in PRIORITY_CONTEXT_FIELDS:
        value = raw_context.get(field, False)
        if not isinstance(value, bool):
            raise ValidationError(
                f"priority_context.{field} must be a boolean when present."
            )
        normalized[field] = value
    return normalized


def _normalize_recent_updates(payload: dict[str, Any]) -> list[str]:
    if "recent_updates" not in payload:
        return []
    return _expect_string_list(payload, "recent_updates")


def validate_issue_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("Issue payload must be a JSON object.")
    missing = [field for field in REQUIRED_ISSUE_FIELDS if field not in payload]
    if missing:
        raise ValidationError(f"Issue payload missing required fields: {missing}")

    normalized = deepcopy(payload)
    normalized["profile_slug"] = _expect_string(payload, "profile_slug")
    normalized["title"] = _expect_string(payload, "title")
    normalized["status"] = _expect_enum(payload, "status", ISSUE_STATUSES)
    normalized["working_conclusion"] = _expect_string(payload, "working_conclusion")
    normalized["confidence_frame"] = _expect_enum(
        payload,
        "confidence_frame",
        CONFIDENCE_FRAMES,
    )
    normalized["supporting_evidence"] = _expect_string_list(payload, "supporting_evidence")
    normalized["contradicting_evidence"] = _expect_string_list(
        payload, "contradicting_evidence"
    )
    normalized["next_best_action"] = _expect_string(payload, "next_best_action")
    normalized["why_this_action_now"] = _expect_string(payload, "why_this_action_now")
    normalized["specialist_type"] = _expect_string(payload, "specialist_type")
    normalized["tests_or_discussions_to_request"] = _expect_string_list(
        payload,
        "tests_or_discussions_to_request",
    )
    normalized["result_that_would_change_plan"] = _expect_string(
        payload,
        "result_that_would_change_plan",
    )
    normalized["last_reviewed_at"] = _expect_string(payload, "last_reviewed_at")
    normalized["linked_sources"] = _expect_string_list(payload, "linked_sources")
    normalized["priority_context"] = _normalize_priority_context(payload)
    normalized["recent_updates"] = _normalize_recent_updates(payload)
    return normalized


def validate_outcome_update(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValidationError("Outcome update payload must be a JSON object.")
    missing = [field for field in REQUIRED_OUTCOME_UPDATE_FIELDS if field not in payload]
    if missing:
        raise ValidationError(f"Outcome update missing required fields: {missing}")

    normalized = deepcopy(payload)
    normalized["issue_slug"] = _expect_string(payload, "issue_slug")
    normalized["event_type"] = _expect_enum(payload, "event_type", EVENT_TYPES)
    normalized["summary"] = _expect_string(payload, "summary")
    normalized["date"] = _expect_string(payload, "date")
    normalized["attachments_or_source_refs"] = _expect_string_list(
        payload,
        "attachments_or_source_refs",
    )
    return normalized


def _merge_unique_strings(original: list[str], revised: list[str]) -> list[str]:
    merged: list[str] = []
    for value in original + revised:
        if value not in merged:
            merged.append(value)
    return merged


def merge_issue_payloads(
    existing: dict[str, Any],
    revised: dict[str, Any],
    *,
    update_reference: str | None = None,
) -> dict[str, Any]:
    merged = deepcopy(existing)
    merged.update(revised)

    list_fields = (
        "supporting_evidence",
        "contradicting_evidence",
        "tests_or_discussions_to_request",
        "linked_sources",
        "recent_updates",
    )
    for field in list_fields:
        merged[field] = _merge_unique_strings(
            existing.get(field, []),
            revised.get(field, []),
        )

    priority_context = deepcopy(existing.get("priority_context", {}))
    priority_context.update(revised.get("priority_context", {}))
    merged["priority_context"] = priority_context
    if update_reference:
        merged["recent_updates"] = _merge_unique_strings(
            merged.get("recent_updates", []),
            [update_reference],
        )
    return validate_issue_payload(merged)


def load_issue_file(path: Path) -> IssueFile:
    payload = validate_issue_payload(load_json(path))
    return IssueFile(slug=path.stem, path=path, payload=payload)


def load_issue_collection(path: Path) -> list[IssueFile]:
    if path.is_dir():
        issue_paths = sorted(path.glob("*.json"))
    else:
        issue_paths = [path]
    return [load_issue_file(issue_path) for issue_path in issue_paths]


def save_issue(path: Path, payload: dict[str, Any]) -> None:
    write_json(path, validate_issue_payload(payload))
