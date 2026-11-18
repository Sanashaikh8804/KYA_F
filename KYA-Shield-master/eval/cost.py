from __future__ import annotations

from typing import Any

from kya.policy import load_cost_matrix


def transaction_amount(events: list[dict[str, Any]]) -> float:
    transactions = [event for event in events if event.get("event_type") == "transaction"]
    return sum(float(event.get("amount", 0.0)) for event in transactions)


def realised_cost(action: str, label: dict[str, str], amount: float) -> float:
    matrix = load_cost_matrix()
    legitimate = label["intent"] == "legitimate"
    if legitimate:
        return float(matrix["legitimate_cost"][action])
    return float(matrix["fraud_loss_fraction_of_amount"][action]) * amount


def cost_per_1000(
    actions: list[str],
    labels: list[dict[str, str]],
    amounts: list[float],
) -> float:
    if not labels:
        return 0.0
    total = sum(
        realised_cost(action, label, amount)
        for action, label, amount in zip(actions, labels, amounts)
    )
    return round(1000 * total / len(labels), 2)
