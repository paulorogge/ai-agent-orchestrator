from __future__ import annotations

from typing import List

from ai_agent_orchestrator.memory.base import Memory
from ai_agent_orchestrator.protocol.messages import Message


class InMemoryMemory(Memory):
    """Simple in-memory conversation store."""

    def __init__(self) -> None:
        self._messages: List[Message] = []

    def add(self, message: Message) -> None:
        self._messages.append(message)

    def get_conversation(self) -> List[Message]:
        return list(self._messages)
