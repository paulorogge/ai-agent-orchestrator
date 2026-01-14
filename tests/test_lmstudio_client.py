from __future__ import annotations

import importlib.util
import json
from typing import Any

from ai_agent_orchestrator.protocol.messages import Message
from task_runner_app.llm import LMStudioClient, PROTOCOL_REMINDER


def test_lmstudio_client_retries_on_protocol_violation() -> None:
    if importlib.util.find_spec("httpx") is None:
        import pytest

        pytest.skip("httpx not installed; lmstudio extra not enabled")

    import httpx

    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if len(requests) == 1:
            payload: dict[str, Any] = {
                "choices": [{"message": {"content": "not json"}}]
            }
        else:
            payload = {
                "choices": [
                    {"message": {"content": '{"type":"final","content":"ok"}'}}
                ]
            }
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, base_url="http://testserver")

    llm = LMStudioClient(base_url="http://testserver", model="test-model", client=client)
    response = llm.generate([Message(role="user", content="Hello")])

    assert response == '{"type":"final","content":"ok"}'
    assert len(requests) == 2

    retry_body = json.loads(requests[1].content)
    messages = retry_body["messages"]
    assert messages[-1]["role"] == "system"
    assert PROTOCOL_REMINDER in messages[-1]["content"]
