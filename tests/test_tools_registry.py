import pytest

from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.registry import ToolRegistry
from ai_agent_orchestrator.utils.errors import ToolExecutionError, ToolNotFoundError


def test_registry_runs_tool() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    result = registry.run("echo", {"message": "hello"})
    assert result == "hello"


def test_registry_missing_tool_raises() -> None:
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        registry.run("missing", {})


def test_registry_invalid_args_raise() -> None:
    registry = ToolRegistry()
    registry.register(EchoTool())

    with pytest.raises(ToolExecutionError):
        registry.run("echo", {"message": 123})
