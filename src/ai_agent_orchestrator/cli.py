from __future__ import annotations

import runpy
from pathlib import Path
from typing import Annotated, Iterable, Literal

import typer

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
            ...,
            "--name",
            help="Example to run.",
            case_sensitive=False,
        ),
    ],
) -> None:
    """Run one of the packaged examples."""
    example_path = _get_example_path(name)
    runpy.run_path(str(example_path), run_name="__main__")


@app.command("list-tools")
def list_tools() -> None:
    """List the built-in tools registered in the default registry."""
    registry = _build_default_registry()
    for name, description in sorted(_iter_registered_tools(registry)):
        typer.echo(f"{name}: {description}")


def _get_example_path(example_name: ExampleName) -> Path:
    repo_root = Path(__file__).resolve().parents[2]
    examples_dir = repo_root / "examples"
    example_paths = {
        "basic_chat": examples_dir / "basic_chat.py",
        "tool_calling": examples_dir / "tool_calling.py",
        "routed_flow": examples_dir / "routed_flow.py",
    }
    return example_paths[example_name]


def main() -> None:
    app()
