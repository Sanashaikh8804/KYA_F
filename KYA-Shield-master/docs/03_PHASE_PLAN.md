# 03. Phase plan (9 Nov to 18 Dec 2026)

Round 1 is plan-only, but the shortlist lands on 4 Dec and finals start 15 Dec, so **start building now**. Phases overlap; the Round 1 abstract is the critical path first.

| Phase | Dates | Goal | Main owner | Done when |
|---|---|---|---|---|
| P0 Register + abstract | 9-30 Nov | Team formed, registered, abstract + diagram submitted | Team leader | Abstract submitted by 30 Nov, one submission only |
| P1 Mock bank + logging | 10-16 Nov | Bank app emitting schema-valid events | Backend | 3 sample sessions validate against schema |
| P2 Generator + dataset | 14-24 Nov | >=1,600 labelled sessions, splits with unseen config | Data/generator | Labels reproducible; SPLITS.md documents the unseen framework + attack |
| P3 Detection | 22 Nov - 1 Dec | Human/bot/LLM classifier | ML | Macro-F1, per-class recall, hard-mode reported |
| P4 Mandate + trust + drift | 25 Nov - 6 Dec | Intent firewall | ML + Backend | Unit tests pass; ablation table exists |
| P5 Policy + API | 3-8 Dec | Cost-based action, reason codes, scoring API | Backend | p95 < 100 ms; 100% reason codes |
| P6 Evaluation | 6-11 Dec | All five metrics, baselines, ablations | ML | `make eval` regenerates `docs/RESULTS.md` |
| P7 Demo + report + video | 9-14 Dec | Dashboard, 6-page report, <=3 min video | Frontend/docs | `make demo` works from a clean clone |
| Finals | 15-18 Dec | 20 min talk + live demo + 5 min Q&A | All | Backup video ready |

## Weekly checkpoints

| Week of | Checkpoint |
|---|---|
| 9 Nov | Team locked, registration done, abstract outline, mock bank skeleton |
| 16 Nov | Abstract draft reviewed by everyone; mock bank complete; first bot/LLM sessions generated |
| 23 Nov | Abstract final and submitted early (do not wait for 30 Nov); dataset v1 |
| 30 Nov | Detection model trained; mandate verifier + drift features in progress |
| 7 Dec | Full pipeline end to end; evaluation running |
| 14 Dec | Demo rehearsed twice; report and video done; repo clean-clone test |

## What must exist for finals (Minimum Viable)

- End-to-end pipeline (detection, trust score, action with reason codes) behind the scoring API
- Self-built labelled dataset meeting the minimum size and split
- Results on all success metrics, with depth in at least one track

## Stretch goals (attempt in this order)

1. Signed-mandate scheme with scope checks on amount, merchant and frequency (already core to our idea)
2. Hard-mode results for human-mimicking agents
3. Multiple agentic fraud typologies, each documented

## Cut list if time runs short

Drop in this order: extra typologies, second LLM-agent framework (keep one seen + one unseen), fancy dashboard polish. Never drop: held-out unseen config, baselines, reason codes, latency measurement, reproducibility.
