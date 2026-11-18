# KYA-Shield

KYA-Shield is a local mock-bank and scoring-service prototype for the Perfios x IIT Bombay Techfest 2026 "Know Your Agent" problem.

## Phase 1: run the mock bank

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn mockbank.app:app --reload
```

Open `http://127.0.0.1:8000/`. The mock bank is local-only and uses seeded fake principals. It never connects to a real bank or payment system.

The API exposes:

- `POST /login`
- `GET /balance/{principal_id}`
- `POST /payees`
- `POST /transfer`
- `POST /merchant-payment`
- `GET /external-content`
- `GET /sessions/{session_id}/events`

Every request accepts an `X-Session-ID` header. The bank records client-side-compatible events through `/events` and server-side API/transaction events through the API endpoints.

## Tests

```powershell
pytest
```

## Project pack

The original planning documents, schemas, examples, and configuration are copied into this build folder. Assumptions and later phases will be added here without modifying `D:\KYA`.

## Current implementation status

- Phase 1: mock bank, browser UI, and schema-shaped event logging
- Phase 2: deterministic mandate/session generator and 1,600-session synthetic dataset
- Phase 3: low-latency session features and initial agent detector
- Phase 4: Ed25519 mandate verification, scope violations, intent-drift features, and capped trust scoring

Phase 4 APIs are available from `kya.mandate`, `kya.drift`, and `kya.trust`. The scoring endpoint and final dashboard are planned for Phase 5/7.

Phase 5 is also available:

```powershell
D:\anaconda\python.exe -m uvicorn mockbank.app:app --reload
```

Send a session event list to `POST http://127.0.0.1:8000/score`. The response contains the agent class, trust score, fraud probability, cost-based action, expected costs, ranked reason codes, and latency. Mandate verification requires the issuer's trusted Ed25519 public key when calling `score_session()` directly; the HTTP demo endpoint reports a supplied mandate as unverifiable unless a key registry is wired in.

Measure the scoring path with:

```powershell
D:\anaconda\python.exe eval\latency.py
```

## External datasets

If public downloads are available under `dataset\`, generate a derived summary without copying
the raw files:

```powershell
D:\anaconda\python.exe -m generator.enrich_distributions --dataset-dir dataset
```

This supports distribution enrichment only; it does not replace the synthetic KYA session labels
or the unseen-configuration test split.

## Next.js dashboard

The clean light operations dashboard lives in `demo\`. Start the API first, then:

```powershell
cd D:\KYA-Shield\demo
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Use the three scenario buttons to load
events from the FastAPI demo endpoints and send them to `POST /score`.

The demo scenarios now resolve as:

- Human customer: `allow`
- Authorised agent: `allow`
- Prompt-injected agent: `block`

## Production-style hardening

See [docs/PRODUCTION_CONTROLS.md](D:/KYA-Shield/docs/PRODUCTION_CONTROLS.md). For local testing:

```powershell
$env:KYA_API_KEY = "local-demo-key"
$env:KYA_SHADOW_MODE = "true"
D:\anaconda\python.exe -m uvicorn mockbank.app:app --host 127.0.0.1 --port 8000
```

With shadow mode enabled, the API preserves the recommendation in `recommended_action` but
returns `action=allow`. Every score is appended to `audit/events.jsonl`.

## Ollama agent session generation

Ollama is used only to generate realistic agent behavior; it is not called by `/score`.
The runner sends tool definitions to Ollama, executes the returned tool calls against the
local mock bank, captures model responses, tool arguments, tool results, timing, and all
server-side bank events, then scores the completed session.

Start the bank and Ollama first. Make sure a model is available with `ollama list`, then run:

```powershell
ollama pull llama3.1:8b
D:\anaconda\python.exe -m ollama_agent.runner "Log in as cust-001, check the balance, and pay 25 dollars to FRESHMART in the grocery category."
```

The trace is written to `data\ollama_sessions\latest.jsonl`. To use another model or endpoint:

```powershell
$env:OLLAMA_MODEL = "qwen2.5:7b"
$env:OLLAMA_URL = "http://127.0.0.1:11434"
$env:KYA_BANK_URL = "http://127.0.0.1:8000"
```

The generated session is scored only after event collection completes, preserving the
low-latency, no-network scoring path.

## Live session monitoring

The dashboard can now monitor an active mock-bank or Ollama session. The API endpoint
`GET /sessions/{session_id}/decision` returns the current events and a fresh decision
together. The dashboard polls it every two seconds while monitoring is enabled.

To monitor the live Ollama trace after running the agent:

1. Copy the printed `session_id` into the dashboard's **Live session monitor** field.
2. Select **Monitor session**.
3. Keep the agent or mock-bank client active; new events and scores appear on the timeline.

Polling pauses when the dashboard's timeline is paused and does not change the `/score` hot path.

## Consented human collection

The synthetic human rows are not real participants. Use the separate collector only after
written consent: see [generator/humans/README.md](D:/KYA-Shield/generator/humans/README.md).
Collected records remain in `data\human_sessions\` and support deletion by pseudonymous ID.
