from __future__ import annotations

from pydantic import BaseModel

from ai_agent_orchestrator.tools.base import Tool


class EchoInput(BaseModel):
    message: str


class EchoTool(Tool):
    name = "echo"
    description = "Echo back a message"
    input_model = EchoInput

    def run(self, validated_input: EchoInput) -> str:
        return validated_input.message
