from __future__ import annotations

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from generator.mandate_issuer import issue_mandate
from kya.policy import choose_action, expected_costs
from kya.scoring_api import score_session
from mockbank.app import app

ROOT = Path(__file__).parents[1]
DECISION_SCHEMA = json.loads((ROOT / "schemas" / "decision_schema.json").read_text())
decision_validator = Draft202012Validator(DECISION_SCHEMA)


def events_with_transaction() -> tuple[list[dict], Ed25519PrivateKey]:
    key = Ed25519PrivateKey.generate()
    mandate, _ = issue_mandate(
        principal_id="cust-001",
        agent_id="agent-1",
        now=__import__("datetime").datetime.fromtimestamp(
            1_794_000_000, __import__("datetime").timezone.utc
        ),
        private_key=key,
    )
    base = {
        "session_id": "phase5-session",
        "device": {"user_agent": "agent", "webdriver": True},
        "client": {
            "client_type": "browser",
            "agent_id": "agent-1",
            "framework_hint": "browseragent_A",
        },
    }
    return [
        {**base, "ts_ms": 1_794_000_000_000, "event_type": "page_view", "page": "catalog"},
        {**base, "ts_ms": 1_794_000_001_000, "event_type": "transaction",
         "amount": 2450, "payee": "FRESHMART", "new_payee": False,
         "merchant_category": "grocery", "mandate": mandate},
    ], key


def test_policy_uses_cost_matrix() -> None:
    costs = expected_costs(0.0, 1000)
    assert costs["allow"] == 0
    assert choose_action(0.99, 2990)[0] == "block"


def test_score_output_matches_decision_schema_and_has_reason() -> None:
    events, key = events_with_transaction()
    decision = score_session(events, public_key=key.public_key())
    errors = list(decision_validator.iter_errors(decision))
    assert not errors, errors
    assert decision["reason_codes"]
    assert decision["agent_class"] == "llm_agent"


def test_score_rejects_missing_events() -> None:
    client = TestClient(app)
    response = client.post("/score", json=[])
    assert response.status_code == 422
