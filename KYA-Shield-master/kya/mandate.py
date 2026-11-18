from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from cryptography.exceptions import InvalidSignature

from generator.mandate_issuer import canonical

R100 = "R100"
R101 = "R101"
R102 = "R102"
R103 = "R103"
R104 = "R104"
R105 = "R105"
R106 = "R106"
R107 = "R107"
R108 = "R108"
R109 = "R109"


@dataclass(frozen=True)
class Violation:
    code: str
    message: str


def _when(ts_ms: int) -> datetime:
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class MandateVerifier:
    def __init__(self, public_key: Any, used_nonces: set[str] | None = None) -> None:
        self.public_key = public_key
        self.used_nonces = used_nonces if used_nonces is not None else set()

    def verify(
        self,
        mandate: dict[str, Any] | None,
        events: list[dict[str, Any]],
    ) -> list[Violation]:
        if not mandate:
            return [Violation(R109, "No mandate was attached to the agent session.")]
        violations = self._verify_signature(mandate)
        nonce = mandate.get("nonce")
        if nonce in self.used_nonces:
            violations.append(Violation(R104, "The mandate nonce has already been used."))
        if isinstance(nonce, str):
            self.used_nonces.add(nonce)

        agent_ids = {
            event.get("client", {}).get("agent_id")
            for event in events
            if event.get("client", {}).get("agent_id")
        }
        if agent_ids and mandate.get("agent_id") not in agent_ids:
            violations.append(Violation(R105, "The session agent is not bound to the mandate."))
        principal_id = next(
            (event.get("principal_id") for event in events if event.get("principal_id")),
            mandate.get("principal_id"),
        )
        if principal_id != mandate.get("principal_id"):
            violations.append(Violation(R105, "The mandate is bound to a different principal."))

        transactions = [
            event for event in sorted(events, key=lambda item: item["ts_ms"])
            if event.get("event_type") == "transaction"
        ]
        spent = 0.0
        for transaction in transactions:
            violations.extend(
                self._scope_violations(mandate, transaction, spent, transactions)
            )
            spent += float(transaction.get("amount", 0.0))
        return _unique(violations)

    def _verify_signature(self, mandate: dict[str, Any]) -> list[Violation]:
        signature = mandate.get("signature")
        if not isinstance(signature, str):
            return [Violation(R100, "The mandate signature is missing.")]
        body = {key: value for key, value in mandate.items() if key != "signature"}
        try:
            decoded = base64.b64decode(signature, validate=True)
            self.public_key.verify(decoded, canonical(body))
        except (InvalidSignature, ValueError, TypeError, binascii.Error, json.JSONDecodeError):
            return [Violation(R100, "The mandate signature is invalid.")]
        return []

    def _scope_violations(
        self,
        mandate: dict[str, Any],
        transaction: dict[str, Any],
        spent: float,
        transactions: list[dict[str, Any]],
    ) -> list[Violation]:
        now = _when(int(transaction["ts_ms"]))
        violations: list[Violation] = []
        try:
            if not (_parse_time(mandate["issued_at"]) <= now <= _parse_time(mandate["expires_at"])):
                violations.append(Violation(R103, "The transaction is outside the mandate validity window."))
        except (KeyError, TypeError, ValueError):
            violations.append(Violation(R103, "The mandate validity window is invalid."))
        amount = float(transaction.get("amount", 0.0))
        if amount > float(mandate.get("max_amount_per_txn", 0.0)):
            violations.append(Violation(R102, "The transaction exceeds the per-transaction amount cap."))
        if spent + amount > float(mandate.get("max_total_amount", 0.0)):
            violations.append(Violation(R107, "The mandate cumulative amount cap would be exceeded."))
        if transaction.get("merchant_category") not in mandate.get("allowed_merchant_categories", []):
            violations.append(Violation(R106, "The merchant category is outside the mandate scope."))
        allowed_payees = mandate.get("allowed_payees") or []
        if allowed_payees and transaction.get("payee") not in allowed_payees:
            violations.append(Violation(R101, f"Payee '{transaction.get('payee')}' is not allowed by the mandate."))
        day_start = int(transaction["ts_ms"]) - 86_400_000
        transactions_today = sum(
            int(item["ts_ms"]) >= day_start and int(item["ts_ms"]) <= int(transaction["ts_ms"])
            for item in transactions
        )
        if transactions_today > int(mandate.get("max_txns_per_day", 0)):
            violations.append(Violation(R108, "The mandate daily transaction frequency limit was exceeded."))
        return violations


def _unique(violations: list[Violation]) -> list[Violation]:
    result: list[Violation] = []
    seen: set[str] = set()
    for violation in violations:
        if violation.code not in seen:
            result.append(violation)
            seen.add(violation.code)
    return result
