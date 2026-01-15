from __future__ import annotations

from collections import deque
from typing import Callable

import pytest
from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.observability.events import ListEventSink
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.base import Tool, ToolInput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry
from ai_agent_orchestrator.utils.errors import ToolExecutionError


class ErrorToolInput(ToolInput):
    reason: str


class ErrorTool(Tool[ErrorToolInput]):
    name = "error.tool"
    description = "Always fails."
    input_model = ErrorToolInput

    def run(self, validated_input: ErrorToolInput) -> str:
        raise ValueError(validated_input.reason)


class SecretToolInput(ToolInput):
    x: int
    secret: str


class SecretTool(Tool[SecretToolInput]):
    name = "secret.tool"
    description = "Returns a safe response."
    input_model = SecretToolInput

    def run(self, validated_input: SecretToolInput) -> str:
        return f"ok:{validated_input.x}"


def _fixed_clock(start: int, count: int) -> Callable[[], int]:
    values = deque(range(start, start + count))

    def _clock() -> int:
        return values.popleft()

    return _clock


def _id_factory(prefix: str) -> Callable[[], str]:
    counter = 0

    def _next() -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}{counter}"

    return _next


def test_event_sequence_tool_then_final() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 2, "b": 5},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(MathAddTool())
    memory = InMemoryMemory()
    sink = ListEventSink()

    agent = Agent(llm=llm, tools=tools, memory=memory)
    agent.run("Add numbers", event_sink=sink)

    names = [event.name for event in sink.events]
    assert names == [
        "agent.run.started",
        "agent.step.started",
        "agent.model.requested",
        "agent.model.responded",
        "agent.output.parsed",
        "agent.tool.started",
        "agent.tool.finished",
        "agent.step.finished",
        "agent.step.started",
        "agent.model.requested",
        "agent.model.responded",
        "agent.output.parsed",
        "agent.step.finished",
        "agent.run.finished",
    ]


def test_event_determinism() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 1, "b": 2},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(MathAddTool())
    memory = InMemoryMemory()
    sink = ListEventSink()

    clock = _fixed_clock(1000, 20)
    run_id_factory = lambda: "run_test"
    span_id_factory = _id_factory("sp_")

    agent = Agent(llm=llm, tools=tools, memory=memory)
    agent.run(
        "Add numbers",
        event_sink=sink,
        clock=clock,
        run_id_factory=run_id_factory,
        span_id_factory=span_id_factory,
    )

    assert sink.events[0].time_ms == 1000
    assert sink.events[0].run_id == "run_test"
    assert sink.events[0].span_id == "sp_1"
    assert sink.events[1].span_id == "sp_2"
    assert sink.events[1].parent_span_id == "sp_1"
    assert sink.events[2].span_id == "sp_3"
    assert sink.events[2].parent_span_id == "sp_2"
    assert sink.events[2].step == 1


def test_args_keys_no_values() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="secret.tool",
        args={"x": 1, "secret": "abc"},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(SecretTool())
    memory = InMemoryMemory()
    sink = ListEventSink()

    agent = Agent(llm=llm, tools=tools, memory=memory)
    agent.run("Add numbers", event_sink=sink)

    args_key_events = [
        event
        for event in sink.events
        if event.name in {"agent.output.parsed", "agent.tool.started"}
    ]
    assert args_key_events
    for event in args_key_events:
        if "args_keys" in event.data:
            assert event.data["args_keys"] == ["secret", "x"]
        for value in event.data.values():
            assert "abc" not in str(value)


def test_tool_error_emits_run_failed_and_tool_finished() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="error.tool",
        args={"reason": "boom"},
    ).model_dump_json()

    llm = FakeLLM([tool_call])
    tools = ToolRegistry()
    tools.register(ErrorTool())
    memory = InMemoryMemory()
    sink = ListEventSink()

    agent = Agent(llm=llm, tools=tools, memory=memory)

    with pytest.raises(ToolExecutionError):
        agent.run("Trigger error", event_sink=sink)

    tool_finished = [event for event in sink.events if event.name == "agent.tool.finished"]
    assert tool_finished
    assert tool_finished[-1].data["status"] == "error"
    assert tool_finished[-1].data["error_type"] == "ToolExecutionError"

    run_failed = [event for event in sink.events if event.name == "agent.run.failed"]
    assert run_failed
    assert run_failed[-1].data["error_type"] == "ToolExecutionError"
