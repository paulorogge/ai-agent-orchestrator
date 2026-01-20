from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import time
from typing import Any, AsyncIterator, Protocol, cast

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

    class _AsyncByteStream(Protocol):
        def __aiter__(self) -> AsyncIterator[bytes]: ...

        async def aclose(self) -> None: ...

    class DelayedByteStream(_AsyncByteStream):
        def __init__(self, chunks: list[bytes], delay: float) -> None:
            self._chunks = chunks
            self._delay = delay

        async def __aiter__(self) -> AsyncIterator[bytes]:
            for chunk in self._chunks:
                await asyncio.sleep(self._delay)
                yield chunk

        async def aclose(self) -> None:
            return None

    sse_chunks = [
        b"data: "
        b'{"choices":[{"delta":{"content":"{\\"type\\":\\"final\\",'
        b'\\"content\\":\\"Hello"}}]}\n'
        b"\n",
        b'data: {"choices":[{"delta":{"content":" world\\"}"}}]}\n'
        b"\n",
        b"data: [DONE]\n\n",
    ]

    requests: list[Any] = []

    def handler(request: Any) -> Any:
        requests.append(request)
        return httpx.Response(
            200,
            stream=DelayedByteStream(sse_chunks, delay=0.02),
        )

    transport = httpx.MockTransport(handler)
    sync_client = httpx.Client(transport=transport, base_url="http://testserver")

    async def collect() -> tuple[list[Any], list[float]]:
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as async_client:
            llm = LMStudioClient(
                base_url="http://testserver",
                model="test-model",
                client=sync_client,
                async_client=async_client,
            )
            chunks: list[Any] = []
            timestamps: list[float] = []
            async for chunk in llm.stream([Message(role="user", content="Hi")]):
                if chunk.content:
                    timestamps.append(time.perf_counter())
                chunks.append(chunk)
            return chunks, timestamps

    chunks, timestamps = asyncio.run(collect())

    assert [chunk.content for chunk in chunks[:-1]] == [
        '{"type":"final","content":"Hello',
        ' world"}',
    ]
    assert chunks[-1].is_final is True
    assert chunks[-1].content == ""
    assert len(timestamps) == 2
    assert timestamps[1] - timestamps[0] >= 0.01
    assert len(requests) == 1


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

    sse_retry_body = "\n".join(
        [
            'data: {"choices":[{"delta":{"content":"{\\"type\\":\\"final\\",'
            '\\"content\\":\\"ok\\"}"}}]}',
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
            if len(requests) == 1:
                return httpx.Response(200, content=sse_body)
            return httpx.Response(200, content=sse_retry_body)
        raise AssertionError("Expected streaming request payloads.")

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

    assert [chunk.content for chunk in chunks[:-1]] == [
        "oi tudo bem",
        '{"type":"final","content":"ok"}',
    ]
    assert chunks[-1].is_final is True
    assert chunks[-1].content == ""
    assert len(requests) == 2

    retry_body = json.loads(requests[1].content)
    messages = retry_body["messages"]
    assert messages[-1]["role"] == "system"
    assert PROTOCOL_REMINDER in messages[-1]["content"]
