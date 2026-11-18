from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1]))

from kya.scoring_api import score_session


def main() -> None:
    sessions_path = Path(__file__).parents[1] / "data" / "sessions.jsonl"
    latencies: list[float] = []
    with sessions_path.open(encoding="utf-8") as sessions_file:
        for line in sessions_file:
            events = json.loads(line)["events"]
            started = time.perf_counter_ns()
            score_session(events)
            latencies.append((time.perf_counter_ns() - started) / 1_000_000)
    ordered = sorted(latencies)
    p50 = statistics.median(ordered)
    p95 = ordered[max(0, int(len(ordered) * 0.95) - 1)]
    print(f"sessions={len(ordered)}")
    print(f"p50_ms={p50:.4f}")
    print(f"p95_ms={p95:.4f}")
    print(f"budget_ms=100.0000")
    print(f"within_budget={p95 < 100}")


if __name__ == "__main__":
    main()
