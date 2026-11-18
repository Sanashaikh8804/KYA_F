from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Any

from .mandate_issuer import issue_mandate


DEFAULT_SEED = 20261109
DEFAULT_COUNT = 1600
CLASSES = ("human", "scripted_bot", "llm_agent")
PRINCIPALS = ("cust-001", "cust-002", "cust-003")


def _event(
    session_id: str,
    timestamp: int,
    event_type: str,
    *,
    agent_class: str,
    framework: str,
    **fields: Any,
) -> dict[str, Any]:
    automated = agent_class != "human"
    return {
        "session_id": session_id,
        "ts_ms": timestamp,
        "event_type": event_type,
        "device": {
            "user_agent": "KYA-Shield synthetic client",
            "platform": "Windows",
            "screen_w": 1920,
            "screen_h": 1080,
            "webdriver": automated,
            "headless_hint": automated,
            "ip_hash": "synthetic",
        },
        "client": {
            "client_type": "browser",
            **({"framework_hint": framework} if automated else {}),
        },
        **fields,
    }


def make_session(index: int, rng: random.Random) -> tuple[dict[str, Any], dict[str, Any]]:
    session_id = f"s-{index:05d}"
    if index < 120:
        agent_class, intent, framework, typology, augmented = "human", "legitimate", "human", "none", False
    elif index < 500:
        agent_class, intent, framework, typology, augmented = "scripted_bot", "legitimate", "requests", "none", False
    elif index < 1000:
        agent_class, intent, framework, typology, augmented = "llm_agent", "legitimate", "browseragent_A", "none", False
    else:
        agent_class, intent, framework, augmented = "llm_agent", "malicious", "browseragent_A", False
        typology = ("T1", "T2", "T3", "T4")[(index - 1000) % 4]
    hard_mode = (agent_class != "human" and index % 5 == 0)
    if index == 500 or 1540 <= index < 1560:
        framework = "browseragent_B"
    elif 1450 <= index < 1500:
        framework = "toolcall_llm_C"
    split = (
        "test"
        if index in {500, 1550} or framework in {"browseragent_B", "toolcall_llm_C"} or typology in {"T3", "T4"} or index % 20 == 0
        else ("val" if index % 5 == 0 else "train")
    )
    if index == 1550:
        framework, split = "browseragent_B", "test"
    principal = PRINCIPALS[index % len(PRINCIPALS)]
    sid_ts = 1_794_000_000_000 + index * 100_000
    events = [
        _event(session_id, sid_ts, "page_view", agent_class=agent_class, framework=framework, page="login", dwell_ms=0),
        _event(session_id, sid_ts + rng.randint(200, 2000), "api_call", agent_class=agent_class, framework=framework, api_endpoint="/login", http_method="POST"),
    ]
    mandate = None
    if agent_class == "llm_agent":
        mandate, _ = issue_mandate(
            principal_id=principal,
            agent_id=f"agent-{index:05d}",
            now=__import__("datetime").datetime.fromtimestamp(sid_ts / 1000, __import__("datetime").timezone.utc),
            key_id=f"principal:{principal}",
        )
    if intent != "legitimate":
        events.append(_event(
            session_id, sid_ts + 3000, "page_view", agent_class=agent_class, framework=framework,
            page="product_page", content_origin="external", dwell_ms=2200,
        ))
        payee, new_payee, amount = (
            ("ACME-9921", True, 2990.0) if typology == "T1"
            else ("FRESHMART", False, 3000.0) if typology == "T2"
            else ("MULE-001", True, 250.0) if typology == "T3"
            else ("URGENT-PAYEE", True, 875.0)
        )
    else:
        payee, new_payee, amount = "FRESHMART", False, rng.choice((1180.0, 2450.0))
    events.append(_event(
        session_id, sid_ts + 6000, "transaction", agent_class=agent_class, framework=framework,
        amount=amount, payee=payee, new_payee=new_payee, merchant_category="grocery",
        **({"mandate": mandate} if mandate else {}),
    ))
    label = {
        "session_id": session_id, "agent_class": agent_class, "intent": intent,
        "typology": typology, "framework": framework, "hard_mode": str(hard_mode).lower(),
        "has_mandate": str(mandate is not None).lower(), "principal_id": principal,
        "augmented": str(augmented).lower(), "split": split,
    }
    return label, {"session_id": session_id, "events": events}


def build_dataset(output_dir: Path, count: int = DEFAULT_COUNT, seed: int = DEFAULT_SEED) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    labels: list[dict[str, Any]] = []
    sessions_path = output_dir / "sessions.jsonl"
    with sessions_path.open("w", encoding="utf-8") as sessions_file:
        for index in range(count):
            label, session = make_session(index, rng)
            labels.append(label)
            sessions_file.write(json.dumps(session, sort_keys=True) + "\n")
    with (output_dir / "labels.csv").open("w", newline="", encoding="utf-8") as labels_file:
        writer = csv.DictWriter(labels_file, fieldnames=list(labels[0]))
        writer.writeheader()
        writer.writerows(labels)
    (output_dir / "SPLITS.md").write_text(
        "# Dataset splits\n\n"
        f"Generated with seed `{seed}` and `{count}` sessions. Splits are configuration-based.\n\n"
        "- Test includes unseen frameworks `browseragent_B` and `toolcall_llm_C`.\n"
        "- Test includes unseen T3 mule-account farming and T4 urgent-payee attack configurations.\n"
        "- No test labels are used by the generator for model fitting or tuning.\n",
        encoding="utf-8",
    )
    (output_dir / "DATASHEET.md").write_text(
        "# Dataset datasheet\n\n"
        "All sessions are synthetic and target the local mock bank. No real bank, customer, "
        "credential, or payment data is used. Human rows are placeholders until consented "
        "collection is performed; they are marked `augmented=false` only to preserve the "
        "label schema and must not be reported as real human data.\n\n"
        f"Seed: `{seed}`. Regenerate with `python -m generator.build_dataset --output data`.\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("data"))
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    build_dataset(args.output, args.count, args.seed)


if __name__ == "__main__":
    main()
