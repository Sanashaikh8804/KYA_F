# 04. Requirements checklist (brief to our plan)

Tick as you go. "Where" is the file/module that satisfies each item.

## Scoring API

| Requirement from brief | Where | Done |
|---|---|---|
| Function/API: one session's event log in, decision out | `kya/scoring_api.py` | [ ] |
| Input: time-ordered JSON events with session ID, ts (ms), event type, device/client attrs; transactions with amount, payee, new-payee flag, merchant category, mandate | `schemas/event_schema.json` | [ ] |
| Added fields documented | `schemas/event_schema.json` + `docs/ASSUMPTIONS.md` | [ ] |
| Output: agent class (human / scripted bot / LLM agent), trust score 0-100, action, ranked reason codes, latency ms | `schemas/decision_schema.json` | [ ] |

## Dataset

| Requirement | Where | Done |
|---|---|---|
| >= 1,000 labelled sessions | `data/labels.csv` | [ ] |
| >= 50 human sessions | `data/DATASHEET.md` | [ ] |
| Held-out test with at least one unseen agent framework or attack configuration | `data/SPLITS.md` | [ ] |
| Submit generator, dataset, labels | `generator/`, `data/` | [ ] |
| Humans from team/volunteers with informed written consent | `docs/05_DATASET_SPEC.md` consent form | [ ] |
| Cite every dataset, respect licences | `data/DATASHEET.md` | [ ] |
| Declare paid/closed APIs used for data generation | `data/DATASHEET.md` | [ ] |

## Tracks (core mandatory; deep on at least one)

| Track | Plan | Done |
|---|---|---|
| Agent detection (hard mode reported separately) | P3 | [ ] |
| Agent trust scoring (delegation validity, mandate scope, behavioural consistency, provenance) | P4 (our deep track) | [ ] |
| Agentic fraud typologies (document each + how simulated) | P2 + P4 | [ ] |

## Bank-realistic constraints

| Constraint | Plan | Done |
|---|---|---|
| p95 < 100 ms scoring path on laptop CPU | `eval/latency.py` | [ ] |
| Reason codes readable by analyst/auditor | `kya/reasons.py` | [ ] |
| Cost of error using default matrix | `config/cost_matrix.json`, `eval/cost.py` | [ ] |
| Privacy: engineered features; only synthetic/public data | `kya/features.py`, `data/DATASHEET.md` | [ ] |

## Success metrics (one row each in results table)

| Metric | Done |
|---|---|
| Macro-F1 + per-class recall (hard-mode separate) | [ ] |
| ROC-AUC + PR-AUC malicious vs legitimate, incl. unseen config | [ ] |
| Expected cost per 1,000 sessions vs allow-all and rule-based | [ ] |
| p50 and p95 latency vs 100 ms | [ ] |
| Share of decisions with reason codes (target 100%) | [ ] |

## General ground rules

| Rule | Plan | Done |
|---|---|---|
| Self-contained; state assumptions | `docs/ASSUMPTIONS.md` | [ ] |
| Honest evaluation: held-out never used for training/tuning; at least one simple baseline | `eval/` | [ ] |
| Results reproducible from repo | `make eval`, README | [ ] |
| Core solution runs from submitted code (no paid API at inference) | architecture | [ ] |

## Finals submission

| Item | Done |
|---|---|
| Code repo + README (setup, run demo, reproduce every number) | [ ] |
| Technical report (max 6 pages) | [ ] |
| Results summary table (metric, value, test set, baseline; "not attempted" where applicable) | [ ] |
| Demo video (max 3 min) | [ ] |
| Live demo: >=1 human, >=1 legitimate agent, >=1 malicious agent in real time showing class, score, action, reason codes | [ ] |
| Scenario note: typologies covered + cost matrix used | [ ] |
