from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput
from ai_agent_orchestrator.router import Route, Router
from ai_agent_orchestrator.tools.registry import ToolRegistry


def build_agent(label: str) -> Agent:
    response = FinalOutput(type="final", content=f"Handled by {label}").model_dump_json()
    llm = FakeLLM([response])
    return Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory())


def main() -> None:
    sales_agent = build_agent("sales")
    support_agent = build_agent("support")

    router = Router(default_agent=support_agent)
    router.add_route(
        Route(
            name="sales",
            predicate=lambda text: "buy" in text.lower(),
            agent=sales_agent,
        )
    )

    result = router.route("I want to buy")
    print(result.content)


if __name__ == "__main__":
    main()
