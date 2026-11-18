from __future__ import annotations

import json
from pathlib import Path

import pytest

from generator.humans.collector import HumanSessionCollector, pseudonymous_id


def _events(session_id: str) -> list[dict]:
    return [{
        "session_id": session_id,
        "ts_ms": 1,
        "event_type": "page_view",
        "device": {"user_agent": "consented-browser", "webdriver": False},
        "client": {"client_type": "browser"},
        "page": "login",
        "dwell_ms": 1000,
    }]


def test_record_requires_consent_and_separates_human_data(tmp_path: Path) -> None:
    collector = HumanSessionCollector(tmp_path, salt="test-salt")
    with pytest.raises(ValueError, match="consent"):
        collector.record(
            volunteer_reference="volunteer-1",
            session_id="human-1",
            events=_events("human-1"),
            consent_confirmed=False,
        )
    label = collector.record(
        volunteer_reference="volunteer-1",
        session_id="human-1",
        events=_events("human-1"),
        consent_confirmed=True,
    )
    assert label["provenance"] == "consented_mockbank_human_v1"
    assert label["split"] == "collection"
    assert label["volunteer_id"] == pseudonymous_id("volunteer-1", salt="test-salt")
    assert json.loads((tmp_path / "sessions.jsonl").read_text())["volunteer_id"] == label["volunteer_id"]


def test_sensitive_fields_are_rejected(tmp_path: Path) -> None:
    events = _events("human-2")
    events[0]["password"] = "never-store"
    with pytest.raises(ValueError, match="sensitive"):
        HumanSessionCollector(tmp_path, salt="test-salt").record(
            volunteer_reference="volunteer-2",
            session_id="human-2",
            events=events,
            consent_confirmed=True,
        )


def test_delete_volunteer_removes_session_and_label(tmp_path: Path) -> None:
    collector = HumanSessionCollector(tmp_path, salt="test-salt")
    label = collector.record(
        volunteer_reference="volunteer-3",
        session_id="human-3",
        events=_events("human-3"),
        consent_confirmed=True,
    )
    assert collector.delete_volunteer(label["volunteer_id"]) == 1
    assert (tmp_path / "sessions.jsonl").read_text(encoding="utf-8") == ""
    assert len((tmp_path / "labels.csv").read_text(encoding="utf-8").splitlines()) == 1
