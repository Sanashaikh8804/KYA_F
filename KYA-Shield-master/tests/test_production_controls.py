from __future__ import annotations

import json
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from kya.security import ApiKeyGuard, AuditLogger, TrustedKeyRegistry, mandate_key_id
from kya.shadow import apply_shadow_mode


def test_registry_resolves_and_revokes_keys() -> None:
    key = Ed25519PrivateKey.generate()
    registry = TrustedKeyRegistry()
    registry.register("key-1", key.public_key())
    assert registry.resolve("key-1") is not None
    registry.revoke("key-1")
    assert registry.resolve("key-1") is None
    assert registry.is_revoked("key-1")


def test_api_key_guard_and_shadow_mode(monkeypatch) -> None:
    assert ApiKeyGuard("secret").check("secret")
    assert not ApiKeyGuard("secret").check("wrong")
    monkeypatch.setenv("KYA_SHADOW_MODE", "true")
    decision = apply_shadow_mode({"action": "block", "agent_trust_score": 5})
    assert decision["action"] == "allow"
    assert decision["recommended_action"] == "block"
    assert decision["shadow_mode"] is True


def test_audit_logger_writes_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "audit.jsonl"
    AuditLogger(path).record("score", {"session_id": "s-1", "action": "allow"})
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["event_type"] == "score"
    assert record["payload"]["session_id"] == "s-1"


def test_mandate_key_id_defaults_to_principal() -> None:
    assert mandate_key_id({"principal_id": "cust-001"}) == "principal:cust-001"
