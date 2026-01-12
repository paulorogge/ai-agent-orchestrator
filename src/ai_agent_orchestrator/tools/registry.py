from __future__ import annotations

from typing import Dict

from ai_agent_orchestrator.tools.base import Tool
from ai_agent_orchestrator.utils.errors import ToolExecutionError, ToolNotFoundError


class ToolRegistry:
    """Registry for tools available to agents."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolNotFoundError(f"Tool '{name}' is not registered")
        return self._tools[name]

    def run(self, name: str, args: dict) -> str:
        tool = self.get(name)
        try:
            validated = tool.validate(args)
            return tool.run(validated)
        except Exception as exc:  # noqa: BLE001 - wrap tool errors
            raise ToolExecutionError(f"Tool '{name}' failed: {exc}") from exc
