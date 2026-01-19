from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StreamChunk:
    """A streaming chunk emitted by the agent."""

    text: str
    step: int
    is_final: bool = False
