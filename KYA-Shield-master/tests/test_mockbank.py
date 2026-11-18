from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator

from mockbank.app import app

ROOT = Path(__file__).resolve().parents[1]
EVENT_SCHEMA = json.loads((ROOT / "schemas" / "event_schema.json").read_text())
validator = Draft202012Validator(EVENT_SCHEMA)
client = TestClient(app)


def test_seeded_principal_can_complete_merchant_payment() -> None:
    session = "test-human-session"
    headers = {"X-Session-ID": session}
    assert client.post("/login", headers=headers, json={"principal_id": "cust-001"}).status_code == 200
    response = client.post(
        "/merchant-payment",
        headers=headers,
        json={
            "principal_id": "cust-001",
            "amount": 100.0,
            "payee": "FRESHMART",
            "merchant_category": "grocery",
        },
    )
    assert response.status_code == 200
    events = client.get(f"/sessions/{session}/events").json()
    assert len(events) == 3
    for event in events:
        errors = list(validator.iter_errors([event]))
        assert not errors, errors


def test_external_content_is_marked_external() -> None:
    session = "test-external-session"
    response = client.get("/external-content", headers={"X-Session-ID": session})
    assert response.status_code == 200
    events = client.get(f"/sessions/{session}/events").json()
    assert events[-1]["event_type"] == "page_view"
    assert events[-1]["content_origin"] == "external"


def test_live_session_decision_returns_events_and_score() -> None:
    session = "test-live-decision"
    headers = {"X-Session-ID": session}
    assert client.post("/login", headers=headers, json={"principal_id": "cust-001"}).status_code == 200
    response = client.get(f"/sessions/{session}/decision")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["events"]) == 1
    assert payload["decision"]["session_id"] == session


def test_ollama_user_agent_is_recorded_as_tool_calling_agent() -> None:
    session = "test-ollama-metadata"
    response = client.post(
        "/login",
        headers={
            "X-Session-ID": session,
            "User-Agent": "KYA-Ollama-Agent/qwen2.5:7b",
        },
        json={"principal_id": "cust-001"},
    )
    assert response.status_code == 200
    event = client.get(f"/sessions/{session}/events").json()[-1]
    assert event["device"]["webdriver"] is True
    assert event["device"]["headless_hint"] is True
    assert event["client"]["client_type"] == "agent"
    assert event["client"]["framework_hint"] == "toolcall_ollama"


def test_mandate_is_recorded_but_not_enforced_by_bank() -> None:
    session = "test-mandate-session"
    mandate = {
        "mandate_id": "m-1",
        "principal_id": "cust-001",
        "agent_id": "agent-1",
        "signature": "demo-signature",
    }
    response = client.post(
        "/merchant-payment",
        headers={"X-Session-ID": session},
        json={
            "principal_id": "cust-001",
            "amount": 50.0,
            "payee": "UNLISTED-DEMO-PAYEE",
            "merchant_category": "grocery",
            "mandate": mandate,
        },
    )
    assert response.status_code == 200
    event = client.get(f"/sessions/{session}/events").json()[-1]
    assert event["mandate"] == mandate
    assert event["payee"] == "UNLISTED-DEMO-PAYEE"
