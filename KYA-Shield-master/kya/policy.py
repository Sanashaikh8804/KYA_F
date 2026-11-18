from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

Action = Literal["allow", "step_up", "hold", "block"]
POLICY_ACTIONS: tuple[Action, ...] = ("allow", "step_up", "hold", "block")


def load_cost_matrix() -> dict:
    path = Path(__file__).parents[1] / "config" / "cost_matrix.json"
    return json.loads(path.read_text(encoding="utf-8"))


def expected_costs(
    p_fraud: float,
    amount: float,
    cost_matrix: dict | None = None,
) -> dict[Action, float]:
    if not 0 <= p_fraud <= 1:
        raise ValueError("p_fraud must be between 0 and 1")
    if amount < 0:
        raise ValueError("amount must not be negative")
    matrix = cost_matrix or load_cost_matrix()
    legitimate = matrix["legitimate_cost"]
    fraud_fraction = matrix["fraud_loss_fraction_of_amount"]
    return {
        action: round(
            (1 - p_fraud) * float(legitimate[action])
            + p_fraud * float(fraud_fraction[action]) * amount,
            2,
        )
        for action in POLICY_ACTIONS
    }


def choose_action(
    p_fraud: float,
    amount: float,
    cost_matrix: dict | None = None,
) -> tuple[Action, dict[Action, float]]:
    costs = expected_costs(p_fraud, amount, cost_matrix)
    action = min(POLICY_ACTIONS, key=lambda candidate: costs[candidate])
    return action, costs


def rule_based_action(
    *,
    agent_class: str,
    has_mandate: bool,
    new_payee_after_external_content: bool,
) -> Action:
    if agent_class in {"scripted_bot", "llm_agent"} and not has_mandate:
        return "block"
    if new_payee_after_external_content:
        return "hold"
    return "allow"
