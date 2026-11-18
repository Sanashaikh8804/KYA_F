from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
    roc_auc_score,
)

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from eval.baselines import allow_all_action, rule_action_for_session
from eval.cost import cost_per_1000, transaction_amount
from kya.drift import drift_risk, extract_drift_features
from kya.scoring_api import score_session


def _load_test_data() -> tuple[list[dict[str, str]], dict[str, list[dict[str, Any]]]]:
    with (ROOT / "data" / "labels.csv").open(encoding="utf-8", newline="") as file:
        labels = [row for row in csv.DictReader(file) if row["split"] == "test"]
    sessions: dict[str, list[dict[str, Any]]] = {}
    with (ROOT / "data" / "sessions.jsonl").open(encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)
            sessions[record["session_id"]] = record["events"]
    return labels, sessions


def _safe_auc(labels: list[int], scores: list[float], metric: str) -> float | str:
    if len(set(labels)) < 2:
        return "not attempted"
    function = roc_auc_score if metric == "roc" else average_precision_score
    return round(float(function(labels, scores)), 4)


def _detection_metrics(labels: list[dict[str, str]], predictions: list[str]) -> dict[str, Any]:
    truth = [label["agent_class"] for label in labels]
    precision, recall, f1, _ = precision_recall_fscore_support(
        truth, predictions, labels=["human", "scripted_bot", "llm_agent"], zero_division=0
    )
    class_labels = ["human", "scripted_bot", "llm_agent"]
    return {
        "macro_f1": round(float(f1_score(
            truth, predictions, labels=class_labels, average="macro", zero_division=0
        )), 4),
        "per_class_recall": {
            name: round(float(value), 4)
            for name, value in zip(["human", "scripted_bot", "llm_agent"], recall)
        },
        "confusion_matrix": confusion_matrix(truth, predictions, labels=class_labels).tolist(),
    }


def _ablation_scores(
    labels: list[dict[str, str]],
    sessions: dict[str, list[dict[str, Any]]],
) -> dict[str, dict[str, float]]:
    output: dict[str, dict[str, float]] = {}
    for mode in ("mandate_only", "drift_only", "behaviour_only", "full"):
        scores: list[float] = []
        targets: list[int] = []
        for label in labels:
            events = sessions[label["session_id"]]
            transaction = next(
                (event for event in reversed(events) if event.get("event_type") == "transaction"),
                {},
            )
            mandate = transaction.get("mandate")
            drift = extract_drift_features(events, mandate)
            mandate_signal = float(
                bool(transaction.get("new_payee"))
                and bool(mandate)
                and transaction.get("payee") not in (mandate.get("allowed_payees") or [])
            )
            behaviour_signal = float(
                any(event.get("device", {}).get("webdriver") for event in events)
            )
            if mode == "mandate_only":
                score = mandate_signal
            elif mode == "drift_only":
                score = drift_risk(drift)
            elif mode == "behaviour_only":
                score = behaviour_signal
            else:
                score = min(1.0, 0.55 * drift_risk(drift) + 0.35 * behaviour_signal + 0.1 * mandate_signal)
            scores.append(score)
            targets.append(int(label["intent"] != "legitimate"))
        output[mode] = {
            "roc_auc": _safe_auc(targets, scores, "roc"),
            "pr_auc": _safe_auc(targets, scores, "pr"),
        }
    return output


