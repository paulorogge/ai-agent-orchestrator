"""Explicit-only plugin helpers (no discovery)."""
from __future__ import annotations

from typing import Iterable, Protocol, runtime_checkable

from ai_agent_orchestrator.tools import ToolRegistry


@runtime_checkable
class PluginProtocol(Protocol):
    def register(self, registry: ToolRegistry) -> None: ...


def apply_plugins(registry: ToolRegistry, plugins: Iterable[object]) -> None:
    """Apply callable plugins or objects implementing register()."""
    for plugin in plugins:
        if isinstance(plugin, PluginProtocol):
            plugin.register(registry)
            continue
        if callable(plugin):
            plugin(registry)
            continue
        raise TypeError(
            "Plugin must implement register(registry) or be callable."
        )
