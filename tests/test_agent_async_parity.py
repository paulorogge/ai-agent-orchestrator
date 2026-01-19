import asyncio
import time
from typing import Callable

import pytest

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.observability.events import (
    AgentEvent as ObservabilityEvent,
)
from ai_agent_orchestrator.observability.events import (
    ListEventSink,
)
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput
from ai_agent_orchestrator.tools.base import Tool, ToolInput
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry
from ai_agent_orchestrator.utils.errors import ToolExecutionError


class BoomToolInput(ToolInput):
    reason: str


class BoomTool(Tool[BoomToolInput]):
    name = "boom.tool"
    description = "Always fails."
    input_model = BoomToolInput

    def run(self, validated_input: BoomToolInput) -> str:
        raise RuntimeError(validated_input.reason)


class SleepToolInput(ToolInput):
    duration: float


class SleepTool(Tool[SleepToolInput]):
    name = "sleep.tool"
    description = "Sleeps for a bit."
    input_model = SleepToolInput

    def run(self, validated_input: SleepToolInput) -> str:
        time.sleep(validated_input.duration)
        return "slept"


class TriggeringEventSink:
    def __init__(self, tool_started: asyncio.Event) -> None:
        self.events: list[ObservabilityEvent] = []
        self._tool_started = tool_started

    def emit(self, event: ObservabilityEvent) -> None:
        self.events.append(event)
        if event.name == "agent.tool.started":
            self._tool_started.set()


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


def _event_signature(
    events: list[ObservabilityEvent],
) -> list[tuple[str, dict[str, object]]]:
    return [(event.name, event.data) for event in events]


def _event_snapshot(events: list[ObservabilityEvent]) -> list[dict[str, object]]:
    return [
        {
            "name": event.name,
            "run_id": event.run_id,
            "step": event.step,
            "span_id": event.span_id,
            "parent_span_id": event.parent_span_id,
            "data": event.data,
        }
        for event in events
    ]


def test_run_and_run_async_emit_same_events() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 1, "b": 2},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    def run_sync() -> list[ObservabilityEvent]:
        llm = FakeLLM([tool_call, final])
        tools = ToolRegistry()
        tools.register(MathAddTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=2)
        agent.run(
            "Add numbers",
            event_sink=sink,
            clock=_incrementing_clock(3000),
            run_id_factory=lambda: "run_test",
            span_id_factory=_id_factory("sp_"),
        )
        return sink.events

    def run_async() -> list[ObservabilityEvent]:
        llm = FakeLLM([tool_call, final])
        tools = ToolRegistry()
        tools.register(MathAddTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=2)
        asyncio.run(
            agent.run_async(
                "Add numbers",
                event_sink=sink,
                clock=_incrementing_clock(3000),
                run_id_factory=lambda: "run_test",
                span_id_factory=_id_factory("sp_"),
            )
        )
        return sink.events

    sync_events = run_sync()
    async_events = run_async()

    assert [event.name for event in sync_events] == [
        event.name for event in async_events
    ]
    assert _event_snapshot(sync_events) == _event_snapshot(async_events)


def test_error_emits_step_finished_once_with_error() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="boom.tool",
        args={"reason": "boom"},
    ).model_dump_json()

    def run_sync() -> list[ObservabilityEvent]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(BoomTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory)
        with pytest.raises(ToolExecutionError):
            agent.run(
                "Trigger error",
                event_sink=sink,
                clock=_incrementing_clock(4000),
                run_id_factory=lambda: "run_test",
                span_id_factory=_id_factory("sp_"),
            )
        return sink.events

    def run_async() -> list[ObservabilityEvent]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(BoomTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory)
        with pytest.raises(ToolExecutionError):
            asyncio.run(
                agent.run_async(
                    "Trigger error",
                    event_sink=sink,
                    clock=_incrementing_clock(4000),
                    run_id_factory=lambda: "run_test",
                    span_id_factory=_id_factory("sp_"),
                )
            )
        return sink.events

    sync_events = run_sync()
    async_events = run_async()

    assert [event.name for event in sync_events] == [
        event.name for event in async_events
    ]
    assert _event_snapshot(sync_events) == _event_snapshot(async_events)

    step_finished = [
        event
        for event in sync_events
        if event.name == "agent.step.finished" and event.data["outcome"] == "error"
    ]
    assert len(step_finished) == 1

    run_failed = [event for event in sync_events if event.name == "agent.run.failed"]
    assert run_failed
    assert run_failed[-1].data["error_type"] == "ToolExecutionError"

