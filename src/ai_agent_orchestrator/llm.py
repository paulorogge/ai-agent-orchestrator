from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Sequence

from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput


class LLMClient(ABC):
    """Abstract LLM client interface."""

    @abstractmethod
    def generate(self, conversation: Sequence[Message]) -> str:
        """Generate a response from a conversation."""
        raise NotImplementedError


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
