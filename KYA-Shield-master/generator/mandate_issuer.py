from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey


def canonical(fields: dict[str, Any]) -> bytes:
    return json.dumps(
        fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def demo_private_key() -> Ed25519PrivateKey:
    """Fixed local-only demo key; never use this key for production mandates."""
    return Ed25519PrivateKey.from_private_bytes(bytes(range(1, 33)))


def issue_mandate(
    *,
    principal_id: str,
    agent_id: str,
    task_description: str = "Weekly groceries",
    categories: list[str] | None = None,
    payees: list[str] | None = None,
    max_amount_per_txn: float = 3000.0,
    max_total_amount: float = 3000.0,
    max_txns_per_day: int = 3,
    now: datetime | None = None,
    private_key: Ed25519PrivateKey | None = None,
    key_id: str | None = None,
) -> tuple[dict[str, Any], Ed25519PrivateKey]:
    issued_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    key = private_key or Ed25519PrivateKey.generate()
    fields: dict[str, Any] = {
        "mandate_id": f"m-{uuid.uuid4()}",
        "principal_id": principal_id,
        "agent_id": agent_id,
        "agent_provenance": {
            "framework": "kya-shield-generator",
            "registered_at": issued_at.isoformat(),
        },
        "task_description": task_description,
        "allowed_merchant_categories": categories or ["grocery"],
        "allowed_payees": payees or ["FRESHMART", "DAILYBASKET"],
        "max_amount_per_txn": max_amount_per_txn,
        "max_total_amount": max_total_amount,
        "max_txns_per_day": max_txns_per_day,
        "issued_at": issued_at.isoformat(),
        "expires_at": (issued_at + timedelta(days=7)).isoformat(),
        "nonce": uuid.uuid4().hex,
    }
    if key_id:
        fields["key_id"] = key_id
    signature = key.sign(canonical(fields))
    return {**fields, "signature": base64.b64encode(signature).decode("ascii")}, key


def verify_mandate(mandate: dict[str, Any], public_key: Any) -> bool:
    signature = mandate.get("signature")
    if not isinstance(signature, str):
        return False
    body = {key: value for key, value in mandate.items() if key != "signature"}
    try:
        public_key.verify(base64.b64decode(signature, validate=True), canonical(body))
    except Exception:
        return False
    return True


def private_key_pem(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
