from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import AsyncIterator, Deque, Protocol, Sequence

from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput


class LLMClient(ABC):
    """Abstract synchronous LLM client interface."""

    @abstractmethod
    def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation."""
        raise NotImplementedError


class AsyncLLMClient(Protocol):
    """Async-compatible LLM client interface."""

    async def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation asynchronously."""


@dataclass(frozen=True)
class StreamChunk:
    """A streaming chunk of model output."""

    content: str
    is_final: bool = False


class LLMStreamClient(Protocol):
    """Streaming-capable LLM interface."""

    async def stream(self, conversation: Sequence[Message]) -> AsyncIterator[StreamChunk]:
        """Yield streaming chunks for a conversation."""


async def async_generate_via_thread(
    llm: LLMClient, conversation: Sequence[Message]
) -> str:
    """Run a sync LLMClient.generate in a thread for async callers."""
    return await asyncio.to_thread(llm.generate, conversation)


class FakeLLM(LLMClient):
    """Deterministic LLM for offline demos and tests."""

    def __init__(self, responses: Sequence[str] | None = None) -> None:
        self._responses: Deque[str] = deque(responses or [])

    def push(self, response: str) -> None:
        self._responses.append(response)

    def generate(self, conversation: Sequence[Message]) -> str:
        if self._responses:
            return self._responses.popleft()

        last_user = next(
            (msg.content for msg in reversed(conversation) if msg.role == "user"),
            "",
        )
        return FinalOutput(type="final", content=f"Echo: {last_user}").model_dump_json()
