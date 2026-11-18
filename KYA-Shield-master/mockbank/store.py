from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Any


@dataclass
class Principal:
    principal_id: str
    username: str
    balance: float
    payees: set[str] = field(default_factory=set)
    history: list[dict[str, Any]] = field(default_factory=list)


class BankStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self.principals: dict[str, Principal] = {
            "cust-001": Principal("cust-001", "alice", 25000.0, {"FRESHMART", "DAILYBASKET"}),
            "cust-002": Principal("cust-002", "bob", 18000.0, {"ELECTROHUB"}),
            "cust-003": Principal("cust-003", "carol", 32000.0, {"UTILITYCO"}),
        }
        self.sessions: dict[str, list[dict[str, Any]]] = {}

    def add_event(self, session_id: str, event: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            events = self.sessions.setdefault(session_id, [])
            if events and event["ts_ms"] < events[-1]["ts_ms"]:
                raise ValueError("event timestamp must be ordered within a session")
            events.append(event)
        return event

    def events_for(self, session_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return list(self.sessions.get(session_id, []))

    def add_payee(self, principal_id: str, payee: str) -> bool:
        principal = self.principals[principal_id]
        with self._lock:
            is_new = payee not in principal.payees
            principal.payees.add(payee)
        return is_new

    def transact(
        self,
        principal_id: str,
        amount: float,
        payee: str,
        merchant_category: str,
    ) -> bool:
        with self._lock:
            principal = self.principals[principal_id]
            if amount > principal.balance:
                raise ValueError("insufficient balance")
            new_payee = payee not in principal.payees
            principal.balance -= amount
            principal.history.append(
                {"amount": amount, "payee": payee, "merchant_category": merchant_category}
            )
        return new_payee
