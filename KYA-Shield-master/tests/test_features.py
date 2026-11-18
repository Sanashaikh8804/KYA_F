from __future__ import annotations

from kya.detector import AgentDetector
from kya.features import extract_features


def _event(ts_ms: int, event_type: str, **fields: object) -> dict:
    return {
        "session_id": "feature-test",
        "ts_ms": ts_ms,
        "event_type": event_type,
        "device": {"user_agent": "test", "webdriver": False, "headless_hint": False},
        "client": {"client_type": "browser"},
        **fields,
    }


def test_features_capture_human_pointer_and_keystrokes() -> None:
    events = [
        _event(0, "page_view", page="login"),
        _event(200, "keystroke", key_interval_ms=200),
        _event(500, "click", x=1, y=2),
    ]
    features = extract_features(events)
    assert features["keystroke_count"] == 1
    assert features["pointer_presence"] == 1
    assert features["webdriver_flag"] == 0


def test_detector_identifies_automated_session() -> None:
    events = [
        _event(0, "api_call"),
        _event(100, "api_call"),
        _event(200, "transaction", amount=10, payee="X", new_payee=False, merchant_category="grocery"),
    ]
    events[0]["device"]["webdriver"] = True
    assert AgentDetector().predict(events) == "scripted_bot"
