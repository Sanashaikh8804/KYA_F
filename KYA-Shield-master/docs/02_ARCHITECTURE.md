# 02. Architecture

## Data flow

```
 Customer app ──issues──> Signed Mandate (Ed25519)
        │                         │
        ▼                         ▼
 Agent (LLM / bot / human) ──> Mock Bank (web + API) ──events──> Session event log (JSON)
                                                                       │
                                                                       ▼
                                           ┌───────────────  KYA Scoring Service  ───────────────┐
                                           │ 1. Feature builder (timing, navigation, API ratios)  │
                                           │ 2. Agent detector  → human / scripted_bot / llm_agent│
                                           │ 3. Mandate verifier → hard scope violations          │
                                           │ 4. Intent-drift engine → soft drift signals          │
                                           │ 5. Trust model (LightGBM + calibration) → score 0-100│
                                           │ 6. Cost-based policy → allow/step_up/hold/block      │
                                           │ 7. Reason-code generator (rules + SHAP)              │
                                           └───────────────────────┬──────────────────────────────┘
                                                                   ▼
                                       Decision JSON {agent_class, trust_score, action, reasons, latency_ms}
                                                                   │
                                            hold / step_up ───────►│ Out-of-band confirmation to the human customer
```

## Components

| Component | Folder | Notes |
|---|---|---|
| Mock bank | `mockbank/` | FastAPI + simple web UI: login, balance, add payee, transfer, merchant payment; emits events |
| Generator | `generator/` | Humans (consented collector), scripted bots, LLM agents, attacks, mandate issuer |
| Features | `kya/features.py` | Per-session engineered features; no raw PII |
| Detector | `kya/detector.py` | 3-class LightGBM; baseline = rule thresholds |
| Mandate verifier | `kya/mandate.py` | Signature, expiry, replay, scope checks |
| Drift engine | `kya/drift.py` | Within-session intent-drift features |
| Trust model | `kya/trust.py` | Hard violations override; learned risk model; calibrated |
| Policy | `kya/policy.py` | Minimum expected cost; baselines (allow-all, rules) |
| Reasons | `kya/reasons.py` | Templated, ranked, always at least one code |
| API | `kya/scoring_api.py` | `score_session(events)` + FastAPI `POST /score` |
| Eval | `eval/` | Metrics, baselines, ablations, latency, cost |
| Demo | `demo/` | Live dashboard + 3 scenario runner |

## Latency budget (p95 < 100 ms, laptop CPU, excluding network)

| Stage | Target |
|---|---|
| Parse + validate | < 5 ms |
| Features | < 20 ms |
| Detector + trust model (tree models) | < 20 ms |
| Mandate + drift | < 10 ms |
| Policy + reasons (SHAP on a small tree model, or precomputed contribution lookup) | < 25 ms |
| Headroom | ~20 ms |

No LLM, no network, no disk-heavy calls in this path. Use `predict` on small LightGBM models; if SHAP is too slow, use `pred_contrib=True` in LightGBM.

## Key design choices

- **Never trust agent reasoning.** Only the signed mandate and observable behaviour matter.
- **Hard checks override learned scores.** A bad signature or out-of-scope payee caps the trust score regardless of the model.
- **Calibrated probabilities** feed the cost-based policy so expected cost is meaningful.
- **Step-up goes out-of-band** to the customer, so a hijacked agent cannot approve its own payment.
