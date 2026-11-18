from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from kya.scoring_api import score_session
from kya.security import ApiKeyGuard, AuditLogger, TrustedKeyRegistry, mandate_key_id
from kya.shadow import apply_shadow_mode
from generator.mandate_issuer import demo_private_key

from .store import BankStore

app = FastAPI(title="KYA-Shield Mock Bank", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
store = BankStore()
api_key_guard = ApiKeyGuard()
audit_logger = AuditLogger()
key_registry = TrustedKeyRegistry()
key_registry.register("principal:cust-001", demo_private_key().public_key())


def _session_id(header_value: str | None) -> str:
    if not header_value:
        raise HTTPException(status_code=400, detail="X-Session-ID header is required")
    return header_value


def _context(headers: dict[str, str] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    headers = headers or {}
    user_agent = headers.get("user-agent", "KYA-Shield-local-client")
    is_ollama_agent = "kya-ollama-agent" in user_agent.lower()
    return (
        {
            "user_agent": user_agent,
            "platform": "Windows",
            "screen_w": 1920,
            "screen_h": 1080,
            "webdriver": is_ollama_agent,
            "headless_hint": is_ollama_agent,
            "ip_hash": "local-demo",
        },
        {
            "client_type": "agent" if is_ollama_agent else "browser",
            **({"framework_hint": "toolcall_ollama"} if is_ollama_agent else {}),
        },
    )


def _event(
    session_id: str,
    event_type: str,
    *,
    headers: dict[str, str] | None = None,
    **fields: Any,
) -> dict[str, Any]:
    device, client = _context(headers)
    event = {
        "session_id": session_id,
        "ts_ms": int(time.time() * 1000),
        "event_type": event_type,
        "device": device,
        "client": client,
        **fields,
    }
    store.add_event(session_id, event)
    return event


class LoginRequest(BaseModel):
    principal_id: str


class PayeeRequest(BaseModel):
    principal_id: str
    payee: str = Field(min_length=1, max_length=120)


class PaymentRequest(BaseModel):
    principal_id: str
    amount: float = Field(gt=0)
    payee: str = Field(min_length=1, max_length=120)
    merchant_category: str = Field(min_length=1, max_length=80)
    mandate: dict[str, Any] | None = None


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return (Path(__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


@app.post("/events")
def client_event(
    payload: dict[str, Any],
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    session_id = _session_id(x_session_id)
    allowed = {
        "page",
        "target",
        "x",
        "y",
        "dwell_ms",
        "key_interval_ms",
        "content_origin",
        "referrer",
    }
    event_type = payload.get("event_type")
    if event_type not in {"page_view", "click", "keystroke", "form_submit"}:
        raise HTTPException(status_code=400, detail="unsupported client event_type")
    fields = {key: value for key, value in payload.items() if key in allowed}
    headers = {"user-agent": user_agent} if user_agent else None
    return _event(session_id, event_type, headers=headers, **fields)


@app.post("/login")
def login(
    request: LoginRequest,
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    session_id = _session_id(x_session_id)
    if request.principal_id not in store.principals:
        raise HTTPException(status_code=404, detail="unknown principal")
    headers = {"user-agent": user_agent} if user_agent else None
    _event(session_id, "api_call", headers=headers, api_endpoint="/login", http_method="POST")
    return {"session_id": session_id, "principal_id": request.principal_id}


@app.get("/balance/{principal_id}")
def balance(
    principal_id: str,
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    session_id = _session_id(x_session_id)
    principal = store.principals.get(principal_id)
    if principal is None:
        raise HTTPException(status_code=404, detail="unknown principal")
    headers = {"user-agent": user_agent} if user_agent else None
    _event(session_id, "api_call", headers=headers, api_endpoint="/balance", http_method="GET")
    return {"principal_id": principal_id, "balance": principal.balance}


@app.post("/payees")
def add_payee(
    request: PayeeRequest,
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    session_id = _session_id(x_session_id)
    if request.principal_id not in store.principals:
        raise HTTPException(status_code=404, detail="unknown principal")
    is_new = store.add_payee(request.principal_id, request.payee)
    headers = {"user-agent": user_agent} if user_agent else None
    _event(session_id, "api_call", headers=headers, api_endpoint="/payees", http_method="POST")
    return {"payee": request.payee, "new_payee": is_new}


def _payment(
    request: PaymentRequest,
    session_id: str,
    endpoint: str,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    if request.principal_id not in store.principals:
        raise HTTPException(status_code=404, detail="unknown principal")
    _event(session_id, "api_call", headers=headers, api_endpoint=endpoint, http_method="POST")
    try:
        new_payee = store.transact(
            request.principal_id,
            request.amount,
            request.payee,
            request.merchant_category,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    event = _event(
        session_id,
        "transaction",
        headers=headers,
        amount=request.amount,
        payee=request.payee,
        new_payee=new_payee,
        merchant_category=request.merchant_category,
        **({"mandate": request.mandate} if request.mandate is not None else {}),
    )
    return {"status": "accepted", "event": event}


@app.post("/transfer")
def transfer(
    request: PaymentRequest,
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    headers = {"user-agent": user_agent} if user_agent else None
    return _payment(request, _session_id(x_session_id), "/transfer", headers)


@app.post("/merchant-payment")
def merchant_payment(
    request: PaymentRequest,
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    headers = {"user-agent": user_agent} if user_agent else None
    return _payment(request, _session_id(x_session_id), "/merchant-payment", headers)


@app.get("/external-content")
def external_content(
    x_session_id: str | None = Header(default=None),
    user_agent: str | None = Header(default=None),
) -> dict[str, str]:
    session_id = _session_id(x_session_id)
    headers = {"user-agent": user_agent} if user_agent else None
    _event(
        session_id,
        "page_view",
        headers=headers,
        page="external_product",
        content_origin="external",
        referrer="mock-external-content",
    )
    return {
        "page": "external_product",
        "content_origin": "external",
        "message": "Synthetic external content for local defensive testing.",
    }


@app.get("/sessions/{session_id}/events")
def session_events(session_id: str) -> list[dict[str, Any]]:
    return store.events_for(session_id)


@app.get("/sessions/{session_id}/decision")
def session_decision(session_id: str) -> dict[str, Any]:
    events = store.events_for(session_id)
    if not events:
        raise HTTPException(status_code=404, detail="session has no events")
    try:
        return {"events": events, "decision": apply_shadow_mode(
            score_session(events, key_registry=key_registry)
        )}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/score")
def score(
    events: list[dict[str, Any]],
    x_api_key: str | None = Header(default=None),
) -> dict[str, Any]:
    if not api_key_guard.check(x_api_key):
        raise HTTPException(status_code=401, detail="invalid API key")
    try:
        result = apply_shadow_mode(score_session(events, key_registry=key_registry))
        audit_logger.record("score", {
            "session_id": result.get("session_id"),
            "action": result.get("action"),
            "recommended_action": result.get("recommended_action"),
            "agent_class": result.get("agent_class"),
            "trust_score": result.get("agent_trust_score"),
            "reason_codes": [reason["code"] for reason in result["reason_codes"]],
        })
        return result
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/demo/scenarios/{scenario}")
def demo_scenario(scenario: str) -> list[dict[str, Any]]:
    files = {
        "human": "sample_session_human.json",
        "legitimate-agent": "sample_session_legit_agent.json",
        "prompt-injected-agent": "sample_session_hijacked_agent.json",
    }
    filename = files.get(scenario)
    if filename is None:
        raise HTTPException(status_code=404, detail="unknown demo scenario")
    path = Path(__file__).parents[1] / "examples" / filename
    try:
        import json

        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise HTTPException(status_code=500, detail="demo scenario unavailable") from exc
