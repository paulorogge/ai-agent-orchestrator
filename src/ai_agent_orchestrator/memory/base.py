from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from ai_agent_orchestrator.protocol.messages import Message


class Memory(ABC):
    """Conversation memory interface."""

    @abstractmethod
    def add(self, message: Message) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_conversation(self) -> List[Message]:
        raise NotImplementedError
