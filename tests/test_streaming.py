import asyncio
from collections.abc import AsyncIterator, Sequence

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import LLMStreamChunk
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.observability.events import ListEventSink
from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.base import Tool, ToolInput
from ai_agent_orchestrator.tools.registry import ToolRegistry


class FakeStreamingLLM:
    def __init__(self, output: str, chunks: list[str]) -> None:
        self._output = output
        self._chunks = chunks

    def generate(self, conversation: Sequence[Message]) -> str:
        return self._output

    async def stream(
        self, conversation: Sequence[Message]
    ) -> AsyncIterator[LLMStreamChunk]:
        for chunk in self._chunks:
            yield LLMStreamChunk(content=chunk)


class EchoToolInput(ToolInput):
    text: str


class EchoTool(Tool[EchoToolInput]):
    name = "echo.tool"
    description = "Echoes the input."
    input_model = EchoToolInput

    def __init__(self) -> None:
        self.calls: list[str] = []

    def run(self, validated_input: EchoToolInput) -> str:
        self.calls.append(validated_input.text)
        return validated_input.text


def test_agent_streaming_matches_non_streaming() -> None:
    output = FinalOutput(type="final", content="Hello").model_dump_json()
    chunks = [output[:10], output[10:]]

    llm = FakeStreamingLLM(output, chunks)
    tools = ToolRegistry()
    memory = InMemoryMemory()
    agent = Agent(llm=llm, tools=tools, memory=memory)

    async def collect() -> tuple[str, list[str], int]:
        streamed_text = ""
        chunks_seen: list[str] = []
        final_count = 0
        async for chunk in agent.stream_async("Hi"):
            streamed_text += chunk.text
            chunks_seen.append(chunk.text)
            if chunk.is_final:
                final_count += 1
        return streamed_text, chunks_seen, final_count

    streamed_text, chunks_seen, final_count = asyncio.run(collect())

    assert streamed_text == "Hello"
    assert "".join(chunks_seen) == "Hello"
    assert final_count == 1

    llm_sync = FakeStreamingLLM(output, chunks)
    agent_sync = Agent(llm=llm_sync, tools=tools, memory=InMemoryMemory())
    response = asyncio.run(agent_sync.run_async("Hi"))

    assert response.content == streamed_text


def test_streamed_chunks_reconstruct_final_output() -> None:
    output = FinalOutput(type="final", content="Streamed response").model_dump_json()
    chunks = [output[:12], output[12:24], output[24:]]

    llm = FakeStreamingLLM(output, chunks)
    agent = Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory())

    async def collect() -> tuple[str, int]:
        streamed_text = ""
        final_count = 0
        async for chunk in agent.stream_async("Hi"):
            streamed_text += chunk.text
            if chunk.is_final:
                final_count += 1
        return streamed_text, final_count

    streamed_text, final_count = asyncio.run(collect())

    llm_sync = FakeStreamingLLM(output, chunks)
    agent_sync = Agent(
        llm=llm_sync, tools=ToolRegistry(), memory=InMemoryMemory()
    )
    final_text = asyncio.run(agent_sync.run_async("Hi")).content

    assert streamed_text == "Streamed response"
    assert streamed_text == final_text
    assert final_count == 1


def test_streaming_plain_text_fallbacks_to_final_plain() -> None:
    output = "olá mundo"
    chunks = ["olá", " mundo"]

    llm = FakeStreamingLLM(output, chunks)
    tools = ToolRegistry()
    memory = InMemoryMemory()
    agent = Agent(llm=llm, tools=tools, memory=memory)

    async def collect() -> tuple[str, int]:
        streamed_text = ""
        final_count = 0
        async for chunk in agent.stream_async("Oi"):
            streamed_text += chunk.text
            if chunk.is_final:
                final_count += 1
        return streamed_text, final_count

    streamed_text, final_count = asyncio.run(collect())

    assert streamed_text == output
    assert final_count == 1

    llm_sync = FakeStreamingLLM(output, chunks)
    agent_sync = Agent(llm=llm_sync, tools=tools, memory=InMemoryMemory())
    response = asyncio.run(agent_sync.run_async("Oi"))

    assert response.content == streamed_text


def test_streaming_tool_call_executes_after_full_buffer() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="echo.tool",
        args={"text": "ok"},
    ).model_dump_json()
    chunks = [tool_call[:20], tool_call[20:]]

    llm = FakeStreamingLLM(tool_call, chunks)
    tools = ToolRegistry()
    echo_tool = EchoTool()
    tools.register(echo_tool)
    memory = InMemoryMemory()
    sink = ListEventSink()
    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=1)

    async def consume() -> tuple[str, int]:
        streamed_text = ""
        final_count = 0
        async for chunk in agent.stream_async("Hi", event_sink=sink):
            streamed_text += chunk.text
            if chunk.is_final:
                final_count += 1
        return streamed_text, final_count

    streamed, final_count = asyncio.run(consume())

    assert tool_call not in streamed
    assert streamed == "Max steps reached without final response."
    assert final_count == 1
    assert echo_tool.calls == ["ok"]
    names = [event.name for event in sink.events]
    assert "agent.tool.started" in names
    assert names.index("agent.model.responded") < names.index("agent.tool.started")

    llm_sync = FakeStreamingLLM(tool_call, chunks)
    tools_sync = ToolRegistry()
    tools_sync.register(EchoTool())
    agent_sync = Agent(
        llm=llm_sync, tools=tools_sync, memory=InMemoryMemory(), max_steps=1
    )
    response = asyncio.run(agent_sync.run_async("Hi"))
    assert response.content == streamed
