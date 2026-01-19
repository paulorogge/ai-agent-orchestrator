import asyncio

from ai_agent_orchestrator.agent import Agent, AgentEventType
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def test_agent_handles_tool_then_final_async() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 2, "b": 5},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(MathAddTool())
    memory = InMemoryMemory()

    agent = Agent(llm=llm, tools=tools, memory=memory)
    response = asyncio.run(agent.run_async("Add numbers"))

    assert response.content == "Done"
    assert response.steps_used == 2
    assert any(event.type == AgentEventType.TOOL_RESULT for event in response.events)
