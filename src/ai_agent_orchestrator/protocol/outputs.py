from __future__ import annotations

import json
from typing import Any, Literal, Union

from pydantic import BaseModel, ValidationError, Field


class ToolCallOutput(BaseModel):
    type: Literal["tool_call"]
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)


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
            tool_name = data.get("tool_name")
            if not isinstance(tool_name, str) or not tool_name.strip():
                return FinalOutput(type="final", content=raw)

            args = data.get("args", {})
            if args is None:
                args = {}
            if not isinstance(args, dict):
                return FinalOutput(type="final", content=raw)

            return ToolCallOutput.model_validate(
                {"type": "tool_call", "tool_name": tool_name, "args": args}
            )
        if data.get("type") == "final":
            if "content" not in data:
                return FinalOutput(type="final", content=raw)

            content = data.get("content")
            if isinstance(content, str):
                return FinalOutput(type="final", content=content)

            try:
                return FinalOutput(type="final", content=str(content))
            except Exception:
                return FinalOutput(type="final", content=raw)
    except ValidationError:
        return FinalOutput(type="final", content=raw)

    return FinalOutput(type="final", content=raw)
