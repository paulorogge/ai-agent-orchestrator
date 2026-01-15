from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol


@dataclass(frozen=True)
class AgentEvent:
    name: str
    time_ms: int
    run_id: str
    step: int
    span_id: str
    parent_span_id: str | None
    data: dict[str, Any]


class SupportsEmit(Protocol):
    def emit(self, event: AgentEvent) -> None: ...


EventSink = Callable[[AgentEvent], None] | SupportsEmit


def emit_event(sink: EventSink | None, event: AgentEvent) -> None:
    if sink is None:
        return
    if callable(sink):
        sink(event)
        return
    sink.emit(event)


def build_event(
    *,
    name: str,
    time_ms: int,
    run_id: str,
    step: int,
    span_id: str,
    parent_span_id: str | None,
    data: dict[str, Any] | None = None,
) -> AgentEvent:
    return AgentEvent(
        name=name,
        time_ms=time_ms,
        run_id=run_id,
        step=step,
        span_id=span_id,
        parent_span_id=parent_span_id,
        data={} if data is None else data,
    )


class ListEventSink:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        self.events.append(event)
