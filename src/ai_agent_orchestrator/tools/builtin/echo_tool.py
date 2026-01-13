from __future__ import annotations

from ai_agent_orchestrator.tools.base import Tool, ToolInput


class EchoInput(ToolInput):
    message: str


class EchoTool(Tool[EchoInput]):
    name = "echo"
    description = "Echo back a message"
    input_model = EchoInput

    def run(self, validated_input: EchoInput) -> str:
        return validated_input.message
