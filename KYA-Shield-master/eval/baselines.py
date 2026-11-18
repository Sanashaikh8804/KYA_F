from __future__ import annotations

from typing import Any

from kya.drift import extract_drift_features
from kya.policy import rule_based_action


def rule_action_for_session(events: list[dict[str, Any]], label: dict[str, str]) -> str:
    mandate = next(
        (
            event.get("mandate")
            for event in reversed(events)
            if event.get("event_type") == "transaction" and event.get("mandate")
        ),
        None,
    )
    drift = extract_drift_features(events, mandate)
    return rule_based_action(
        agent_class=label["agent_class"],
        has_mandate=label["has_mandate"] == "true",
        new_payee_after_external_content=bool(drift["new_payee_after_external_content"]),
    )


def allow_all_action(_: list[dict[str, Any]], __: dict[str, str]) -> str:
    return "allow"
