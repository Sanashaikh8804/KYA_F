# Round 1 abstract: KYA-Shield

> **Before submitting:** replace every [BRACKET], delete this note, and keep the final text between 600 and 900 words. Only the team leader may submit, once, through the Techfest website, before 30 Nov. Attach the optional one-page architecture diagram (see `02_ARCHITECTURE.md`).

**Title:** KYA-Shield: an intent-bound trust firewall for AI agents in banking

## 1. Problem and domain chosen

Problem 2, Know Your Agent (KYA), under Fraud Detection and Prevention. Customers are starting to let AI agents pay for them, but bank controls cannot tell a legitimate agent from a hijacked one. Our team [TEAM: one line of background] finds this compelling because the most dangerous case, a legitimate agent steered by prompt injection, looks clean to every existing signal.

## 2. Understanding of the challenge

Detecting that an agent is present is the easy half. The hard half is deciding whether its action is safe. A hijacked shopping agent has a valid credential, a known device and normal history, so device and behaviour checks pass; its reasoning is the compromised component, so no score built on what the agent says can be trusted. Trust must be anchored in something the attacker cannot rewrite, within bank constraints: p95 latency under 100 ms, reason codes on every decision, and actions chosen under asymmetric costs (INR 500 for blocking a legitimate customer; up to 100% of the amount for missing fraud). With no data provided, we must also build and honestly evaluate our own dataset.

## 3. Proposed approach

**Agent detection.** Session features (inter-event timing and burstiness, keystroke and pointer presence, navigation entropy, API-to-UI ratio, automation flags, the think-then-burst signature of LLM agents) feed a calibrated LightGBM classifier for human, scripted bot and LLM agent. A threshold rule set is the baseline.

**Signed intent mandate.** The customer's delegation is an Ed25519-signed mandate (agent ID, allowed merchant categories, optional payee list, per-transaction and total caps, daily frequency, expiry, nonce), modelled on Google's AP2 concepts. The bank verifies signature, expiry, replay and every scope limit independently of the agent.

**Intent-drift scoring.** Scope checks miss hijacks that stay in scope, so we add drift features: a new payee shortly after external content loads, category switches against the mandated task, amount creep against history and cap, changed API rhythm, and payee reuse across sessions (mule farming). A LightGBM risk model yields a calibrated fraud probability and an Agent Trust Score (0 to 100). Hard mandate violations cap the score regardless of the model.

**Cost-based action and reasons.** The action (allow, step-up, hold, block) minimises expected cost under the brief's cost matrix. Reason codes come from rule flags plus top feature contributions, with a fallback code for 100% coverage. Holds and step-ups go to the customer out of band, so a hijacked agent cannot approve its own payment.

Stack: Python, FastAPI, LightGBM, Playwright/Selenium bots, an open-source browser-agent framework and a tool-calling LLM for agent sessions, `cryptography` for signing. No LLM or network call in the scoring path.

## 4. Minimum viable

At finals we will demo: (a) the end-to-end pipeline behind the specified scoring API; (b) our own dataset of about 1,600 labelled sessions (at least 50 real, consented humans) with a held-out test split containing an agent framework and an attack configuration unseen in training; (c) results on all five success metrics, with depth in trust scoring. Live scenarios: a human, a legitimate agent inside its mandate, and a prompt-injected agent redirecting payment.

## 5. Stretch ambitions

(1) The signed-mandate scheme with amount, merchant and frequency checks, the natural core of our trust track; (2) hard-mode results for human-mimicking agents, reported separately; (3) further typologies (APP-scam agents, synthetic-identity onboarding), each documented with its simulation.

## 6. Expected impact

For lenders, payment providers and banks that will let customers' agents transact, KYA-Shield cuts agent-enabled fraud loss while limiting friction, since interventions are chosen by expected cost. Impact is measured as expected cost per 1,000 sessions against allow-all and rule-based policies, malicious-session recall at a stated false-positive rate, and latency.

## 7. Novelty and differentiation

The obvious baseline is bot detection. We never trust agent reasoning: trust is anchored in the customer's signed intent, and the score combines hard mandate checks with intent drift, so in-scope hijacks are still caught. We ablate mandate-only, drift-only and full systems on an unseen framework and attack.

## 8. Evaluation plan

Macro-F1 and per-class recall (hard-mode separate); ROC-AUC and PR-AUC for malicious versus legitimate sessions, including the unseen configuration; expected cost per 1,000 sessions against allow-all and rule-based baselines; p50 and p95 latency against 100 ms; share of decisions with reason codes. Splits are by configuration, tuning uses validation only, results average at least three seeds, and every number regenerates from the repository. Data: our mock bank, consented humans and generated sessions; PaySim and IEEE-CIS for enrichment only, cited.

## 9. Responsible design

Engineered features only, synthetic or public data, consent-based human collection, no password values recorded. Reason codes on every decision. Hard checks override learned scores, step-up is out of band, and attacks are simulated only against our own mock bank. No demographic features; false-positive rates reported by device and client type. Paid APIs, if any, will be declared.

## 10. Feasibility and risks

[TEAM: each member and their skills, e.g. backend/API, ML, data generation, frontend.] The work splits into mock bank, generator, models and demo, planned to the 15 to 18 December finals. Risks: a small human sample (early recruitment, honest reporting), simulated attacks differing from real ones (several typologies, unseen test configuration), and explanation latency (tree-model contributions).
