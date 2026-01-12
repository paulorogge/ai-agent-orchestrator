from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def main() -> None:
    llm = FakeLLM()
    memory = InMemoryMemory()
    tools = ToolRegistry()
    tools.register(EchoTool())
    agent = Agent(llm=llm, tools=tools, memory=memory)

    response = agent.run("Hello")
    print(response.content)


if __name__ == "__main__":
    main()
