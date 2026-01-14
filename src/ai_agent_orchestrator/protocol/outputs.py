from __future__ import annotations

import json
from typing import Any, Literal, Union

from pydantic import BaseModel, Field, ValidationError


class ToolCallOutput(BaseModel):
    type: Literal["tool_call"]
    tool_name: str
    args: dict[str, Any] = Field(default_factory=dict)


class FinalOutput(BaseModel):
    type: Literal["final"]
    content: str


OutputType = Union[ToolCallOutput, FinalOutput]


def _serialize_content(content: dict[str, Any] | list[Any]) -> str:
    try:
        return json.dumps(content, ensure_ascii=False)
    except UnicodeEncodeError:
        try:
            return json.dumps(content, ensure_ascii=True)
        except (TypeError, ValueError):
            return str(content)
    except (TypeError, ValueError):
        return str(content)


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

            if isinstance(content, (bool, int, float)) or content is None:
                return FinalOutput(type="final", content=str(content))

            if isinstance(content, (dict, list)):
                return FinalOutput(
                    type="final",
                    content=_serialize_content(content),
                )

            return FinalOutput(type="final", content=str(content))
    except ValidationError:
        return FinalOutput(type="final", content=raw)

    return FinalOutput(type="final", content=raw)
