from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def test_agent_handles_tool_then_final() -> None:
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
    response = agent.run("Add numbers")

    assert response.content == "Done"
    assert any(event.type == "tool_result" for event in response.events)
