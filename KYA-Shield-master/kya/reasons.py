from __future__ import annotations

from typing import Any

from .mandate import Violation

_DRIFT_REASONS = {
    "new_payee_after_external_content": (
        "R201",
        "A new payee was used shortly after external content was loaded.",
        0.90,
    ),
    "category_switch_vs_task": (
        "R202",
        "The transaction category differs from the delegated task.",
        0.65,
    ),
    "amount_ratio_to_cap": (
        "R203",
        "The transaction is close to the mandate amount cap.",
        0.50,
    ),
    "amount_zscore_vs_history": (
        "R204",
        "The amount is unusual compared with the customer's history.",
        0.55,
    ),
    "api_pattern_shift": (
        "R205",
        "The API interaction pattern changed after external content.",
        0.40,
    ),
    "payee_reuse_across_sessions": (
        "R206",
        "This payee has appeared across multiple sessions.",
        0.45,
    ),
    "txn_velocity": (
        "R207",
        "Transactions occurred at an unusually high velocity.",
        0.35,
    ),
}


def build_reason_codes(
    violations: list[Violation],
    drift_features: dict[str, float],
) -> list[dict[str, Any]]:
    reasons: list[dict[str, Any]] = [
        {"code": violation.code, "text": violation.message, "weight": 1.0}
        for violation in violations
    ]
    for feature, (code, text, weight) in _DRIFT_REASONS.items():
        value = drift_features.get(feature, 0.0)
        threshold = 0.95 if feature == "amount_ratio_to_cap" else 0.50
        if value > threshold:
            reasons.append({"code": code, "text": text, "weight": round(min(1.0, weight * max(1.0, value)), 3)})
    if not reasons:
        reasons.append({
            "code": "R000",
            "text": "Behaviour is consistent with the principal's mandate and history.",
            "weight": 0.0,
        })
    reasons.sort(key=lambda reason: (-float(reason["weight"]), reason["code"]))
    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for reason in reasons:
        if reason["code"] not in seen:
            unique.append(reason)
            seen.add(reason["code"])
    return unique[:5]
