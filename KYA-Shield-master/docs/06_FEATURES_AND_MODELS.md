# 06. Features, models and reason codes

## A. Agent detection features (human vs scripted bot vs LLM agent)

| Group | Features |
|---|---|
| Timing | mean / std / CV of inter-event gaps, min gap, burstiness, long-pause-then-burst count (LLM "think then act" signature), time to first action |
| Keystrokes | inter-key interval stats and entropy, backspace rate, paste events, chars per second in form fill |
| Pointer / scroll | presence of click coordinates, pointer path noise, scroll events per page, click target precision |
| Navigation | path length to goal, navigation entropy, revisit rate, directness (fraction of pages that lead to the goal) |
| API vs UI | ratio of api_call to click/keystroke events, direct API-only sessions |
| Client | webdriver/automation flags, user-agent consistency, headless hints, screen/viewport anomalies |
| Pattern repetition | similarity to other sessions in the same time window (template reuse) |

Models: 3-class LightGBM with calibrated probabilities. **Baseline**: simple rule thresholds (e.g. CV of gaps, webdriver flag, API ratio). Report macro-F1, per-class recall, confusion matrix; hard-mode sessions reported separately.

## B. Mandate scope features (hard checks, kya/mandate.py)

| Check | Violation code |
|---|---|
| Signature invalid | R100 |
| Mandate expired / not yet valid | R103 |
| Replay (nonce reused) | R104 |
| Agent ID not bound to mandate | R105 |
| Payee not in allow-list (when list present) | R101 |
| Merchant category not permitted | R106 |
| Amount over per-transaction cap | R102 |
| Cumulative amount over total cap | R107 |
| Frequency limit exceeded | R108 |
| Transaction with no mandate while agent class is LLM/bot | R109 |

## C. Intent-drift features (soft, kya/drift.py)

| Feature | Intuition |
|---|---|
| `new_payee_after_external_content` | Payee added shortly after external content loaded: classic injection signature |
| `secs_from_external_load_to_payee_add` | Short gap = suspicious |
| `category_switch_vs_task` | Spend category differs from the mandate's task category |
| `amount_ratio_to_cap` and `amount_zscore_vs_history` | In-scope but unusual for this principal |
| `api_pattern_shift` | API-call distribution changes after external content load |
| `rhythm_change` | Change in event cadence mid-session |
| `payee_reuse_across_sessions` | Mule-farming signal |
| `n_new_payees_in_session` | Multiple fresh payees |
| `txn_velocity` | Many transactions quickly |

## D. History and provenance features

Principal's typical amounts, categories, known payees, usual hours; agent provenance (registered framework/agent ID, age of registration, prior session outcomes in the simulator).

## E. Trust model (kya/trust.py)

1. Hard mandate violations cap the trust score (e.g. any R100/R101/R102 caps at <= 25).
2. Otherwise a LightGBM risk model over drift + behaviour + history + provenance gives a calibrated `p_fraud`.
3. Trust score = `round(100 * (1 - p_fraud))`, then the caps from step 1 are applied.
4. Calibration on validation (isotonic or Platt); report calibration quality.

Ablations: **mandate-only**, **drift-only**, **behaviour-only**, **full**. This table is our main evidence for the intent-firewall claim.

## F. Cost-based policy (kya/policy.py)

For each action a, expected cost = `P(legit) * legit_cost[a] + P(fraud) * fraud_fraction[a] * amount`. Choose the minimum. Baselines: **allow-all** and a **simple rule-based policy** (e.g. block if no mandate and agent; hold if new payee; else allow).

Cost matrix is in `config/cost_matrix.json` (the brief's default). We may substitute justified values; record any change.

## G. Reason codes (kya/reasons.py)

- Rule-based codes from B and C (analyst-readable sentences)
- Top contributing model features (LightGBM `pred_contrib=True`) mapped to templates
- Ranked by contribution; return top 3-5
- Fallback `R000: Behaviour consistent with the principal's mandate and history` so **100%** of decisions carry a code

Example output:

```
1. R101 Payee 'ACME-9921' is not in the mandate's allowed payees.
2. R201 New payee added 4.2 s after external page content was loaded.
3. R300 Amount is 3.8x this customer's typical shopping payment.
```

## H. Latency tips

Keep features vectorised (NumPy), small trees (<=300 trees), avoid pandas in the hot path, load models once at startup, and benchmark with `eval/latency.py` on the test set.
