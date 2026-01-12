from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput
from ai_agent_orchestrator.router import Route, Router
from ai_agent_orchestrator.tools.registry import ToolRegistry


def build_agent(message: str) -> Agent:
    llm = FakeLLM([FinalOutput(type="final", content=message).model_dump_json()])
    return Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory())


def test_router_routes_to_matching_agent() -> None:
    sales = build_agent("sales")
    support = build_agent("support")

    router = Router(default_agent=support)
    router.add_route(
        Route(name="sales", predicate=lambda text: "buy" in text, agent=sales)
    )

    response = router.route("buy now")
    assert response.content == "sales"


def test_router_falls_back_to_default() -> None:
    sales = build_agent("sales")
    support = build_agent("support")
    router = Router(default_agent=support)
    router.add_route(
        Route(name="sales", predicate=lambda text: "buy" in text, agent=sales)
    )

    response = router.route("help")
    assert response.content == "support"
