from __future__ import annotations

import math
from collections import Counter
from statistics import mean, pstdev
from typing import Any


def extract_features(events: list[dict[str, Any]]) -> dict[str, float]:
    if not events:
        raise ValueError("events must contain at least one event")
    ordered = sorted(events, key=lambda event: event["ts_ms"])
    gaps = [
        max(0, later["ts_ms"] - earlier["ts_ms"])
        for earlier, later in zip(ordered, ordered[1:])
    ]
    gaps_mean = mean(gaps) if gaps else 0.0
    gap_std = pstdev(gaps) if len(gaps) > 1 else 0.0
    event_counts = Counter(event["event_type"] for event in ordered)
    pages = [event.get("page", "") for event in ordered if event["event_type"] == "page_view"]
    unique_pages = len(set(page for page in pages if page))
    api_count = event_counts["api_call"]
    ui_count = sum(event_counts[event_type] for event_type in ("click", "keystroke", "form_submit"))
    key_intervals = [
        event["key_interval_ms"]
        for event in ordered
        if event["event_type"] == "keystroke" and "key_interval_ms" in event
    ]
    key_entropy = 0.0
    if key_intervals:
        frequencies = Counter(min(10, interval // 50) for interval in key_intervals)
        total = len(key_intervals)
        key_entropy = -sum((count / total) * math.log2(count / total) for count in frequencies.values())
    first_action_gap = (
        ordered[1]["ts_ms"] - ordered[0]["ts_ms"] if len(ordered) > 1 else 0
    )
    devices = [event.get("device", {}) for event in ordered]
    return {
        "event_count": float(len(ordered)),
        "gap_mean_ms": float(gaps_mean),
        "gap_std_ms": float(gap_std),
        "gap_cv": float(gap_std / gaps_mean) if gaps_mean else 0.0,
        "gap_min_ms": float(min(gaps)) if gaps else 0.0,
        "time_to_first_action_ms": float(first_action_gap),
        "api_ratio": float(api_count / max(1, len(ordered))),
        "api_to_ui_ratio": float(api_count / max(1, ui_count)),
        "keystroke_count": float(event_counts["keystroke"]),
        "key_interval_entropy": float(key_entropy),
        "click_count": float(event_counts["click"]),
        "pointer_presence": float(sum("x" in event and "y" in event for event in ordered)),
        "page_count": float(event_counts["page_view"]),
        "unique_page_count": float(unique_pages),
        "navigation_revisit_rate": float(1 - unique_pages / max(1, len(pages))),
        "webdriver_flag": float(any(device.get("webdriver", False) for device in devices)),
        "headless_hint": float(any(device.get("headless_hint", False) for device in devices)),
        "transaction_count": float(event_counts["transaction"]),
    }
