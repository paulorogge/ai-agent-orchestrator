import pytest

from ai_agent_orchestrator.plugins import apply_plugins
from ai_agent_orchestrator.tools import ToolRegistry


def test_apply_plugins_calls_callable() -> None:
    registry = ToolRegistry()
    seen: dict[str, ToolRegistry] = {}

    def plugin(target: ToolRegistry) -> None:
        seen["registry"] = target

    apply_plugins(registry, [plugin])

    assert seen["registry"] is registry


def test_apply_plugins_calls_registerable() -> None:
    registry = ToolRegistry()

    class RegisterablePlugin:
        def __init__(self) -> None:
            self.seen: ToolRegistry | None = None

        def register(self, target: ToolRegistry) -> None:
            self.seen = target

    plugin = RegisterablePlugin()

    apply_plugins(registry, [plugin])

    assert plugin.seen is registry


def test_apply_plugins_rejects_invalid_plugin() -> None:
    registry = ToolRegistry()

    class BadPlugin:
        def __repr__(self) -> str:
            return "BadPlugin()"

    plugin = BadPlugin()

    with pytest.raises(TypeError) as exc:
        apply_plugins(registry, [plugin])

    message = str(exc.value)
    assert "BadPlugin()" in message
    assert "BadPlugin" in message


def test_apply_plugins_empty_list_is_noop() -> None:
    registry = ToolRegistry()

    apply_plugins(registry, [])
