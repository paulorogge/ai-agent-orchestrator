import asyncio
import time

from ai_agent_orchestrator.agent import Agent, AgentEvent, AgentEventType
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.base import Tool, ToolInput
from ai_agent_orchestrator.tools.registry import ToolRegistry


class BlockingToolInput(ToolInput):
    pass


class BlockingTool(Tool[BlockingToolInput]):
    name = "blocking.tool"
    description = "Sleeps briefly to simulate blocking work."
    input_model = BlockingToolInput

    def run(self, validated_input: BlockingToolInput) -> str:
        time.sleep(0.2)
        return "slept"


def _build_agent() -> Agent:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="blocking.tool",
        args={},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()
    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(BlockingTool())
    memory = InMemoryMemory()
    return Agent(llm=llm, tools=tools, memory=memory, max_steps=2)


def test_run_async_completes_with_blocking_tool() -> None:
    agent = _build_agent()

    async def run_check() -> tuple[str, list[AgentEvent]]:
        response = await asyncio.wait_for(agent.run_async("Hi"), timeout=1.0)
        return response.content, response.events

    content, events = asyncio.run(run_check())

    assert content == "Done"
    assert any(event.type == AgentEventType.TOOL_RESULT for event in events)


def test_stream_async_completes_with_blocking_tool() -> None:
    agent = _build_agent()

    async def collect() -> str:
        streamed_text = ""
        async for chunk in agent.stream_async("Hi"):
            streamed_text += chunk.text
        return streamed_text

    streamed_text = asyncio.run(asyncio.wait_for(collect(), timeout=1.0))

    assert streamed_text == "Done"
