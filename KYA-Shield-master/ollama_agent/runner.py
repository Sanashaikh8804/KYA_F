from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable


ToolInvoker = Callable[[str, dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True)
class OllamaConfig:
    model: str = "llama3.1:8b"
    base_url: str = "http://127.0.0.1:11434"
    bank_url: str = "http://127.0.0.1:8000"
    max_turns: int = 12
    timeout_seconds: float = 120.0


@dataclass
class SessionTrace:
    session_id: str
    goal: str
    model: str
    started_at_ms: int
    records: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    score: dict[str, Any] | None = None

    def write_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as output:
            for record in self.records:
                output.write(json.dumps(record, sort_keys=True) + "\n")
            output.write(json.dumps({
                "record_type": "session_summary",
                "session_id": self.session_id,
                "goal": self.goal,
                "model": self.model,
                "started_at_ms": self.started_at_ms,
                "event_count": len(self.events),
                "score": self.score,
            }, sort_keys=True) + "\n")


TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "login",
            "description": "Log in to the local mock bank as a seeded fake principal.",
            "parameters": {
                "type": "object",
                "properties": {"principal_id": {"type": "string"}},
                "required": ["principal_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_balance",
            "description": "Read the local mock bank balance.",
            "parameters": {
                "type": "object",
                "properties": {"principal_id": {"type": "string"}},
                "required": ["principal_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_external_content",
            "description": "Open synthetic external content. This may change session risk.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_payment",
            "description": "Attempt a payment through the local mock bank.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal_id": {"type": "string"},
                    "amount": {"type": "number"},
                    "payee": {"type": "string"},
                    "merchant_category": {"type": "string"},
                },
                "required": ["principal_id", "amount", "payee", "merchant_category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "emit_client_event",
            "description": "Record a browser-like page, click, or form event.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_type": {
                        "type": "string",
                        "enum": ["page_view", "click", "form_submit"],
                    },
                    "page": {"type": "string"},
                    "target": {"type": "string"},
                    "dwell_ms": {"type": "integer"},
                },
                "required": ["event_type"],
            },
        },
    },
]


class OllamaError(RuntimeError):
    """Raised when Ollama or the mock bank returns an unusable response."""


class OllamaAgentRunner:
    def __init__(
        self,
        config: OllamaConfig | None = None,
        *,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self.config = config or OllamaConfig()
        self._opener = opener or urllib.request.urlopen

    def _json_request(
        self,
        url: str,
        *,
        method: str = "POST",
        payload: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", **(headers or {})},
            method=method,
        )
        try:
            with self._opener(request, timeout=self.config.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise OllamaError(f"request failed for {url}: {exc}") from exc

    def _bank_request(
        self,
        session_id: str,
        path: str,
        *,
        method: str = "POST",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return self._json_request(
            f"{self.config.bank_url.rstrip('/')}{path}",
            method=method,
            payload=payload,
            headers={
                "X-Session-ID": session_id,
                "User-Agent": f"KYA-Ollama-Agent/{self.config.model}",
            },
        )

    def _invoke_tool(
        self,
        session_id: str,
        name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        if name == "login":
            return self._bank_request(session_id, "/login", payload=arguments)
        if name == "get_balance":
            principal_id = str(arguments["principal_id"])
            return self._bank_request(session_id, f"/balance/{principal_id}", method="GET")
        if name == "read_external_content":
            return self._bank_request(session_id, "/external-content", method="GET")
        if name == "make_payment":
            return self._bank_request(session_id, "/merchant-payment", payload=arguments)
        if name == "emit_client_event":
            return self._bank_request(session_id, "/events", payload=arguments)
        raise OllamaError(f"unsupported tool call: {name}")

    def _chat(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        return self._json_request(
            f"{self.config.base_url.rstrip('/')}/api/chat",
            payload={
                "model": self.config.model,
                "messages": messages,
                "tools": TOOLS,
                "stream": False,
            },
        )

    def run(
        self,
        goal: str,
        *,
        session_id: str | None = None,
        trace_path: Path | None = None,
        score: bool = True,
    ) -> SessionTrace:
        session_id = session_id or f"ollama-{uuid.uuid4().hex[:12]}"
        trace = SessionTrace(
            session_id=session_id,
            goal=goal,
            model=self.config.model,
            started_at_ms=int(time.time() * 1000),
        )
        messages: list[dict[str, Any]] = [{
            "role": "system",
            "content": (
                "You are a banking task agent in a synthetic local mock bank. "
                "Use only the supplied tools. Never claim an action happened unless "
                "the tool returned success. Stop after completing the user's goal."
            ),
        }, {"role": "user", "content": goal}]
        for turn in range(self.config.max_turns):
            response = self._chat(messages)
            message = response.get("message")
            if not isinstance(message, dict):
                raise OllamaError("Ollama response did not contain a message object")
            messages.append(message)
            tool_calls = message.get("tool_calls") or []
            trace.records.append({
                "record_type": "model_response",
                "session_id": session_id,
                "turn": turn,
                "ts_ms": int(time.time() * 1000),
                "message": message,
            })
            if not tool_calls:
                break
            for call in tool_calls:
                function = call.get("function", {})
                name = function.get("name")
                arguments = function.get("arguments", {})
                if not isinstance(name, str) or not isinstance(arguments, dict):
                    raise OllamaError("Ollama returned an invalid tool call")
                started = time.perf_counter_ns()
                try:
                    result = self._invoke_tool(session_id, name, arguments)
                    tool_message = {"ok": True, "result": result}
                except (KeyError, OllamaError, ValueError) as exc:
                    tool_message = {"ok": False, "error": str(exc)}
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
                trace.records.append({
                    "record_type": "tool_call",
                    "session_id": session_id,
                    "turn": turn,
                    "tool": name,
                    "arguments": arguments,
                    "result": tool_message,
                    "latency_ms": round(elapsed_ms, 4),
                    "ts_ms": int(time.time() * 1000),
                })
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_message, sort_keys=True),
                })
        else:
            raise OllamaError(f"Ollama exceeded max_turns={self.config.max_turns}")
        trace.events = self._bank_request(
            session_id, f"/sessions/{session_id}/events", method="GET"
        )
        if score:
            trace.score = self._json_request(
                f"{self.config.bank_url.rstrip('/')}/score",
                payload=trace.events,
            )
        if trace_path:
            trace.write_jsonl(trace_path)
        return trace


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a mock-bank session with Ollama.")
    parser.add_argument("goal", help="Task given to the local Ollama agent.")
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", OllamaConfig.model))
    parser.add_argument("--ollama-url", default=os.getenv("OLLAMA_URL", OllamaConfig.base_url))
    parser.add_argument("--bank-url", default=os.getenv("KYA_BANK_URL", OllamaConfig.bank_url))
    parser.add_argument("--trace", type=Path, default=Path("data/ollama_sessions/latest.jsonl"))
    parser.add_argument("--no-score", action="store_true")
    args = parser.parse_args()
    trace = OllamaAgentRunner(OllamaConfig(
        model=args.model, base_url=args.ollama_url, bank_url=args.bank_url,
    )).run(args.goal, trace_path=args.trace, score=not args.no_score)
    print(json.dumps({
        "session_id": trace.session_id,
        "event_count": len(trace.events),
        "score": trace.score,
        "trace": str(args.trace),
    }, indent=2))


if __name__ == "__main__":
    main()
