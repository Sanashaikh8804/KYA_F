# 12. Rules to respect, risks and ethics

## Hackathon rules that can cost you points

| Rule | What to do |
|---|---|
| Self-contained: no data/APIs/mentoring provided | State every assumption in `docs/ASSUMPTIONS.md` |
| Data: public, synthetic or self-collected with written consent only; no real customer/personal data | Consent forms, pseudonymous IDs, mock-bank fake data |
| Cite every dataset, respect licences | `data/DATASHEET.md` |
| Paid/closed APIs allowed for generation/tooling but must be declared; core solution must run from submitted code | Declare in DATASHEET; no API call at inference |
| Honest evaluation: held-out never used for training/tuning; at least one simple baseline; results reproducible | Config-based splits, `make eval`, baselines |
| One submission per team; only the team leader submits | Agree on the leader now |
| Queries only through the Techfest portal Doubt section; email queries are not entertained | Use the portal |
| Solutions must be original and not protected by patents, copyrights or publications | Do not copy others' code wholesale; cite libraries |

## Employer and IP separation (important for you)

- Do not use any code, schemas, data, client knowledge or internal documents from your employer, even anonymised or "inspired by".
- Check your employment contract on side projects, outside activities and IP assignment **before** you register or build, and especially before any incorporation or startup application.
- Build everything on personal time and equipment.

## Ethics and safety

- Attack and malicious-agent simulation runs **only against our own mock bank**, never against real sites, real banks or real payment systems.
- Do not publish a ready-to-use attack toolkit. Publish the benchmark and generator in a form aimed at defence (documented, with the mock bank), and keep injection payloads generic.
- Human volunteers: informed written consent, delete on request, never record password values.
- Be honest in the report about limits: simulated attackers, small human sample, no real bank data.

## Technical risks and mitigations

| Risk | Mitigation |
|---|---|
| Model learns generator quirks, not real signal | Unseen framework/attack in test; configuration-based splits; multiple frameworks |
| Small real-human sample | Recruit 50+ volunteers early; report the limit; separate real vs augmented |
| Hard-mode agents defeat timing features | Rely on mandate + drift signals that do not depend on timing; report hard-mode separately |
| Latency from explanations | Tree-model contribution scores, small models, benchmark early |
| LLM agent frameworks are flaky | Pre-record fallback sessions; pin versions; keep a scripted-LLM fallback for the demo |
| Time shortage between shortlist (4 Dec) and finals (15 Dec) | Build P1-P4 before the shortlist; follow the cut list in `03_PHASE_PLAN.md` |
| Mandate signing misread as "not real security" | State clearly that key custody/revocation are future work; demonstrate verification logic and tests |
| Scope creep | Core pipeline first; typologies T1-T3 only until the core works |

## Things not to claim

- Do not claim real-world accuracy; claim results on our synthetic/self-collected benchmark.
- Do not claim the system is production ready.
- Do not claim to have used real bank data.
