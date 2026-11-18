from __future__ import annotations

import argparse
import csv
import hashlib
import json
import secrets
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SENSITIVE_KEYS = {
    "password",
    "password_value",
    "token",
    "secret",
    "credential",
    "email",
    "phone",
    "name",
}
PROVENANCE = "consented_mockbank_human_v1"


def pseudonymous_id(volunteer_reference: str, *, salt: str) -> str:
    if not volunteer_reference.strip():
        raise ValueError("volunteer reference must not be empty")
    digest = hashlib.sha256(f"{salt}:{volunteer_reference}".encode("utf-8")).hexdigest()
    return f"human-{digest[:16]}"


def _assert_safe_event(value: Any, path: str = "event") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in SENSITIVE_KEYS:
                raise ValueError(f"sensitive field is not allowed: {path}.{key}")
            _assert_safe_event(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_safe_event(child, f"{path}[{index}]")
    elif isinstance(value, str) and len(value) > 500:
        raise ValueError(f"unbounded text is not allowed: {path}")


def validate_events(events: list[dict[str, Any]], session_id: str) -> None:
    if not events:
        raise ValueError("the session has no events")
    if any(event.get("session_id") != session_id for event in events):
        raise ValueError("events belong to a different session")
    if any(events[index]["ts_ms"] > events[index + 1]["ts_ms"] for index in range(len(events) - 1)):
        raise ValueError("events must be ordered by timestamp")
    _assert_safe_event(events)


class HumanSessionCollector:
    def __init__(self, output_dir: Path, *, salt: str | None = None) -> None:
        self.output_dir = output_dir
        self.salt_path = output_dir / ".pseudonym_salt"
        self.salt = salt or self._load_or_create_salt()
        self.sessions_path = output_dir / "sessions.jsonl"
        self.labels_path = output_dir / "labels.csv"

    def _load_or_create_salt(self) -> str:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if self.salt_path.exists():
            return self.salt_path.read_text(encoding="utf-8").strip()
        salt = secrets.token_hex(32)
        self.salt_path.write_text(salt, encoding="utf-8")
        return salt

    def record(
        self,
        *,
        volunteer_reference: str,
        session_id: str,
        events: list[dict[str, Any]],
        consent_confirmed: bool,
    ) -> dict[str, Any]:
        if not consent_confirmed:
            raise ValueError("written consent must be confirmed before collection")
        validate_events(events, session_id)
        volunteer_id = pseudonymous_id(volunteer_reference, salt=self.salt)
        label = {
            "session_id": session_id,
            "agent_class": "human",
            "intent": "unknown",
            "typology": "none",
            "framework": "human",
            "hard_mode": "false",
            "has_mandate": "false",
            "principal_id": "mockbank-consented",
            "augmented": "false",
            "split": "collection",
            "volunteer_id": volunteer_id,
            "provenance": PROVENANCE,
            "consented_at": datetime.now(timezone.utc).isoformat(),
        }
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self.sessions_path.open("a", encoding="utf-8") as output:
            output.write(json.dumps({
                "session_id": session_id,
                "volunteer_id": volunteer_id,
                "provenance": PROVENANCE,
                "events": events,
            }, sort_keys=True) + "\n")
        existing = self._read_labels()
        existing.append(label)
        self._write_labels(existing)
        return label

    def delete_volunteer(self, volunteer_id: str) -> int:
        sessions = self._read_sessions()
        kept_sessions = [row for row in sessions if row.get("volunteer_id") != volunteer_id]
        labels = [row for row in self._read_labels() if row.get("volunteer_id") != volunteer_id]
        removed = len(sessions) - len(kept_sessions)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with self.sessions_path.open("w", encoding="utf-8") as output:
            for row in kept_sessions:
                output.write(json.dumps(row, sort_keys=True) + "\n")
        self._write_labels(labels)
        return removed

    def _read_sessions(self) -> list[dict[str, Any]]:
        if not self.sessions_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.sessions_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _read_labels(self) -> list[dict[str, Any]]:
        if not self.labels_path.exists():
            return []
        with self.labels_path.open(newline="", encoding="utf-8") as source:
            return list(csv.DictReader(source))

    def _write_labels(self, labels: list[dict[str, Any]]) -> None:
        fields = [
            "session_id", "agent_class", "intent", "typology", "framework",
            "hard_mode", "has_mandate", "principal_id", "augmented", "split",
            "volunteer_id", "provenance", "consented_at",
        ]
        with self.labels_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=fields)
            writer.writeheader()
            writer.writerows(labels)


def fetch_events(bank_url: str, session_id: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"{bank_url.rstrip('/')}/sessions/{session_id}/events",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"could not fetch session events: {exc}") from exc
    if not isinstance(payload, list):
        raise RuntimeError("bank returned an invalid event list")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Store a consented mock-bank human session.")
    parser.add_argument("--bank-url", default="http://127.0.0.1:8000")
    parser.add_argument("--session-id")
    parser.add_argument("--volunteer-reference")
    parser.add_argument("--output", type=Path, default=Path("data/human_sessions"))
    parser.add_argument("--confirm-consent", action="store_true")
    parser.add_argument("--delete-volunteer")
    args = parser.parse_args()
    collector = HumanSessionCollector(args.output)
    if args.delete_volunteer:
        print(collector.delete_volunteer(args.delete_volunteer))
        return
    if not args.session_id or not args.volunteer_reference:
        parser.error("--session-id and --volunteer-reference are required for collection")
    label = collector.record(
        volunteer_reference=args.volunteer_reference,
        session_id=args.session_id,
        events=fetch_events(args.bank_url, args.session_id),
        consent_confirmed=args.confirm_consent,
    )
    print(json.dumps(label, indent=2))


if __name__ == "__main__":
    main()
