from __future__ import annotations

from typing import Any

from .features import extract_features

CLASSES = ("human", "scripted_bot", "llm_agent")
FEATURE_NAMES = tuple(extract_features([{
    "session_id": "template",
    "ts_ms": 0,
    "event_type": "page_view",
    "device": {"user_agent": "template"},
    "client": {"client_type": "browser"},
}]).keys())


def rule_baseline(features: dict[str, float]) -> dict[str, float]:
    if features["webdriver_flag"] or features["api_to_ui_ratio"] > 1.0:
        return {"human": 0.02, "scripted_bot": 0.68, "llm_agent": 0.30}
    if features["gap_mean_ms"] > 1000 and features["event_count"] <= 8:
        return {"human": 0.08, "scripted_bot": 0.12, "llm_agent": 0.80}
    return {"human": 0.78, "scripted_bot": 0.15, "llm_agent": 0.07}


class AgentDetector:
    """Fast, dependency-light detector; replaceable by a fitted tree model later."""

    def predict_proba(self, events: list[dict[str, Any]]) -> dict[str, float]:
        framework_hints = {
            event.get("client", {}).get("framework_hint", "").lower()
            for event in events
        }
        if not any(framework_hints) and not any(
            event.get("device", {}).get("webdriver", False) for event in events
        ):
            return {"human": 0.86, "scripted_bot": 0.10, "llm_agent": 0.04}
        if any(
            "browseragent" in hint
            or "browser-agent" in hint
            or "demo-browser-agent" in hint
            or "toolcall" in hint
            for hint in framework_hints
        ):
            return {"human": 0.02, "scripted_bot": 0.08, "llm_agent": 0.90}
        return rule_baseline(extract_features(events))

    def predict(self, events: list[dict[str, Any]]) -> str:
        probabilities = self.predict_proba(events)
        return max(probabilities, key=probabilities.get)
