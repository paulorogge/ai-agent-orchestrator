import asyncio

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import LLMStreamChunk
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput
from ai_agent_orchestrator.tools.registry import ToolRegistry


class FakeStreamingLLM:
    def __init__(self, output: str, chunks: list[str]) -> None:
        self._output = output
        self._chunks = chunks

    def generate(self, conversation: list[object]) -> str:
        return self._output

    async def stream(self, conversation: list[object]):
        for chunk in self._chunks:
            yield LLMStreamChunk(content=chunk)


def test_agent_streaming_matches_non_streaming() -> None:
    output = FinalOutput(type="final", content="Hello").model_dump_json()
    chunks = [output[:10], output[10:]]

    llm = FakeStreamingLLM(output, chunks)
    tools = ToolRegistry()
    memory = InMemoryMemory()
    agent = Agent(llm=llm, tools=tools, memory=memory)

    async def collect() -> tuple[str, str | None, int]:
        streamed_text = ""
        final_text = None
        final_count = 0
        async for chunk in agent.stream_async("Hi"):
            if chunk.is_final:
                final_text = chunk.text
                final_count += 1
            else:
                streamed_text += chunk.text
        return streamed_text, final_text, final_count

    streamed_text, final_text, final_count = asyncio.run(collect())

    assert streamed_text == output
    assert final_text == "Hello"
    assert final_count == 1

    llm_sync = FakeStreamingLLM(output, chunks)
    agent_sync = Agent(llm=llm_sync, tools=tools, memory=InMemoryMemory())
    response = asyncio.run(agent_sync.run_async("Hi"))

    assert response.content == "Hello"
