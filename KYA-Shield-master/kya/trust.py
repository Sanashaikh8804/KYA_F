from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .detector import AgentDetector
from .drift import drift_risk, extract_drift_features
from .mandate import Violation

HARD_CAP_CODES = {"R100", "R101", "R102"}
OTHER_CAP_CODES = {"R103", "R104", "R105", "R106", "R107", "R108", "R109"}


@dataclass(frozen=True)
class TrustResult:
    agent_class: str
    agent_class_probs: dict[str, float]
    agent_trust_score: int
    p_fraud: float
    violations: list[Violation]
    drift_features: dict[str, float]


def calculate_trust(
    events: list[dict[str, Any]],
    violations: list[Violation],
    mandate: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    payee_counts: dict[str, int] | None = None,
) -> TrustResult:
    detector = AgentDetector()
    probabilities = detector.predict_proba(events)
    agent_class = max(probabilities, key=probabilities.get)
    features = extract_drift_features(events, mandate, history, payee_counts)
    behaviour_risk = 1.0 - probabilities.get("human", 0.0)
    drift_score = drift_risk(features)
    if not violations and mandate and not features["new_payee_after_external_content"]:
        # A valid customer mandate is stronger provenance than generic automation signals.
        fraud_probability = min(0.005, 0.25 * drift_score)
    elif not violations and agent_class == "human":
        fraud_probability = min(0.005, 0.15 * drift_score)
    else:
        fraud_probability = min(1.0, 0.55 * drift_score + 0.35 * behaviour_risk)
    if violations:
        fraud_probability = max(fraud_probability, 0.80)
    score = round(100 * (1.0 - fraud_probability))
    codes = {violation.code for violation in violations}
    if codes & HARD_CAP_CODES:
        score = min(score, 25)
    elif codes & OTHER_CAP_CODES:
        score = min(score, 45)
    return TrustResult(
        agent_class=agent_class,
        agent_class_probs=probabilities,
        agent_trust_score=max(0, min(100, score)),
        p_fraud=fraud_probability,
        violations=violations,
        drift_features=features,
    )
