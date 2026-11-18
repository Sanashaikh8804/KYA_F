from __future__ import annotations

import time
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .mandate import MandateVerifier, Violation
from .policy import choose_action
from .reasons import build_reason_codes
from .trust import calculate_trust
from .security import TrustedKeyRegistry, mandate_key_id


def _validate_events(events: list[dict[str, Any]]) -> None:
    if not events:
        raise ValueError("events must contain at least one event")
    session_ids = {event.get("session_id") for event in events}
    if len(session_ids) != 1 or None in session_ids:
        raise ValueError("events must belong to exactly one session")
    if any("ts_ms" not in event or "event_type" not in event for event in events):
        raise ValueError("each event must contain ts_ms and event_type")


def score_session(
    events: list[dict[str, Any]],
    *,
    public_key: Ed25519PublicKey | None = None,
    used_nonces: set[str] | None = None,
    history: list[dict[str, Any]] | None = None,
    payee_counts: dict[str, int] | None = None,
    key_registry: TrustedKeyRegistry | None = None,
) -> dict[str, Any]:
    started = time.perf_counter_ns()
    _validate_events(events)
    ordered = sorted(events, key=lambda event: event["ts_ms"])
    transaction = next(
        (event for event in reversed(ordered) if event.get("event_type") == "transaction"),
        {},
    )
    mandate = transaction.get("mandate")
    if mandate and key_registry is not None:
        public_key = key_registry.resolve(mandate_key_id(mandate))
    if mandate and public_key is None:
        violations = [Violation("R100", "A mandate was supplied but no trusted verification key was configured.")]
    else:
        verifier = MandateVerifier(public_key, used_nonces) if public_key else None
        violations = verifier.verify(mandate, ordered) if verifier else []
    trust = calculate_trust(ordered, violations, mandate, history, payee_counts)
    amount = float(transaction.get("amount", 0.0))
    action, costs = choose_action(trust.p_fraud, amount)
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    return {
        "session_id": ordered[0]["session_id"],
        "agent_class": trust.agent_class,
        "agent_class_probs": trust.agent_class_probs,
        "agent_trust_score": trust.agent_trust_score,
        "p_fraud": round(trust.p_fraud, 6),
        "action": action,
        "expected_cost_by_action": costs,
        "reason_codes": build_reason_codes(trust.violations, trust.drift_features),
        "latency_ms": round(elapsed_ms, 4),
    }