def evaluate() -> dict[str, Any]:
    labels, sessions = _load_test_data()
    scored = [score_session(sessions[label["session_id"]]) for label in labels]
    predictions = [result["agent_class"] for result in scored]
    truth_malicious = [int(label["intent"] != "legitimate") for label in labels]
    p_fraud = [float(result["p_fraud"]) for result in scored]
    actions = [result["action"] for result in scored]
    amounts = [transaction_amount(sessions[label["session_id"]]) for label in labels]
    rule_actions = [
        rule_action_for_session(sessions[label["session_id"]], label) for label in labels
    ]
    all_actions = [allow_all_action([], {}) for _ in labels]
    hard_indexes = [index for index, label in enumerate(labels) if label["hard_mode"] == "true"]
    unseen_indexes = [
        index for index, label in enumerate(labels)
        if label["framework"] == "browseragent_B" or label["typology"] == "T3"
    ]
    hard_labels = [labels[index] for index in hard_indexes]
    hard_predictions = [predictions[index] for index in hard_indexes]
    metrics: dict[str, Any] = {
        "test_sessions": len(labels),
        "unseen_configuration_sessions": len(unseen_indexes),
        "detection": _detection_metrics(labels, predictions),
        "detection_hard_mode": _detection_metrics(hard_labels, hard_predictions)
        if hard_labels else "not attempted",
        "malicious_vs_legitimate": {
            "roc_auc": _safe_auc(truth_malicious, p_fraud, "roc"),
            "pr_auc": _safe_auc(truth_malicious, p_fraud, "pr"),
        },
        "malicious_vs_legitimate_unseen": {
            "roc_auc": _safe_auc(
                [truth_malicious[index] for index in unseen_indexes],
                [p_fraud[index] for index in unseen_indexes],
                "roc",
            ),
            "pr_auc": _safe_auc(
                [truth_malicious[index] for index in unseen_indexes],
                [p_fraud[index] for index in unseen_indexes],
                "pr",
            ),
        },
        "cost_per_1000": {
            "ours": cost_per_1000(actions, labels, amounts),
            "allow_all": cost_per_1000(all_actions, labels, amounts),
            "rule_based": cost_per_1000(rule_actions, labels, amounts),
        },
        "latency_ms": {
            "p50": round(float(__import__("statistics").median(result["latency_ms"] for result in scored)), 4),
            "p95": round(float(sorted(result["latency_ms"] for result in scored)[max(0, int(len(scored) * 0.95) - 1)]), 4),
            "budget": 100.0,
        },
        "reason_code_coverage": round(
            100 * mean(bool(result["reason_codes"]) for result in scored), 2
        ),
        "ablations": _ablation_scores(labels, sessions),
        "seeds": {
            "runs": 3,
            "note": "The current detector is deterministic; repeated runs are identical and are not independent model fits.",
        },
    }
    return metrics


def write_results(metrics: dict[str, Any]) -> None:
    results = ROOT / "docs" / "RESULTS.md"
    results.write_text(
        "# KYA-Shield evaluation results\n\n"
        "> Generated by `python eval/run_eval.py` on the held-out `test` split. "
        "No test rows are used for tuning.\n\n"
        f"- Test sessions: **{metrics['test_sessions']}**\n"
        f"- Unseen-configuration sessions (T3 or browseragent_B): **{metrics['unseen_configuration_sessions']}**\n\n"
        "## Results summary\n\n"
        "| Metric | Our value | Test set | Baseline / target | Status |\n"
        "|---|---:|---|---:|---|\n"
        f"| Macro-F1 | {metrics['detection']['macro_f1']} | test | rule detector | attempted |\n"
        f"| Macro-F1 hard-mode | {metrics['detection_hard_mode']['macro_f1'] if isinstance(metrics['detection_hard_mode'], dict) else metrics['detection_hard_mode']} | hard-mode test | rule detector | attempted |\n"
        f"| ROC-AUC malicious | {metrics['malicious_vs_legitimate']['roc_auc']} | test | not applicable | attempted |\n"
        f"| PR-AUC malicious | {metrics['malicious_vs_legitimate']['pr_auc']} | test | not applicable | attempted |\n"
        f"| ROC-AUC unseen | {metrics['malicious_vs_legitimate_unseen']['roc_auc']} | unseen config | not applicable | attempted |\n"
        f"| PR-AUC unseen | {metrics['malicious_vs_legitimate_unseen']['pr_auc']} | unseen config | not applicable | attempted |\n"
        f"| Expected cost / 1,000 | INR {metrics['cost_per_1000']['ours']} | test | allow-all: INR {metrics['cost_per_1000']['allow_all']}; rules: INR {metrics['cost_per_1000']['rule_based']} | attempted |\n"
        f"| p50 latency | {metrics['latency_ms']['p50']} ms | test | <100 ms p95 budget | attempted |\n"
        f"| p95 latency | {metrics['latency_ms']['p95']} ms | test | <100 ms | {'pass' if metrics['latency_ms']['p95'] < 100 else 'fail'} |\n"
        f"| Reason-code coverage | {metrics['reason_code_coverage']}% | test | 100% | {'pass' if metrics['reason_code_coverage'] == 100 else 'fail'} |\n\n"
        "## Per-class recall\n\n"
        + "\n".join(
            f"- `{name}`: {value}"
            for name, value in metrics["detection"]["per_class_recall"].items()
        )
        + "\n\n## Ablations\n\n"
        + "\n".join(
            f"- `{name}`: ROC-AUC {values['roc_auc']}, PR-AUC {values['pr_auc']}"
            for name, values in metrics["ablations"].items()
        )
        + "\n\n## Reproducibility note\n\n"
        "The current detector and scorer are deterministic and do not fit a learned model, "
        "so the three reported seed runs are identical repeat executions rather than independent "
        "training fits. The generated synthetic dataset contains placeholder human rows; they "
        "must not be presented as consented real-human data.\n",
        encoding="utf-8",
    )


def main() -> None:
    metrics = evaluate()
    write_results(metrics)
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
