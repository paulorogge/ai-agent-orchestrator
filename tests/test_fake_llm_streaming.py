import asyncio

import pytest

from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.protocol.messages import Message


def test_fake_llm_streaming_chunk_order_and_buffer() -> None:
    output = "Hello from FakeLLM"
    chunk_size = 5
    expected_chunks = [
        output[i : i + chunk_size] for i in range(0, len(output), chunk_size)
    ]
    llm = FakeLLM([output], chunk_size=chunk_size)

    async def collect() -> tuple[list[str], list[bool]]:
        chunks: list[str] = []
        finals: list[bool] = []
        async for chunk in llm.stream([Message(role="user", content="Hi")]):
            chunks.append(chunk.content)
            finals.append(chunk.is_final)
        return chunks, finals

    chunks, finals = asyncio.run(collect())

    assert chunks == expected_chunks
    assert "".join(chunks) == output
    assert finals[-1] is True
    assert all(not flag for flag in finals[:-1])


def test_fake_llm_streaming_invalid_chunk_size_does_not_consume() -> None:
    llm = FakeLLM(["A", "B"], chunk_size=0)
    conversation = [Message(role="user", content="Hi")]

    async def consume() -> None:
        async for _ in llm.stream(conversation):
            pass

    with pytest.raises(ValueError, match="chunk_size must be a positive integer or None"):
        asyncio.run(consume())

    llm._chunk_size = None

    async def first_chunk() -> str:
        async for chunk in llm.stream(conversation):
            return chunk.content
        return ""

    assert asyncio.run(first_chunk()) == "A"
