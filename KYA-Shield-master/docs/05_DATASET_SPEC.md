# 05. Dataset specification

No data is provided. We build and label our own. Minimum: **1,000 labelled sessions, at least 50 human**, with a held-out test set containing **at least one agent framework or attack configuration unseen in training**. We submit the generator, dataset and labels.

## Target composition (1,600 sessions)

| Group | Count | Notes |
|---|---|---|
| Human | 120 | At least 50 real sessions from consenting teammates/volunteers; rest may be augmented and must be marked `augmented=true` |
| Scripted bot | 380 | Plain HTTP, Selenium, Playwright. Benign automation (e.g. a scheduled balance check) and malicious (credential stuffing, card testing, rapid payee adds). Includes **80 hard-mode** bots that mimic human timing/navigation |
| LLM agent, legitimate | 500 | Operating inside a valid signed mandate (shopping, bill pay, transfers to listed payees) |
| LLM agent, malicious/compromised | 600 | Prompt-injected payee redirect, in-scope amount/category drift, mule-account farming. Includes **120 hard-mode** agents that add human-like delays/mouse noise |
| **Total** | **1,600** | |

Adjust counts if time is short, but never go below 1,000 total or 50 real humans.

## Typologies to simulate (document each)

| Typology | How it is simulated | Expected signal |
|---|---|---|
| T1 Prompt-injected payee redirect | Product page contains hostile instructions; agent adds a new payee and pays them | new payee after external content, payee outside mandate |
| T2 In-scope amount/category drift | Injection nudges the agent to spend up to the cap or switch category within allowed list | amount creep vs history, category switch, rhythm change |
| T3 Mule-account farming | Many accounts/sessions add the same payee and move small amounts | payee reuse across sessions, burst structure |
| T4 (stretch) Automated APP scam agent | Agent pressures a simulated user to send a transfer | urgency pattern, new payee, unusual amount |
| T5 (stretch) Synthetic-identity onboarding at scale | Bursts of signups with templated identity fields | high-rate repetitive forms |

## Label schema (`data/labels.csv`)

| Column | Values |
|---|---|
| session_id | unique |
| agent_class | human / scripted_bot / llm_agent |
| intent | legitimate / malicious / compromised |
| typology | none / T1 / T2 / T3 / T4 / T5 / credential_stuffing / card_testing |
| framework | e.g. human, requests, selenium, playwright, browseragent_A, toolcall_llm_B |
| hard_mode | true / false |
| has_mandate | true / false |
| principal_id | seeded principal |
| augmented | true / false (humans only) |
| split | train / val / test |

## Splits (by configuration, not random rows)

- `train` and `val`: seen frameworks and attacks
- `test`: contains **at least one unseen agent framework** (e.g. a second open-source browser-agent framework, or a differently prompted tool-calling LLM) **and one unseen attack configuration** (e.g. injection delivered through a payee nickname field or an invoice page instead of the product page)
- Choose the unseen configuration up front, write it in `data/SPLITS.md`, and never touch it during training or tuning.

## Human data collection (needs written consent)

1. Give each volunteer a one-page consent form (below) and keep the signed copies privately, not in the repo.
2. Each volunteer does 3-5 short tasks in the mock bank (e.g. "check balance, add a payee, pay a merchant"), on their own device.
3. Record only event timings and interaction metadata. **Never record the values typed in password fields** and no real personal data; use fake account details in the mock bank.
4. Store a hashed volunteer ID, not names, in the dataset.

### Consent form (template)

> I agree to take part in a student hackathon project. I will use a mock banking website with fake data. The site records how I click, scroll and type (timing only, not what I type into password fields) so it can be used to train and test a fraud-detection model. No real bank, personal or financial data is collected. My data will be stored under a pseudonymous ID, used only for this project and the submission, and I can ask for it to be deleted at any time before submission.
> Name / Signature / Date / Contact (kept separately from the data)

## Public datasets (enrichment only)

| Dataset | Use | Action |
|---|---|---|
| PaySim | Transaction amount/type distributions | Cite; check licence |
| IEEE-CIS Fraud Detection | Merchant/amount/device feature ideas | Cite; check licence (Kaggle competition terms) |
| Google AP2 (Agent Payments Protocol) | Reference for mandate format | Cite as design reference |

## DATASHEET.md must include

Sources and licences, consent process, how each group was generated, frameworks and versions, **every paid/closed API used for generation (declared)**, known biases (small human sample, simulated attackers), seed values, and how to regenerate.

## Hard-mode construction

- Scripted: sample inter-event delays from a human-like distribution, add mouse movement and scroll noise, random typos/backspaces
- LLM: insert thinking-time delays, jittered typing speed, simulated mouse paths, human-style navigation (visit a few irrelevant pages first)
- Report hard-mode results separately and honestly. It is expected to be harder.
