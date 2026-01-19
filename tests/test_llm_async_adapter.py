import asyncio

from ai_agent_orchestrator.llm import FakeLLM, async_generate_via_thread
from ai_agent_orchestrator.protocol.messages import Message


def test_async_generate_via_thread_matches_sync_output() -> None:
    expected = '{"type":"final","content":"ok"}'
    llm = FakeLLM([expected])
    conversation = [Message(role="user", content="hi")]

    result = asyncio.run(async_generate_via_thread(llm, conversation))

    assert result == expected
