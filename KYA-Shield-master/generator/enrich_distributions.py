from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


def _paysim_summary(path: Path) -> dict[str, Any]:
    amounts: list[float] = []
    types: Counter[str] = Counter()
    fraud = 0
    rows = 0
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            rows += 1
            types[row["type"]] += 1
            amounts.append(float(row["amount"]))
            fraud += int(row["isFraud"])
    return {
        "rows": rows,
        "fraud_rows": fraud,
        "fraud_rate": fraud / rows if rows else 0.0,
        "mean_amount": mean(amounts) if amounts else 0.0,
        "amount_quantiles": _quantiles(amounts),
        "transaction_types": dict(types),
    }


def _ieee_summary(path: Path, identity_path: Path | None) -> dict[str, Any]:
    amounts: list[float] = []
    fraud = 0
    rows = 0
    product_codes: Counter[str] = Counter()
    device_types: Counter[str] = Counter()
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            rows += 1
            amounts.append(float(row["TransactionAmt"]))
            fraud += int(row["isFraud"])
            product_codes[row["ProductCD"]] += 1
    if identity_path and identity_path.exists():
        with identity_path.open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                device_types[row.get("DeviceType") or "missing"] += 1
    return {
        "rows": rows,
        "fraud_rows": fraud,
        "fraud_rate": fraud / rows if rows else 0.0,
        "mean_amount": mean(amounts) if amounts else 0.0,
        "amount_quantiles": _quantiles(amounts),
        "product_codes": dict(product_codes),
        "identity_device_types": dict(device_types),
    }


def _quantiles(values: list[float]) -> dict[str, float]:
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0}
    ordered = sorted(values)
    return {
        name: round(ordered[min(len(ordered) - 1, int(len(ordered) * fraction))], 4)
        for name, fraction in (("p50", 0.50), ("p90", 0.90), ("p99", 0.99))
    }


def summarize(dataset_dir: Path, output: Path) -> dict[str, Any]:
    paysim = next(dataset_dir.glob("*_log.csv"), None)
    ieee_transaction = dataset_dir / "train_transaction.csv"
    if paysim is None or not ieee_transaction.exists():
        raise FileNotFoundError(
            "Expected PaySim *_log.csv and IEEE-CIS train_transaction.csv in the dataset directory."
        )
    summary = {
        "source_directory": str(dataset_dir),
        "paysim": _paysim_summary(paysim),
        "ieee_cis": _ieee_summary(
            ieee_transaction,
            dataset_dir / "train_identity.csv",
        ),
        "usage": (
            "Distribution enrichment only. These datasets do not provide KYA agent-session "
            "labels and are not mixed into the held-out session test set."
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-dir", type=Path, default=Path("dataset"))
    parser.add_argument("--output", type=Path, default=Path("data/external_summary.json"))
    args = parser.parse_args()
    summary = summarize(args.dataset_dir, args.output)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
