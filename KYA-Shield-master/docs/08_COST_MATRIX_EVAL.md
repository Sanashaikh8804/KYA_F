# 08. Cost matrix, metrics and evaluation plan

## Default cost matrix (from the brief)

| Actual \ Action | Allow | Step-up | Hold | Block |
|---|---|---|---|---|
| Legitimate (human or authorised agent) | INR 0 | INR 20 | INR 150 | INR 500 |
| Fraudulent or compromised agent | 100% of amount | 30% of amount | 10% of amount | INR 0 |

Machine-readable copy: `config/cost_matrix.json`. We may substitute justified values; document any change.

## Success metrics (all five reported)

| # | Metric | Detail |
|---|---|---|
| 1 | Macro-F1 and per-class recall | human / scripted bot / LLM agent; **hard-mode reported separately** |
| 2 | ROC-AUC and PR-AUC | malicious vs legitimate sessions; include the **unseen** framework/attack configuration |
| 3 | Expected cost per 1,000 sessions | vs allow-all baseline and simple rule-based baseline |
| 4 | p50 and p95 scoring latency | vs the 100 ms budget |
| 5 | Share of decisions with reason codes | target 100% |

## Baselines

| Baseline | Definition |
|---|---|
| Allow-all | Always allow (expected cost = all fraud amount) |
| Rule-based | Block if no mandate and agent detected; hold if new payee and external content; else allow |
| Detection baseline | Threshold rules on timing CV, webdriver flag, API ratio |

## Ablations

| Variant | Purpose |
|---|---|
| Mandate-only | Shows what hard scope checks catch |
| Drift-only | Shows what behaviour drift catches |
| Behaviour-only | Classic bot/agent detection signals |
| Full (mandate + drift + behaviour + history) | Our system |

Hypothesis to prove: **mandate-only misses in-scope hijacks and unseen attack forms; drift adds recall there; the full system gives the lowest expected cost.**

## Evaluation protocol (honest evaluation)

1. Split by configuration, not random rows (see `05_DATASET_SPEC.md`).
2. Tune hyperparameters and policy settings on validation only.
3. Evaluate once on test at the end; report the unseen-config numbers separately.
4. Repeat training with at least 3 seeds; report mean and spread.
5. Report calibration (reliability plot or ECE) since the policy depends on probabilities.
6. Every reported number must regenerate with `make eval`.

## Results summary table (template for the final submission)

| Metric | Our value | Test set | Baseline value | Status |
|---|---|---|---|---|
| Macro-F1 (human/bot/LLM) | | test (seen) | | |
| Macro-F1 hard-mode | | test hard-mode | | |
| Per-class recall (human / bot / LLM) | | test | | |
| ROC-AUC malicious vs legit | | test seen / unseen | | |
| PR-AUC malicious vs legit | | test seen / unseen | | |
| Expected cost per 1,000 sessions | | test | allow-all: ; rules: | |
| p50 latency (ms) | | laptop CPU | 100 ms budget | |
| p95 latency (ms) | | laptop CPU | 100 ms budget | |
| Decisions with reason codes (%) | | test | target 100% | |
| Mandate-only vs drift-only vs full (ablation) | | test | | |

Use "not attempted" for anything skipped; do not omit rows.

## Expected-cost computation (reference)

```
cost(session, action) =
   legit_cost[action]                         if session is legitimate
   fraud_fraction[action] * transaction_amount if session is fraudulent/compromised
expected_cost_per_1000 = 1000 * mean(cost over sessions using the chosen action)
```

Sessions with several transactions: score at the transaction level and sum, or use the largest-amount transaction; state the choice in `ASSUMPTIONS.md`.
