# 11. Team roles (max 4 members)

Only the **team leader** can submit Round 1. Decide the leader first.

| Role | Owns | Phases |
|---|---|---|
| **1. Lead + backend/API** | Registration, abstract submission, mock bank, scoring API, policy, latency | P0, P1, P5 |
| **2. ML engineer** | Features, detector, trust model, calibration, ablations, evaluation | P3, P4, P6 |
| **3. Data/generator engineer** | Human collection, bot scripts, LLM agents, attacks, mandate issuer, dataset and datasheet | P2 |
| **4. Frontend + docs** | Demo dashboard, report, results table, video, presentation | P7 |

If you have fewer than four people, merge roles in this order: 4 into 1, then 3 into 2.

## Skills checklist (for the abstract's feasibility section)

- [ ] Python backend (FastAPI)
- [ ] ML with tabular data (LightGBM, calibration)
- [ ] Browser automation (Playwright/Selenium)
- [ ] LLM agent frameworks and tool calling
- [ ] Applied cryptography basics (Ed25519 signing)
- [ ] Frontend dashboard
- [ ] Technical writing

## Working agreements

- One repo, short branches, pull-request review by one other person
- Daily 10-minute sync in the last two weeks
- Shared `docs/ASSUMPTIONS.md` updated whenever a choice is made
- Nobody tunes on the test split; the ML owner holds the test-set key
