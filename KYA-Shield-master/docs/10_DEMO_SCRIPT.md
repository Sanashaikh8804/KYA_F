# 10. Finals presentation and live demo plan

20 minutes presentation + live demo, then 5 minutes Q&A. Also a backup demo video (max 3 minutes) in case the live demo fails.

## Timeline (20 minutes)

| Time | Section | Content |
|---|---|---|
| 0:00-2:00 | Problem | Agents are paying on behalf of customers; hijacked agents look clean; one slide with the injected-payee story |
| 2:00-5:00 | Approach | Architecture diagram: detector, signed mandate, drift, cost-based policy, out-of-band step-up |
| 5:00-12:00 | **Live demo** | Three scenarios below, dashboard on screen |
| 12:00-16:00 | Results | Results summary table, ablation (mandate-only vs drift-only vs full), unseen-config numbers, cost vs baselines |
| 16:00-18:00 | Responsible design | Reason codes, hard overrides, consent-based data, limitations |
| 18:00-20:00 | Limitations and next steps | Honest limits (synthetic data, small human sample), mandate standards, pilots |

## Live scenarios (run in real time; show class, trust score, action, reason codes)

1. **Human session.** A teammate logs in, checks balance, adds a known payee, pays a merchant. Expected: human, high trust, allow.
2. **Legitimate agent inside its mandate.** Agent with a signed mandate buys groceries from an allowed merchant under the cap. Expected: LLM agent, high trust, allow.
3. **Prompt-injected agent.** Same agent loads a product page with hidden instructions, adds a new payee and tries to pay. Expected: LLM agent, low trust, **hold or block depending on confidence** (by expected cost, block wins when fraud probability is high; for a INR 2,990 payment, hold only beats block below roughly 0.54, see `examples/make_examples.py`). Reason codes: payee outside mandate, new payee after external content. Show the out-of-band confirmation or notification going to the customer. Prepare one lower-confidence case so the audience also sees a hold and a step-up.
4. **Bonus (in-scope hijack).** Injected agent pays an allowed merchant but at the cap in a switched category. Show that a mandate-only variant would allow it while the full system holds it.

## Dashboard must show

Event stream, agent class with probabilities, trust score gauge, chosen action, ranked reason codes, scoring latency in ms, and the expected cost of each candidate action.

## Required notes to include

- **Scenario note:** typologies covered (T1, T2, T3, plus any stretch) and how each was simulated
- **Cost matrix used:** the brief's default (show the table)
- Final slide: results summary table with "not attempted" where applicable

## Rehearsal checklist

- [ ] Clean-clone test of `make demo` on the presenting laptop
- [ ] Offline-safe: the demo must not need the internet or paid APIs
- [ ] Pre-recorded sessions as a fallback if a live agent misbehaves
- [ ] Backup video (max 3 min) exported and on a USB drive
- [ ] Two full timed rehearsals; one Q&A rehearsal with a friend asking hard questions

## Likely judge questions (prepare answers)

1. How do you know the model is not just detecting your own generator's quirks? (unseen framework/attack, configuration-based splits)
2. What if the attacker also forges the mandate? (signature verification, key custody in future work)
3. What does mandate adoption require from agent builders? (SDK, open spec, AP2 alignment)
4. Why not just block all agents? (friction cost; cost matrix shows blocking legitimate agents is expensive)
5. How does it hold up against human-mimicking agents? (hard-mode results, and drift signals that do not depend on timing)
