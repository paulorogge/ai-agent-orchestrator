from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass
from typing import AsyncIterator, Deque, Protocol, Sequence, TypeAlias

from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput


@dataclass(frozen=True)
class LLMStreamChunk:
    """A streaming chunk of model output."""

    content: str
    is_final: bool = False


class SupportsSyncGenerate(Protocol):
    """Protocol for LLMs that provide a synchronous generate method."""

    def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation."""


class SupportsAsyncGenerate(Protocol):
    """Protocol for LLMs that provide an async generate method."""

    async def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation asynchronously."""


class SupportsAsyncStream(Protocol):
    """Optional protocol for LLMs that provide an async stream method."""

    async def stream(
        self, conversation: Sequence[Message]
    ) -> AsyncIterator[LLMStreamChunk]:
        """Yield streaming chunks for a conversation."""


LLMClientProtocol: TypeAlias = SupportsSyncGenerate | SupportsAsyncGenerate


LLMClientStreamProtocol: TypeAlias = SupportsAsyncStream


class LLMClient(ABC):
    """Abstract synchronous LLM client interface."""

    @abstractmethod
    def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation."""
        raise NotImplementedError


async def async_generate_via_thread(
    llm: SupportsSyncGenerate, conversation: Sequence[Message]
) -> str:
    """Run a sync generate method in a thread for async callers."""
    return await asyncio.to_thread(llm.generate, conversation)


class FakeLLM(LLMClient):
    """Deterministic LLM for offline demos and tests."""

    def __init__(
        self, responses: Sequence[str] | None = None, chunk_size: int | None = None
    ) -> None:
        self._responses: Deque[str] = deque(responses or [])
        self._chunk_size = chunk_size

    def push(self, response: str) -> None:
        self._responses.append(response)

    def generate(self, conversation: Sequence[Message]) -> str:
        return self._next_response(conversation)

    async def stream(
        self, conversation: Sequence[Message]
    ) -> AsyncIterator[LLMStreamChunk]:
        chunk_size = self._chunk_size
        if chunk_size is not None and chunk_size <= 0:
            raise ValueError("chunk_size must be a positive integer or None.")
        response = self._next_response(conversation)
        if chunk_size is None:
            yield LLMStreamChunk(content=response, is_final=True)
            return
        for offset in range(0, len(response), chunk_size):
            chunk = response[offset : offset + chunk_size]
            is_final = offset + chunk_size >= len(response)
            yield LLMStreamChunk(content=chunk, is_final=is_final)

    def _next_response(self, conversation: Sequence[Message]) -> str:
        if self._responses:
            return self._responses.popleft()

        last_user = next(
            (msg.content for msg in reversed(conversation) if msg.role == "user"),
            "",
        )
        return FinalOutput(type="final", content=f"Echo: {last_user}").model_dump_json()
