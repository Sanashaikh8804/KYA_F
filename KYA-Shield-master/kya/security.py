from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class TrustedKeyRegistry:
    """In-memory registry for demo use; production storage should be KMS/HSM-backed."""

    def __init__(self) -> None:
        self._keys: dict[str, Ed25519PublicKey] = {}
        self._revoked: set[str] = set()

    def register(self, key_id: str, public_key: Ed25519PublicKey) -> None:
        if not key_id:
            raise ValueError("key_id is required")
        self._keys[key_id] = public_key

    def register_pem(self, key_id: str, pem: bytes) -> None:
        key = serialization.load_pem_public_key(pem)
        if not isinstance(key, Ed25519PublicKey):
            raise TypeError("only Ed25519 public keys are supported")
        self.register(key_id, key)

    def revoke(self, key_id: str) -> None:
        if key_id not in self._keys:
            raise KeyError(key_id)
        self._revoked.add(key_id)

    def resolve(self, key_id: str | None) -> Ed25519PublicKey | None:
        if not key_id or key_id in self._revoked:
            return None
        return self._keys.get(key_id)

    def is_revoked(self, key_id: str | None) -> bool:
        return bool(key_id and key_id in self._revoked)


def mandate_key_id(mandate: dict[str, Any] | None) -> str | None:
    if not mandate:
        return None
    explicit = mandate.get("key_id")
    if isinstance(explicit, str):
        return explicit
    principal = mandate.get("principal_id")
    return f"principal:{principal}" if isinstance(principal, str) else None


class ApiKeyGuard:
    def __init__(self, expected_key: str | None = None) -> None:
        self.expected_key = expected_key or os.getenv("KYA_API_KEY")

    def check(self, supplied_key: str | None) -> bool:
        if not self.expected_key:
            return True
        return bool(supplied_key) and secrets.compare_digest(supplied_key, self.expected_key)


class AuditLogger:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path or os.getenv("KYA_AUDIT_LOG", "audit/events.jsonl"))
        self._lock = Lock()

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        record = {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "payload": payload,
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(record, sort_keys=True) + "\n")


def request_id(session_id: str) -> str:
    return hashlib.sha256(f"{session_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()[:20]


def public_key_pem(public_key: Ed25519PublicKey) -> bytes:
    return public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
