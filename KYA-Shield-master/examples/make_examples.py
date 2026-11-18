"""Generate and validate KYA-Shield example artefacts.

Run from the pack root:  python3 examples/make_examples.py

What it does
1. Creates an Ed25519 DEMO key pair and an Ed25519-signed mandate (docs/07_MANDATE_SPEC.md).
2. Writes three example sessions: human, legitimate agent in scope, prompt-injected agent.
3. Verifies the mandate signature and scope for every transaction.
4. Validates events, mandate and the illustrative decision against the JSON schemas.
5. Computes the minimum-expected-cost action from config/cost_matrix.json.

The decision file is ILLUSTRATIVE (p_fraud is hand-set to show the policy maths), not model output.
"""
import base64
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from generator.mandate_issuer import demo_private_key
OUT = ROOT / "examples"
SEED = 7
random.seed(SEED)

BASE_TS = 1_794_000_000_000  # ms, early Nov 2026 (arbitrary fixed value for reproducibility)


# ---------- mandate signing / verification ----------
def canonical(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_mandate(fields: dict, key: Ed25519PrivateKey) -> dict:
    sig = key.sign(canonical(fields))
    return {**fields, "signature": base64.b64encode(sig).decode()}


def verify_mandate(mandate: dict, public_key) -> list:
    """Return a list of violation codes for the mandate itself (empty = valid)."""
    body = {k: v for k, v in mandate.items() if k != "signature"}
    try:
        public_key.verify(base64.b64decode(mandate["signature"]), canonical(body))
    except (InvalidSignature, Exception):
        return ["R100"]
    return []


def check_scope(mandate: dict, txn: dict, now_ms: int, spent_so_far: float, txns_today: int) -> list:
    v = []
    now = datetime.fromtimestamp(now_ms / 1000, tz=timezone.utc)
    if not (datetime.fromisoformat(mandate["issued_at"]) <= now <= datetime.fromisoformat(mandate["expires_at"])):
        v.append("R103")
    if txn["amount"] > mandate["max_amount_per_txn"]:
        v.append("R102")
    if spent_so_far + txn["amount"] > mandate["max_total_amount"]:
        v.append("R107")
    if txn["merchant_category"] not in mandate["allowed_merchant_categories"]:
        v.append("R106")
    if mandate.get("allowed_payees") and txn["payee"] not in mandate["allowed_payees"]:
        v.append("R101")
    if txns_today >= mandate["max_txns_per_day"]:
        v.append("R108")
    return v


# ---------- session builders ----------
def device(webdriver=False, ua="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0"):
    return {"user_agent": ua, "platform": "Win32", "screen_w": 1920, "screen_h": 1080,
            "webdriver": webdriver, "headless_hint": webdriver, "ip_hash": "demo-salted-hash"}


def human_session(sid):
    t = BASE_TS
    ev = []

    def add(gap, **kw):
        nonlocal t
        t += gap
        ev.append({"session_id": sid, "ts_ms": t, "device": device(),
                   "client": {"client_type": "browser"}, **kw})

    add(0, event_type="page_view", page="login", dwell_ms=0)
    for _ in range(8):
        add(random.randint(90, 420), event_type="keystroke", target="username", key_interval_ms=random.randint(80, 380))
    add(random.randint(600, 1800), event_type="click", target="login_btn", x=842, y=511)
    add(random.randint(900, 2500), event_type="page_view", page="balance", dwell_ms=random.randint(1500, 4000))
    add(random.randint(2500, 6000), event_type="click", target="pay_merchant", x=610, y=388)
    add(random.randint(1200, 3000), event_type="form_submit", target="merchant_payment")
    add(random.randint(300, 900), event_type="transaction", amount=1180.0, payee="FRESHMART",
        new_payee=False, merchant_category="grocery")
    return ev


def make_mandate(key, principal, agent):
    issued = datetime.fromtimestamp(BASE_TS / 1000 - 3600, tz=timezone.utc)
    fields = {
        "mandate_id": "m-demo-0001",
        "principal_id": principal,
        "agent_id": agent,
        "agent_provenance": {"framework": "demo-browser-agent", "registered_at": issued.isoformat()},
        "task_description": "Weekly groceries under INR 3,000",
        "allowed_merchant_categories": ["grocery"],
        "allowed_payees": ["FRESHMART", "DAILYBASKET"],
        "max_amount_per_txn": 3000.0,
        "max_total_amount": 3000.0,
        "max_txns_per_day": 3,
        "issued_at": issued.isoformat(),
        "expires_at": (issued + timedelta(days=7)).isoformat(),
        "nonce": "nonce-demo-0001",
        "key_id": "principal:cust-001",
    }
    return sign_mandate(fields, key)


def agent_session(sid, mandate, hijacked):
    t = BASE_TS + 10_000
    ev = []
    agent = mandate["agent_id"]

    def add(gap, **kw):
        nonlocal t
        t += gap
        ev.append({"session_id": sid, "ts_ms": t, "device": device(webdriver=True, ua="HeadlessChrome/126.0"),
                   "client": {"client_type": "browser", "framework_hint": "demo-browser-agent", "agent_id": agent}, **kw})

    add(0, event_type="api_call", api_endpoint="/auth/token", http_method="POST")
    add(900, event_type="page_view", page="catalog", dwell_ms=300)
    # external product page (injection surface)
    add(2400, event_type="page_view", page="product_page", content_origin="external", dwell_ms=2400)
    if not hijacked:
        add(3100, event_type="api_call", api_endpoint="/cart/add", http_method="POST")
        add(1800, event_type="form_submit", target="merchant_payment")
        add(500, event_type="transaction", amount=2450.0, payee="FRESHMART", new_payee=False,
            merchant_category="grocery", mandate=mandate)
    else:
        # injected instruction makes the agent add a new payee seconds after external content load
        add(4200, event_type="api_call", api_endpoint="/payees/add", http_method="POST")
        add(1100, event_type="form_submit", target="add_payee")
        add(600, event_type="transaction", amount=2990.0, payee="ACME-9921", new_payee=True,
            merchant_category="grocery", mandate=mandate)
    return ev


# ---------- main ----------
def main():
    key = demo_private_key()  # DEMO key only: never reuse in anything real
    pub = key.public_key()
    mandate = make_mandate(key, principal="cust-001", agent="agent-demo-01")
    assert verify_mandate(mandate, pub) == [], "mandate must verify"

    sessions = {
        "sample_session_human.json": human_session("s-human-001"),
        "sample_session_legit_agent.json": agent_session("s-agent-legit-001", mandate, hijacked=False),
        "sample_session_hijacked_agent.json": agent_session("s-agent-hijack-001", mandate, hijacked=True),
    }

    schemas = {n: json.loads((ROOT / "schemas" / n).read_text())
               for n in ("event_schema.json", "decision_schema.json", "mandate_schema.json")}
    ev_val = Draft202012Validator(schemas["event_schema.json"])
    man_val = Draft202012Validator(schemas["mandate_schema.json"])

    man_val.validate(mandate)
    (OUT / "sample_mandate.json").write_text(json.dumps(mandate, indent=2))

    for name, events in sessions.items():
        ev_val.validate(events)
        (OUT / name).write_text(json.dumps(events, indent=2))
        print(f"valid: {name} ({len(events)} events)")

    # scope check demo
    print("\nScope checks (mandate verification is done by the bank, not the agent):")
    for name in ("sample_session_legit_agent.json", "sample_session_hijacked_agent.json"):
        for e in sessions[name]:
            if e["event_type"] == "transaction":
                viol = check_scope(mandate, e, e["ts_ms"], spent_so_far=0.0, txns_today=0)
                print(f"  {name}: payee={e['payee']} amount={e['amount']} -> violations={viol or 'none'}")

    # tamper test: widening the cap must break the signature
    tampered = {**mandate, "max_amount_per_txn": 50000.0}
    assert verify_mandate(tampered, pub) == ["R100"], "tampered mandate must fail"
    print("\ntamper test: widened cap -> R100 (signature invalid), as expected")

    # cost-based policy on the hijacked transaction (p_fraud is ILLUSTRATIVE)
    cm = json.loads((ROOT / "config" / "cost_matrix.json").read_text())
    txn = [e for e in sessions["sample_session_hijacked_agent.json"] if e["event_type"] == "transaction"][0]
    p_fraud = 0.92

    def exp_cost(action):
        return (1 - p_fraud) * cm["legitimate_cost"][action] + p_fraud * cm["fraud_loss_fraction_of_amount"][action] * txn["amount"]

    costs = {a: round(exp_cost(a), 2) for a in cm["actions"]}
    action = min(costs, key=costs.get)
    print(f"\nexpected cost by action (p_fraud={p_fraud}, amount={txn['amount']}): {costs} -> {action}")

    decision = {
        "_illustrative": True,
        "session_id": "s-agent-hijack-001",
        "agent_class": "llm_agent",
        "agent_class_probs": {"human": 0.02, "scripted_bot": 0.07, "llm_agent": 0.91},
        "agent_trust_score": 8,
        "p_fraud": p_fraud,
        "action": action,
        "expected_cost_by_action": costs,
        "reason_codes": [
            {"code": "R101", "text": "Payee 'ACME-9921' is not in the mandate's allowed payees.", "weight": 0.52},
            {"code": "R201", "text": "A new payee was added 4.2 s after external page content was loaded.", "weight": 0.31},
            {"code": "R300", "text": "Amount is at 99.7% of the mandate cap and unusual for this customer.", "weight": 0.11},
        ],
        "latency_ms": 41.7,
    }
    Draft202012Validator(schemas["decision_schema.json"]).validate(decision)
    (OUT / "sample_decision_hijacked_agent.json").write_text(json.dumps(decision, indent=2))
    print("valid: sample_decision_hijacked_agent.json")


if __name__ == "__main__":
    main()
