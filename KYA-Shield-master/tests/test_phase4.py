from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from generator.mandate_issuer import issue_mandate
from kya.drift import extract_drift_features
from kya.mandate import MandateVerifier
from kya.trust import calculate_trust


NOW = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
TS = int(NOW.timestamp() * 1000)


def make_case(**mandate_options: object) -> tuple[dict, list[dict], Ed25519PrivateKey]:
    key = Ed25519PrivateKey.generate()
    mandate, _ = issue_mandate(
        principal_id="cust-001",
        agent_id="agent-1",
        now=NOW,
        private_key=key,
        **mandate_options,
    )
    base = {
        "session_id": "phase4",
        "device": {"user_agent": "agent", "webdriver": True},
        "client": {"client_type": "browser", "agent_id": "agent-1", "framework_hint": "browseragent_A"},
    }
    events = [
        {**base, "ts_ms": TS, "event_type": "page_view", "page": "product_page", "content_origin": "external"},
        {**base, "ts_ms": TS + 2_000, "event_type": "transaction", "amount": 100.0, "payee": "FRESHMART", "new_payee": False, "merchant_category": "grocery", "mandate": mandate},
    ]
    return mandate, events, key


def codes(mandate: dict, events: list[dict], key: Ed25519PrivateKey) -> set[str]:
    return {item.code for item in MandateVerifier(key.public_key()).verify(mandate, events)}


def test_each_scope_violation() -> None:
    mandate, events, key = make_case(max_amount_per_txn=50.0)
    assert "R102" in codes(mandate, events, key)
    mandate, events, key = make_case(max_total_amount=50.0)
    assert "R107" in codes(mandate, events, key)
    mandate, events, key = make_case(categories=["travel"])
    assert "R106" in codes(mandate, events, key)
    mandate, events, key = make_case(payees=["OTHER"])
    assert "R101" in codes(mandate, events, key)
    mandate, events, key = make_case(max_txns_per_day=1)
    events.insert(1, {**events[1], "ts_ms": TS + 1_000, "payee": "DAILYBASKET"})
    assert "R108" in codes(mandate, events, key)


def test_signature_expiry_replay_and_agent_binding() -> None:
    mandate, events, key = make_case()
    mandate["signature"] = "invalid"
    assert "R100" in codes(mandate, events, key)
    mandate, events, key = make_case()
    expired_key = Ed25519PrivateKey.generate()
    expired_mandate, _ = issue_mandate(
        principal_id="cust-001",
        agent_id="agent-1",
        now=NOW - timedelta(days=10),
        private_key=expired_key,
    )
    assert "R103" in codes(expired_mandate, events, expired_key)
    mandate, events, key = make_case()
    verifier = MandateVerifier(key.public_key())
    assert not {item.code for item in verifier.verify(mandate, events)} - set()
    assert "R104" in {item.code for item in verifier.verify(mandate, events)}
    mandate, events, key = make_case()
    events[1]["client"]["agent_id"] = "other-agent"
    assert "R105" in codes(mandate, events, key)


def test_drift_and_hard_trust_cap() -> None:
    mandate, events, key = make_case(payees=["FRESHMART"])
    events.insert(1, {**events[0], "ts_ms": TS + 500, "event_type": "api_call", "api_endpoint": "/payees/add"})
    events[-1]["payee"] = "ACME-9921"
    events[-1]["new_payee"] = True
    violations = MandateVerifier(key.public_key()).verify(mandate, events)
    drift = extract_drift_features(events, mandate)
    result = calculate_trust(events, violations, mandate)
    assert drift["new_payee_after_external_content"] == 1
    assert result.agent_trust_score <= 25
