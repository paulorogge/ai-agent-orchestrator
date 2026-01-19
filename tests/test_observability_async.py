from __future__ import annotations

import asyncio
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


def _incrementing_clock(start: int) -> Callable[[], int]:
    current = start

    def _clock() -> int:
        nonlocal current
        value = current
        current += 1
        return value

    return _clock


def _id_factory(prefix: str) -> Callable[[], str]:
    counter = 0

    def _next() -> str:
        nonlocal counter
        counter += 1
        return f"{prefix}{counter}"

    return _next


def test_event_sequence_tool_then_final_async() -> None:
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
    asyncio.run(agent.run_async("Add numbers", event_sink=sink))

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


def test_event_payload_fields_for_key_events_async() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 3, "b": 4},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(MathAddTool())
    memory = InMemoryMemory()
    sink = ListEventSink()

    agent = Agent(llm=llm, tools=tools, memory=memory)
    asyncio.run(agent.run_async("Add numbers", event_sink=sink))

    run_started = next(
        event for event in sink.events if event.name == "agent.run.started"
    )
    assert run_started.data["max_steps"] == agent.max_steps

    step_started = [
        event for event in sink.events if event.name == "agent.step.started"
    ]
    assert step_started[0].data["input_messages_count"] == 1
    assert step_started[1].data["input_messages_count"] == 2

    model_responded = [
        event for event in sink.events if event.name == "agent.model.responded"
    ]
    assert model_responded[0].data["raw_length"] == len(tool_call)
    assert model_responded[1].data["raw_length"] == len(final)

    run_finished = next(
        event for event in sink.events if event.name == "agent.run.finished"
    )
    assert run_finished.data["steps_used"] == 2
    assert run_finished.data["outcome"] == "final"


def test_event_determinism_async() -> None:
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

    clock = _incrementing_clock(1000)

    def run_id_factory() -> str:
        return "run_test"

    span_id_factory = _id_factory("sp_")

    agent = Agent(llm=llm, tools=tools, memory=memory)
    asyncio.run(
        agent.run_async(
            "Add numbers",
            event_sink=sink,
            clock=clock,
            run_id_factory=run_id_factory,
            span_id_factory=span_id_factory,
        )
    )

    assert sink.events[0].time_ms == 1000
    assert sink.events[0].run_id == "run_test"
    assert sink.events[0].span_id == "sp_1"
    assert sink.events[1].span_id == "sp_2"
    assert sink.events[1].parent_span_id == "sp_1"
    assert sink.events[2].span_id == "sp_3"
    assert sink.events[2].parent_span_id == "sp_2"
    assert sink.events[2].step == 1
    assert sink.events[-1].name == "agent.run.finished"
    assert sink.events[-1].data["outcome"] == "final"


def test_args_keys_no_values_async() -> None:
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
    asyncio.run(agent.run_async("Add numbers", event_sink=sink))

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


def test_tool_error_emits_run_failed_and_tool_finished_async() -> None:
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

    with pytest.raises(Exception) as excinfo:
        asyncio.run(agent.run_async("Trigger error", event_sink=sink))

    tool_finished = [
        event for event in sink.events if event.name == "agent.tool.finished"
    ]
    assert tool_finished
    assert tool_finished[-1].data["status"] == "error"
    assert tool_finished[-1].data["error_type"] == excinfo.value.__class__.__name__

    step_finished = [
        event
        for event in sink.events
        if event.name == "agent.step.finished" and event.data["outcome"] == "error"
    ]
    assert len(step_finished) == 1

    run_failed = [
        event for event in sink.events if event.name == "agent.run.failed"
    ]
    assert run_failed
    assert run_failed[-1].data["error_type"] == excinfo.value.__class__.__name__

    tool_finished_index = sink.events.index(tool_finished[-1])
    step_finished_index = sink.events.index(step_finished[0])
    run_failed_index = sink.events.index(run_failed[-1])
    assert tool_finished_index < step_finished_index < run_failed_index
