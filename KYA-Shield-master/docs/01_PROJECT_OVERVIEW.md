# 01. Project overview

## The problem

AI agents now browse, decide and pay on behalf of customers. Bank fraud controls were built for humans (typing cadence, device, navigation) and classical bots (scripts, credential stuffing). Agents sit in between. They can be legitimate, compromised, hijacked through prompt injection, or built for fraud at scale. Existing controls cannot reliably identify them or tell good agents from bad ones.

## What the brief asks for

For a stream of payment and banking interactions:
1. Detect whether a non-human agent is involved
2. Produce an explainable **Agent Trust Score** (how safe it is to let the action proceed)
3. Recommend a real-time action: **allow, step-up authentication, hold or block**

Exposed as a function/API: one session's event log in, a decision out.

## Our idea: the intent firewall

The hard cases are not "is it a bot". A hijacked legitimate agent has a valid credential, a known device and a clean history. Its reasoning is the compromised part, so we do not trust it. We trust only the **customer's signed intent**.

1. **Signed mandate.** When a customer delegates a task, the app issues a signed mandate (principal, agent, allowed merchant categories, amount cap, frequency, expiry).
2. **Scope checks (hard).** Signature, expiry, replay, amount, merchant category, payee, frequency.
3. **Intent drift (soft).** Behaviour changes inside the session that scope checks alone miss: a new payee right after external content loaded, an in-scope amount that is abnormal for this principal, a category switch, a changed API rhythm.
4. **Cost-based action.** Choose the action with minimum expected cost under the brief's cost matrix.
5. **Out-of-band step-up.** Hold and step-up go to the human customer, never back to the agent.

## Why this is differentiated

- Targets the agent-specific attack (prompt-injected redirection), not generic bot traffic
- Framework-agnostic: needs only the session log and the mandate
- Catches in-scope abuse that a pure mandate check misses (the combination of mandate + drift is the original part)
- Clear evaluation story: ablation "mandate-only vs drift-only vs both" on an **unseen** attack configuration

## Track focus

- Core pipeline (mandatory): detection + trust score + action with reason codes, behind the scoring API
- Go deep on: **Agent trust scoring** (+ signed mandate scheme, which is a stretch goal)
- Typologies to simulate (document each): (1) prompt-injected payee redirect, (2) in-scope amount/category drift, (3) mule-account farming. Stretch: automated APP-scam agent, synthetic-identity onboarding at scale.
- Hard mode (agents that mimic human timing/navigation) reported separately

## Out of scope

Real bank integration, real customer data, production-grade key management, any attack on a real site or payment system.
