from __future__ import annotations

from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from generator.build_dataset import make_session
from generator.mandate_issuer import issue_mandate, verify_mandate


def test_mandate_signature_detects_tampering() -> None:
    key = Ed25519PrivateKey.generate()
    mandate, _ = issue_mandate(
        principal_id="cust-001",
        agent_id="agent-1",
        now=datetime(2026, 11, 9, tzinfo=timezone.utc),
        private_key=key,
    )
    assert verify_mandate(mandate, key.public_key())
    mandate["max_amount_per_txn"] = 99999
    assert not verify_mandate(mandate, key.public_key())


def test_dataset_session_has_schema_fields() -> None:
    label, session = make_session(1000, __import__("random").Random(7))
    transaction = next(event for event in session["events"] if event["event_type"] == "transaction")
    assert label["typology"] == "T1"
    assert transaction["new_payee"] is True
    assert transaction["mandate"]["signature"]
