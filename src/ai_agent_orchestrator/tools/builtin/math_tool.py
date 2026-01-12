from __future__ import annotations

from pydantic import BaseModel, Field

from ai_agent_orchestrator.tools.base import Tool


class MathAddInput(BaseModel):
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")


class MathAddTool(Tool):
    name = "math.add"
    description = "Add two numbers"
    input_model = MathAddInput

    def run(self, validated_input: MathAddInput) -> str:
        return str(validated_input.a + validated_input.b)
