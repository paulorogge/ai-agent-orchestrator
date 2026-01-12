"""ai-agent-orchestrator package."""
from __future__ import annotations

from typing import Optional

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry


def _build_default_agent() -> Agent:
    tools = ToolRegistry()
    tools.register(MathAddTool())
    tools.register(EchoTool())
    llm = FakeLLM()
    memory = InMemoryMemory()
    return Agent(llm=llm, tools=tools, memory=memory)


def main() -> None:
    """CLI entrypoint."""
    import typer

    app = typer.Typer(help="AI Agent Orchestrator CLI")

    @app.command()
    def chat(message: str, max_steps: Optional[int] = typer.Option(None)) -> None:
        """Run a single chat turn using the FakeLLM backend."""
        agent = _build_default_agent()
        if max_steps is not None:
            agent.max_steps = max_steps
        response = agent.run(message)
        typer.echo(response.content)

    app()


__all__ = [
    "Agent",
    "FakeLLM",
    "ToolRegistry",
    "InMemoryMemory",
    "main",
]
