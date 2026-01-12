from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def main() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 2, "b": 3},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Result computed.").model_dump_json()

    llm = FakeLLM([tool_call, final])
    memory = InMemoryMemory()
    tools = ToolRegistry()
    tools.register(MathAddTool())
    agent = Agent(llm=llm, tools=tools, memory=memory)

    response = agent.run("Compute 2 + 3")
    print(response.content)


if __name__ == "__main__":
    main()
