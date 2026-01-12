from __future__ import annotations

import json
from typing import Any, Literal, Union

from pydantic import BaseModel, ValidationError


class ToolCallOutput(BaseModel):
    type: Literal["tool_call"]
    tool_name: str
    args: dict[str, Any]


class FinalOutput(BaseModel):
    type: Literal["final"]
    content: str


OutputType = Union[ToolCallOutput, FinalOutput]


def parse_output(raw: str) -> OutputType:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return FinalOutput(type="final", content=raw)

    if not isinstance(data, dict) or "type" not in data:
        return FinalOutput(type="final", content=raw)

    try:
        if data.get("type") == "tool_call":
            return ToolCallOutput.model_validate(data)
        if data.get("type") == "final":
            return FinalOutput.model_validate(data)
    except ValidationError:
        return FinalOutput(type="final", content=raw)

    return FinalOutput(type="final", content=raw)
