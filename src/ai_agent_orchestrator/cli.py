from __future__ import annotations

from typing import Annotated, Callable, Dict, Iterable, Literal

import typer

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.router import Route, Router
from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry

app = typer.Typer(no_args_is_help=True)

ExampleName = Literal["basic_chat", "tool_calling", "routed_flow"]


def _build_default_registry() -> ToolRegistry:
    tools = ToolRegistry()
    tools.register(MathAddTool())
    tools.register(EchoTool())
    return tools


def _iter_registered_tools(registry: ToolRegistry) -> Iterable[tuple[str, str]]:
    tools = registry._tools
    return ((tool.name, tool.description) for tool in tools.values())


@app.command("run-example")
def run_example(
    name: Annotated[
        ExampleName,
        typer.Option(
            help="Example to run.",
            case_sensitive=False,
        ),
    ] = "basic_chat",
) -> None:
    """Run one of the packaged examples."""
    examples: Dict[str, Callable[[], None]] = {
        "basic_chat": _run_basic_chat,
        "tool_calling": _run_tool_calling,
        "routed_flow": _run_routed_flow,
    }
    examples[name]()


@app.command("list-tools")
def list_tools() -> None:
    """List the built-in tools registered in the default registry."""
    registry = _build_default_registry()
    for name, description in sorted(_iter_registered_tools(registry)):
        typer.echo(f"{name}: {description}")


def _run_basic_chat() -> None:
    llm = FakeLLM()
    memory = InMemoryMemory()
    tools = ToolRegistry()
    tools.register(EchoTool())
    agent = Agent(llm=llm, tools=tools, memory=memory)

    response = agent.run("Hello")
    typer.echo(response.content)


def _run_tool_calling() -> None:
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
    typer.echo(response.content)


def _run_routed_flow() -> None:
    sales_agent = _build_routed_agent("sales")
    support_agent = _build_routed_agent("support")

    router = Router(default_agent=support_agent)
    router.add_route(
        Route(
            name="sales",
            predicate=lambda text: "buy" in text.lower(),
            agent=sales_agent,
        )
    )

    result = router.route("I want to buy")
    typer.echo(result.content)


def _build_routed_agent(label: str) -> Agent:
    response = FinalOutput(type="final", content=f"Handled by {label}").model_dump_json()
    llm = FakeLLM([response])
    return Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory())


def main() -> None:
    app()
