from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Mapping

from ai_agent_orchestrator.llm import LLMClient
from ai_agent_orchestrator.memory.base import Memory
from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput, parse_output
from ai_agent_orchestrator.tools.registry import ToolRegistry


class AgentEventType(str, Enum):
    LLM_RESPONSE = "llm_response"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FINAL = "final"


@dataclass
class AgentEvent:
    type: AgentEventType
    content: str | None
    tool_name: str | None = None
    args: Mapping[str, Any] | None = None
    step: int = 0


@dataclass
class AgentResponse:
    content: str
    events: List[AgentEvent] = field(default_factory=list)
    steps_used: int = 0


class Agent:
    """Orchestrates a conversation loop with tool calls."""

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        memory: Memory,
        max_steps: int = 5,
    ) -> None:
        self.llm = llm
        self.tools = tools
        self.memory = memory
        self.max_steps = max_steps

    def run(self, user_input: str) -> AgentResponse:
        self.memory.add(Message(role="user", content=user_input))
        events: List[AgentEvent] = []

        for step in range(1, self.max_steps + 1):
            conversation = self.memory.get_conversation()
            raw_output = self.llm.generate(conversation)
            events.append(
                AgentEvent(
                    type=AgentEventType.LLM_RESPONSE, content=raw_output, step=step
                )
            )
            parsed = parse_output(raw_output)

            if isinstance(parsed, ToolCallOutput):
                events.append(
                    AgentEvent(
                        type=AgentEventType.TOOL_CALL,
                        content=None,
                        tool_name=parsed.tool_name,
                        args=parsed.args,
                        step=step,
                    )
                )
                tool_result = self.tools.run(parsed.tool_name, parsed.args)
                self.memory.add(
                    Message(role="tool", content=tool_result, name=parsed.tool_name)
                )
                events.append(
                    AgentEvent(
                        type=AgentEventType.TOOL_RESULT,
                        content=tool_result,
                        tool_name=parsed.tool_name,
                        step=step,
                    )
                )
                continue

            if isinstance(parsed, FinalOutput):
                self.memory.add(Message(role="assistant", content=parsed.content))
                events.append(
                    AgentEvent(
                        type=AgentEventType.FINAL, content=parsed.content, step=step
                    )
                )
                return AgentResponse(
                    content=parsed.content, events=events, steps_used=step
                )

        fallback = "Max steps reached without final response."
        self.memory.add(Message(role="assistant", content=fallback))
        events.append(
            AgentEvent(
                type=AgentEventType.FINAL,
                content=fallback,
                step=self.max_steps,
            )
        )
        return AgentResponse(
            content=fallback, events=events, steps_used=self.max_steps
        )
