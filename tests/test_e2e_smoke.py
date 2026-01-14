from ai_agent_orchestrator.agent import Agent, AgentEventType
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def test_e2e_smoke_tool_flow() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 3, "b": 4},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Result computed.").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(MathAddTool())
    memory = InMemoryMemory()

    agent = Agent(llm=llm, tools=tools, memory=memory)
    response = agent.run("Add 3 and 4.")

    assert response.content == "Result computed."
    assert response.steps_used == 2

    event_types = [event.type for event in response.events]
    assert AgentEventType.TOOL_CALL in event_types
    assert AgentEventType.TOOL_RESULT in event_types
    assert AgentEventType.FINAL in event_types

    tool_call_index = event_types.index(AgentEventType.TOOL_CALL)
    tool_result_index = event_types.index(AgentEventType.TOOL_RESULT)
    final_index = event_types.index(AgentEventType.FINAL)
    assert tool_call_index < tool_result_index < final_index
