from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base class for tool inputs."""


class Tool(ABC):
    """Abstract tool interface."""

    name: str
    description: str
    input_model: Type[ToolInput]

    @abstractmethod
    def run(self, validated_input: ToolInput) -> str:
        raise NotImplementedError

    def validate(self, args: dict[str, Any]) -> ToolInput:
        return self.input_model.model_validate(args)
