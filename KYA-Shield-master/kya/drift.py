from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


def extract_drift_features(
    events: list[dict[str, Any]],
    mandate: dict[str, Any] | None = None,
    history: list[dict[str, Any]] | None = None,
    payee_counts: dict[str, int] | None = None,
) -> dict[str, float]:
    ordered = sorted(events, key=lambda event: event["ts_ms"])
    external = [event for event in ordered if event.get("content_origin") == "external"]
    external_ts = external[-1]["ts_ms"] if external else None
    transactions = [event for event in ordered if event.get("event_type") == "transaction"]
    payee_adds = [
        event for event in ordered
        if event.get("event_type") == "api_call"
        and event.get("api_endpoint", "").rstrip("/") in {"/payees", "/payees/add"}
    ]
    new_payee_after_external = any(
        external_ts is not None and event["ts_ms"] >= external_ts
        and event["ts_ms"] - external_ts <= 60_000
        for event in payee_adds
    ) or any(
        external_ts is not None and transaction.get("new_payee")
        and transaction["ts_ms"] >= external_ts
        and transaction["ts_ms"] - external_ts <= 60_000
        for transaction in transactions
    )
    gaps = [
        later["ts_ms"] - earlier["ts_ms"]
        for earlier, later in zip(ordered, ordered[1:])
    ]
    first_txn = transactions[0] if transactions else {}
    amount = float(first_txn.get("amount", 0.0))
    cap = float((mandate or {}).get("max_amount_per_txn", 0.0))
    history_amounts = [float(item["amount"]) for item in (history or []) if "amount" in item]
    typical = mean(history_amounts) if history_amounts else amount
    history_std = pstdev(history_amounts) if len(history_amounts) > 1 else max(typical * 0.25, 1.0)
    task = (mandate or {}).get("task_description", "").lower()
    category = first_txn.get("merchant_category", "")
    category_words = {category.lower(), category.lower().rstrip("y") + "ies"}
    category_switch = bool(
        category
        and task
        and not any(word in task for word in (*category_words, "shopping", "payment"))
    )
    api_before = sum(event.get("event_type") == "api_call" for event in ordered if external_ts is None or event["ts_ms"] < external_ts)
    api_after = sum(event.get("event_type") == "api_call" for event in ordered if external_ts is not None and event["ts_ms"] >= external_ts)
    rhythm_change = 0.0
    if len(gaps) >= 4:
        midpoint = len(gaps) // 2
        before, after = gaps[:midpoint], gaps[midpoint:]
        rhythm_change = abs(mean(before) - mean(after)) / max(mean(before), 1.0)
    payee = first_txn.get("payee", "")
    return {
        "new_payee_after_external_content": float(new_payee_after_external),
        "secs_from_external_load_to_payee_add": (
            float((payee_adds[0]["ts_ms"] - external_ts) / 1000)
            if external_ts is not None and payee_adds and payee_adds[0]["ts_ms"] >= external_ts
            else 0.0
        ),
        "category_switch_vs_task": float(category_switch),
        "amount_ratio_to_cap": float(amount / cap) if cap else 0.0,
        "amount_zscore_vs_history": float((amount - typical) / history_std),
        "api_pattern_shift": float(abs(api_after - api_before) / max(1, api_before + api_after)),
        "rhythm_change": float(rhythm_change),
        "payee_reuse_across_sessions": float((payee_counts or {}).get(payee, 0) > 1),
        "n_new_payees_in_session": float(sum(transaction.get("new_payee", False) for transaction in transactions)),
        "txn_velocity": float(len(transactions) / max((ordered[-1]["ts_ms"] - ordered[0]["ts_ms"]) / 1000, 1.0)),
    }


def drift_risk(features: dict[str, float]) -> float:
    weights = {
        "new_payee_after_external_content": 0.35,
        "category_switch_vs_task": 0.15,
        "amount_ratio_to_cap": 0.10,
        "amount_zscore_vs_history": 0.10,
        "api_pattern_shift": 0.05,
        "rhythm_change": 0.05,
        "payee_reuse_across_sessions": 0.10,
        "n_new_payees_in_session": 0.05,
        "txn_velocity": 0.05,
    }
    score = sum(
        weight * min(1.0, abs(features.get(name, 0.0)) if name != "amount_ratio_to_cap" else features.get(name, 0.0))
        for name, weight in weights.items()
    )
    return max(0.0, min(1.0, score))
