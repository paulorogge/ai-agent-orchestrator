"""Example: explicit-only plugins registering tools (no discovery)."""
from __future__ import annotations

from ai_agent_orchestrator.plugins import apply_plugins
from ai_agent_orchestrator.tools import Tool, ToolInput, ToolRegistry


class NameInput(ToolInput):
    name: str


class HelloTool(Tool[NameInput]):
    name = "hello"
    description = "Say hello to someone."
    input_model = NameInput

    def run(self, validated_input: NameInput) -> str:
        return f"Hello, {validated_input.name}!"


def callable_plugin(registry: ToolRegistry) -> None:
    """Register tools explicitly (no discovery)."""
    registry.register(HelloTool())


class GoodbyeTool(Tool[NameInput]):
    name = "goodbye"
    description = "Say goodbye to someone."
    input_model = NameInput

    def run(self, validated_input: NameInput) -> str:
        return f"Goodbye, {validated_input.name}."


class RegisterablePlugin:
    """Register tools explicitly (no discovery)."""

    def register(self, registry: ToolRegistry) -> None:
        registry.register(GoodbyeTool())


def main() -> None:
    registry = ToolRegistry()
    apply_plugins(registry, [callable_plugin, RegisterablePlugin()])

    print(registry.run("hello", {"name": "Ada"}))
    print(registry.run("goodbye", {"name": "Linus"}))


if __name__ == "__main__":
    main()