def test_tool_error_parity_sync_async() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="boom.tool",
        args={"reason": "boom"},
    ).model_dump_json()

    def run_sync() -> tuple[Exception, list[ObservabilityEvent]]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(BoomTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory)
        with pytest.raises(ToolExecutionError) as excinfo:
            agent.run(
                "Trigger error",
                event_sink=sink,
                clock=_incrementing_clock(1000),
                run_id_factory=lambda: "run_test",
                span_id_factory=_id_factory("sp_"),
            )
        return excinfo.value, sink.events

    def run_async() -> tuple[Exception, list[ObservabilityEvent]]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(BoomTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory)
        with pytest.raises(ToolExecutionError) as excinfo:
            asyncio.run(
                agent.run_async(
                    "Trigger error",
                    event_sink=sink,
                    clock=_incrementing_clock(1000),
                    run_id_factory=lambda: "run_test",
                    span_id_factory=_id_factory("sp_"),
                )
            )
        return excinfo.value, sink.events

    sync_exc, sync_events = run_sync()
    async_exc, async_events = run_async()

    assert str(sync_exc) == str(async_exc)
    assert isinstance(sync_exc.__cause__, RuntimeError)
    assert isinstance(async_exc.__cause__, RuntimeError)

    assert _event_signature(sync_events) == _event_signature(async_events)

    tool_finished = [
        event for event in sync_events if event.name == "agent.tool.finished"
    ]
    assert tool_finished
    assert tool_finished[-1].data["status"] == "error"
    assert tool_finished[-1].data["error_type"] == "ToolExecutionError"


def test_max_steps_fallback_parity_sync_async() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="math.add",
        args={"a": 1, "b": 2},
    ).model_dump_json()

    def run_sync() -> tuple[str, list[object], list[ObservabilityEvent]]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(MathAddTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=1)
        response = agent.run(
            "Add numbers",
            event_sink=sink,
            clock=_incrementing_clock(2000),
            run_id_factory=lambda: "run_test",
            span_id_factory=_id_factory("sp_"),
        )
        return response.content, response.events, sink.events

    def run_async() -> tuple[str, list[object], list[ObservabilityEvent]]:
        llm = FakeLLM([tool_call])
        tools = ToolRegistry()
        tools.register(MathAddTool())
        memory = InMemoryMemory()
        sink = ListEventSink()
        agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=1)
        response = asyncio.run(
            agent.run_async(
                "Add numbers",
                event_sink=sink,
                clock=_incrementing_clock(2000),
                run_id_factory=lambda: "run_test",
                span_id_factory=_id_factory("sp_"),
            )
        )
        return response.content, response.events, sink.events

    sync_content, sync_events, sync_observability = run_sync()
    async_content, async_events, async_observability = run_async()

    assert sync_content == async_content
    assert [event.type for event in sync_events] == [
        event.type for event in async_events
    ]
    assert _event_signature(sync_observability) == _event_signature(async_observability)

    run_finished = [
        event for event in sync_observability if event.name == "agent.run.finished"
    ]
    assert run_finished
    assert run_finished[-1].data["outcome"] == "max_steps"


def test_run_async_offloads_blocking_tool() -> None:
    tool_call = ToolCallOutput(
        type="tool_call",
        tool_name="sleep.tool",
        args={"duration": 0.2},
    ).model_dump_json()
    final = FinalOutput(type="final", content="Done").model_dump_json()

    llm = FakeLLM([tool_call, final])
    tools = ToolRegistry()
    tools.register(SleepTool())
    memory = InMemoryMemory()
    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=2)

    async def run_check() -> tuple[str, list[ObservabilityEvent]]:
        tool_started = asyncio.Event()
        sink = TriggeringEventSink(tool_started)
        task = asyncio.create_task(agent.run_async("Hi", event_sink=sink))
        await asyncio.wait_for(tool_started.wait(), timeout=0.2)
        tick = asyncio.Event()
        loop = asyncio.get_running_loop()
        loop.call_later(0.01, tick.set)
        await asyncio.wait_for(tick.wait(), timeout=0.1)
        response = await asyncio.wait_for(task, timeout=1.0)
        return response.content, sink.events

    content, events = asyncio.run(run_check())

    assert content == "Done"
    names = [event.name for event in events]
    assert "agent.tool.started" in names
    assert "agent.tool.finished" in names
    assert names.index("agent.tool.started") < names.index("agent.tool.finished")
