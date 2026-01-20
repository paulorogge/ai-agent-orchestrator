from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
from typing import Any, cast

from ai_agent_orchestrator.protocol.messages import Message
from task_runner_app.llm import PROTOCOL_REMINDER, LMStudioClient


def test_lmstudio_client_retries_on_protocol_violation() -> None:
    if importlib.util.find_spec("httpx") is None:
        import pytest

        pytest.skip("httpx not installed; lmstudio extra not enabled")

    httpx = cast(Any, importlib.import_module("httpx"))

    requests: list[Any] = []

    def handler(request: Any) -> Any:
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


def test_lmstudio_client_streams_sse_chunks() -> None:
    if importlib.util.find_spec("httpx") is None:
        import pytest

        pytest.skip("httpx not installed; lmstudio extra not enabled")

    httpx = cast(Any, importlib.import_module("httpx"))

    sse_body = "\n".join(
        [
            'data: {"choices":[{"delta":{"content":"Hello"}}]}',
            "",
            'data: {"choices":[{"delta":{"content":" world"}}]}',
            "",
            "data: [DONE]",
            "",
        ]
    )

    def handler(request: Any) -> Any:
        return httpx.Response(200, content=sse_body)

    transport = httpx.MockTransport(handler)
    sync_client = httpx.Client(transport=transport, base_url="http://testserver")

    async def collect() -> list[Any]:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            llm = LMStudioClient(
                base_url="http://testserver",
                model="test-model",
                client=sync_client,
                async_client=async_client,
            )
            return [chunk async for chunk in llm.stream([Message(role="user", content="Hi")])]

    chunks = asyncio.run(collect())

    assert [chunk.content for chunk in chunks[:-1]] == ["Hello", " world"]
    assert chunks[-1].is_final is True
    assert chunks[-1].content == ""


def test_lmstudio_client_stream_retries_on_protocol_violation() -> None:
    if importlib.util.find_spec("httpx") is None:
        import pytest

        pytest.skip("httpx not installed; lmstudio extra not enabled")

    httpx = cast(Any, importlib.import_module("httpx"))

    sse_body = "\n".join(
        [
            'data: {"choices":[{"delta":{"content":"oi tudo bem"}}]}',
            "",
            "data: [DONE]",
            "",
        ]
    )

    requests: list[Any] = []

    def handler(request: Any) -> Any:
        requests.append(request)
        payload = json.loads(request.content)
        if payload.get("stream"):
            return httpx.Response(200, content=sse_body)
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"type":"final","content":"ok"}'}}]},
        )

    transport = httpx.MockTransport(handler)
    sync_client = httpx.Client(transport=transport, base_url="http://testserver")

    async def collect() -> list[Any]:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            llm = LMStudioClient(
                base_url="http://testserver",
                model="test-model",
                client=sync_client,
                async_client=async_client,
            )
            return [chunk async for chunk in llm.stream([Message(role="user", content="Hi")])]

    chunks = asyncio.run(collect())

    assert [chunk.content for chunk in chunks[:-1]] == ["oi tudo bem"]
    assert chunks[-1].is_final is True
    assert chunks[-1].content == '{"type":"final","content":"ok"}'
    assert len(requests) == 2

    retry_body = json.loads(requests[1].content)
    messages = retry_body["messages"]
    assert messages[-1]["role"] == "system"
    assert PROTOCOL_REMINDER in messages[-1]["content"]
