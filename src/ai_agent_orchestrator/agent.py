from __future__ import annotations

import asyncio
import json
import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Mapping

from ai_agent_orchestrator.llm import LLMClient, async_generate_via_thread
from ai_agent_orchestrator.memory.base import Memory
from ai_agent_orchestrator.observability.clock import Clock, system_clock_ms
from ai_agent_orchestrator.observability.events import EventSink, build_event, emit_event
from ai_agent_orchestrator.observability.ids import (
    RunIdFactory,
    SpanIdFactory,
    default_run_id,
    default_span_id,
)
from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput, parse_output
from ai_agent_orchestrator.tools.registry import ToolRegistry


class AgentEventType(str, Enum):
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL = "final"


@dataclass
class AgentEvent:
    type: AgentEventType
    content: str | None
    tool_name: str | None = None
    args: Mapping[str, Any] | None = None
    step: int = 0


@dataclass
class AgentResponse:
    content: str
    events: List[AgentEvent] = field(default_factory=list)
    steps_used: int = 0


class Agent:
    """Orchestrates a conversation loop with tool calls using a sync LLMClient."""

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        memory: Memory,
        max_steps: int = 5,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.max_steps = max_steps

    def run(
        self,
        user_input: str,
        event_sink: EventSink | None = None,
        clock: Clock = system_clock_ms,
        run_id_factory: RunIdFactory = default_run_id,
        span_id_factory: SpanIdFactory = default_span_id,
    ) -> AgentResponse:
        self.memory.add(Message(role="user", content=user_input))
        events: List[AgentEvent] = []
        run_id = run_id_factory()
        run_span_id = span_id_factory()
        tool_count = len(list(self.tools.iter_tools()))
        step_span_id = run_span_id
        current_step = 0
        step_finished_emitted = False

        emit_event(
            event_sink,
            build_event(
                name="agent.run.started",
                time_ms=clock(),
                run_id=run_id,
                step=0,
                span_id=run_span_id,
                parent_span_id=None,
                data={"max_steps": self.max_steps},
            ),
        )

        try:
            for step in range(1, self.max_steps + 1):
                current_step = step
                step_finished_emitted = False
                step_span_id = span_id_factory()
                conversation = self.memory.get_conversation()
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.step.started",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=step_span_id,
                        parent_span_id=run_span_id,
                        data={"input_messages_count": len(conversation)},
                    ),
                )
                model_span_id = span_id_factory()
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.model.requested",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "message_count": len(conversation),
                            "tool_count": tool_count,
                        },
                    ),
                )
                raw_output = self.llm.generate(conversation)
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.model.responded",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "response_type": "text",
                            "raw_length": len(raw_output),
                        },
                    ),
                )
                events.append(
                    AgentEvent(
                        type=AgentEventType.LLM_RESPONSE, content=raw_output, step=step
                    )
                )
                try:
                    parsed = parse_output(raw_output)
                except Exception:
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.output.parsed",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=model_span_id,
                            parent_span_id=step_span_id,
                            data={
                                "parsed_type": "invalid",
                                "is_valid": False,
                            },
                        ),
                    )
                    raise
                parsed_type, is_valid, output_metadata = _classify_output(
                    raw_output, parsed
                )
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.output.parsed",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "parsed_type": parsed_type,
                            "is_valid": is_valid,
                            **output_metadata,
                        },
                    ),
                )

                if isinstance(parsed, ToolCallOutput):
                    tool_span_id = span_id_factory()
                    args_keys = sorted(parsed.args.keys())
                    events.append(
                        AgentEvent(
                            type=AgentEventType.TOOL_CALL,
                            content=None,
                            tool_name=parsed.tool_name,
                            args=parsed.args,
                            step=step,
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.tool.started",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=tool_span_id,
                            parent_span_id=step_span_id,
                            data={
                                "tool_name": parsed.tool_name,
                                "args_keys": args_keys,
                                "args_count": len(args_keys),
                            },
                        ),
                    )
                    tool_status = "ok"
                    error_type = None
                    try:
                        tool_result = self.tools.run(parsed.tool_name, parsed.args)
                    except Exception as exc:
                        tool_status = "error"
                        error_type = exc.__class__.__name__
                        raise
                    finally:
                        emit_event(
                            event_sink,
                            build_event(
                                name="agent.tool.finished",
                                time_ms=clock(),
                                run_id=run_id,
                                step=step,
                                span_id=tool_span_id,
                                parent_span_id=step_span_id,
                                data={
                                    "tool_name": parsed.tool_name,
                                    "status": tool_status,
                                    "error_type": error_type,
                                },
                            ),
                        )
                    self.memory.add(
                        Message(role="tool", content=tool_result, name=parsed.tool_name)
                    )
                    events.append(
                        AgentEvent(
                            type=AgentEventType.TOOL_RESULT,
                            content=tool_result,
                            tool_name=parsed.tool_name,
                            step=step,
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.step.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=step_span_id,
                            parent_span_id=run_span_id,
                            data={"outcome": "tool_call"},
                        ),
                    )
                    step_finished_emitted = True
                    continue

                if isinstance(parsed, FinalOutput):
                    self.memory.add(Message(role="assistant", content=parsed.content))
                    events.append(
                        AgentEvent(
                            type=AgentEventType.FINAL, content=parsed.content, step=step
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.step.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=step_span_id,
                            parent_span_id=run_span_id,
                            data={"outcome": "final"},
                        ),
                    )
                    step_finished_emitted = True
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.run.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=run_span_id,
                            parent_span_id=None,
                            data={"steps_used": step, "outcome": "final"},
                        ),
                    )
                    return AgentResponse(
                        content=parsed.content, events=events, steps_used=step
                    )

            fallback = "Max steps reached without final response."
            self.memory.add(Message(role="assistant", content=fallback))
            events.append(
                AgentEvent(
                    type=AgentEventType.FINAL,
                    content=fallback,
                    step=self.max_steps,
                )
            )
            emit_event(
                event_sink,
                build_event(
                    name="agent.step.finished",
                    time_ms=clock(),
                    run_id=run_id,
                    step=self.max_steps,
                    span_id=step_span_id,
                    parent_span_id=run_span_id,
                    data={"outcome": "max_steps"},
                ),
            )
            step_finished_emitted = True
            emit_event(
                event_sink,
                build_event(
                    name="agent.run.finished",
                    time_ms=clock(),
                    run_id=run_id,
                    step=self.max_steps,
                    span_id=run_span_id,
                    parent_span_id=None,
                    data={"steps_used": self.max_steps, "outcome": "max_steps"},
                ),
            )
            return AgentResponse(
                content=fallback, events=events, steps_used=self.max_steps
            )
        except Exception as exc:
            if current_step and not step_finished_emitted:
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.step.finished",
                        time_ms=clock(),
                        run_id=run_id,
                        step=current_step,
                        span_id=step_span_id,
                        parent_span_id=run_span_id,
                        data={"outcome": "error"},
                    ),
                )
            emit_event(
                event_sink,
                build_event(
                    name="agent.run.failed",
                    time_ms=clock(),
                    run_id=run_id,
                    step=current_step,
                    span_id=run_span_id,
                    parent_span_id=None,
                    data={"error_type": exc.__class__.__name__},
                ),
            )
            raise

    async def run_async(
        self,
        user_input: str,
        event_sink: EventSink | None = None,
        clock: Clock = system_clock_ms,
        run_id_factory: RunIdFactory = default_run_id,
        span_id_factory: SpanIdFactory = default_span_id,
    ) -> AgentResponse:
        self.memory.add(Message(role="user", content=user_input))
        events: List[AgentEvent] = []
        run_id = run_id_factory()
        run_span_id = span_id_factory()
        tool_count = len(list(self.tools.iter_tools()))
        step_span_id = run_span_id
        current_step = 0
        step_finished_emitted = False

        emit_event(
            event_sink,
            build_event(
                name="agent.run.started",
                time_ms=clock(),
                run_id=run_id,
                step=0,
                span_id=run_span_id,
                parent_span_id=None,
                data={"max_steps": self.max_steps},
            ),
        )

        try:
            for step in range(1, self.max_steps + 1):
                current_step = step
                step_finished_emitted = False
                step_span_id = span_id_factory()
                conversation = self.memory.get_conversation()
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.step.started",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=step_span_id,
                        parent_span_id=run_span_id,
                        data={"input_messages_count": len(conversation)},
                    ),
                )
                model_span_id = span_id_factory()
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.model.requested",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "message_count": len(conversation),
                            "tool_count": tool_count,
                        },
                    ),
                )
                if inspect.iscoroutinefunction(self.llm.generate):
                    raw_output = await self.llm.generate(conversation)
                else:
                    raw_output = await async_generate_via_thread(
                        self.llm, conversation
                    )
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.model.responded",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "response_type": "text",
                            "raw_length": len(raw_output),
                        },
                    ),
                )
                events.append(
                    AgentEvent(
                        type=AgentEventType.LLM_RESPONSE, content=raw_output, step=step
                    )
                )
                try:
                    parsed = parse_output(raw_output)
                except Exception:
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.output.parsed",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=model_span_id,
                            parent_span_id=step_span_id,
                            data={
                                "parsed_type": "invalid",
                                "is_valid": False,
                            },
                        ),
                    )
                    raise
                parsed_type, is_valid, output_metadata = _classify_output(
                    raw_output, parsed
                )
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.output.parsed",
                        time_ms=clock(),
                        run_id=run_id,
                        step=step,
                        span_id=model_span_id,
                        parent_span_id=step_span_id,
                        data={
                            "parsed_type": parsed_type,
                            "is_valid": is_valid,
                            **output_metadata,
                        },
                    ),
                )

                if isinstance(parsed, ToolCallOutput):
                    tool_span_id = span_id_factory()
                    args_keys = sorted(parsed.args.keys())
                    events.append(
                        AgentEvent(
                            type=AgentEventType.TOOL_CALL,
                            content=None,
                            tool_name=parsed.tool_name,
                            args=parsed.args,
                            step=step,
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.tool.started",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=tool_span_id,
                            parent_span_id=step_span_id,
                            data={
                                "tool_name": parsed.tool_name,
                                "args_keys": args_keys,
                                "args_count": len(args_keys),
                            },
                        ),
                    )
                    tool_status = "ok"
                    error_type = None
                    try:
                        tool_result = await asyncio.to_thread(
                            self.tools.run, parsed.tool_name, parsed.args
                        )
                    except Exception as exc:
                        tool_status = "error"
                        error_type = exc.__class__.__name__
                        raise
                    finally:
                        emit_event(
                            event_sink,
                            build_event(
                                name="agent.tool.finished",
                                time_ms=clock(),
                                run_id=run_id,
                                step=step,
                                span_id=tool_span_id,
                                parent_span_id=step_span_id,
                                data={
                                    "tool_name": parsed.tool_name,
                                    "status": tool_status,
                                    "error_type": error_type,
                                },
                            ),
                        )
                    self.memory.add(
                        Message(
                            role="tool", content=tool_result, name=parsed.tool_name
                        )
                    )
                    events.append(
                        AgentEvent(
                            type=AgentEventType.TOOL_RESULT,
                            content=tool_result,
                            tool_name=parsed.tool_name,
                            step=step,
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.step.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=step_span_id,
                            parent_span_id=run_span_id,
                            data={"outcome": "tool_call"},
                        ),
                    )
                    step_finished_emitted = True
                    continue

                if isinstance(parsed, FinalOutput):
                    self.memory.add(Message(role="assistant", content=parsed.content))
                    events.append(
                        AgentEvent(
                            type=AgentEventType.FINAL, content=parsed.content, step=step
                        )
                    )
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.step.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=step_span_id,
                            parent_span_id=run_span_id,
                            data={"outcome": "final"},
                        ),
                    )
                    step_finished_emitted = True
                    emit_event(
                        event_sink,
                        build_event(
                            name="agent.run.finished",
                            time_ms=clock(),
                            run_id=run_id,
                            step=step,
                            span_id=run_span_id,
                            parent_span_id=None,
                            data={"steps_used": step, "outcome": "final"},
                        ),
                    )
                    return AgentResponse(
                        content=parsed.content, events=events, steps_used=step
                    )

            fallback = "Max steps reached without final response."
            self.memory.add(Message(role="assistant", content=fallback))
            events.append(
                AgentEvent(
                    type=AgentEventType.FINAL,
                    content=fallback,
                    step=self.max_steps,
                )
            )
            emit_event(
                event_sink,
                build_event(
                    name="agent.step.finished",
                    time_ms=clock(),
                    run_id=run_id,
                    step=self.max_steps,
                    span_id=step_span_id,
                    parent_span_id=run_span_id,
                    data={"outcome": "max_steps"},
                ),
            )
            step_finished_emitted = True
            emit_event(
                event_sink,
                build_event(
                    name="agent.run.finished",
                    time_ms=clock(),
                    run_id=run_id,
                    step=self.max_steps,
                    span_id=run_span_id,
                    parent_span_id=None,
                    data={"steps_used": self.max_steps, "outcome": "max_steps"},
                ),
            )
            return AgentResponse(
                content=fallback, events=events, steps_used=self.max_steps
            )
        except Exception as exc:
            if current_step and not step_finished_emitted:
                emit_event(
                    event_sink,
                    build_event(
                        name="agent.step.finished",
                        time_ms=clock(),
                        run_id=run_id,
                        step=current_step,
                        span_id=step_span_id,
                        parent_span_id=run_span_id,
                        data={"outcome": "error"},
                    ),
                )
            emit_event(
                event_sink,
                build_event(
                    name="agent.run.failed",
                    time_ms=clock(),
                    run_id=run_id,
                    step=current_step,
                    span_id=run_span_id,
                    parent_span_id=None,
                    data={"error_type": exc.__class__.__name__},
                ),
            )
            raise


def _classify_output(
    raw: str, parsed: FinalOutput | ToolCallOutput
) -> tuple[str, bool, dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return "invalid", False, {}

    if not isinstance(data, dict):
        return "invalid", False, {}

    output_type = data.get("type")
    if output_type == "tool_call":
        if isinstance(parsed, ToolCallOutput):
            return (
                "tool_call",
                True,
                {
                    "tool_name": parsed.tool_name,
                    "args_keys": sorted(parsed.args.keys()),
                },
            )
        return "invalid", False, {}
    if output_type == "final":
        if "content" in data and isinstance(parsed, FinalOutput):
            return "final", True, {}
        return "invalid", False, {}

    return "invalid", False, {}
