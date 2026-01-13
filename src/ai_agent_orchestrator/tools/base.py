from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base class for tool inputs."""


TToolInput = TypeVar("TToolInput", bound=ToolInput)


class Tool(ABC, Generic[TToolInput]):
    """Abstract tool interface."""

    name: str
    description: str
    input_model: type[TToolInput]

    @abstractmethod
    def run(self, validated_input: TToolInput) -> str:
        raise NotImplementedError

    def validate(self, args: dict[str, Any]) -> TToolInput:
        return self.input_model.model_validate(args)
