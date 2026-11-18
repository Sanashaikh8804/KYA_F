from __future__ import annotations

import json
from pathlib import Path

from ollama_agent.runner import OllamaAgentRunner, OllamaConfig, SessionTrace


def test_tool_schemas_and_trace_are_serializable(tmp_path: Path) -> None:
    trace = SessionTrace("ollama-test", "check balance", "test-model", 1)
    trace.records.append({
        "record_type": "tool_call",
        "tool": "get_balance",
        "arguments": {"principal_id": "cust-001"},
    })
    path = tmp_path / "trace.jsonl"
    trace.write_jsonl(path)
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert lines[-1]["record_type"] == "session_summary"
    assert lines[-1]["event_count"] == 0


def test_bank_tool_mapping_uses_session_header() -> None:
    calls = []

    def opener(request, timeout):
        calls.append((request.method, request.full_url, request.get_header("X-session-id")))
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return None
            def read(self): return b'{"ok": true}'
        return Response()

    runner = OllamaAgentRunner(OllamaConfig(), opener=opener)
    assert runner._invoke_tool("session-1", "login", {"principal_id": "cust-001"}) == {"ok": True}
    assert calls == [("POST", "http://127.0.0.1:8000/login", "session-1")]
