from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ai_agent_orchestrator.llm import LLMClient
from ai_agent_orchestrator.memory.base import Memory
from ai_agent_orchestrator.protocol.messages import Message
from ai_agent_orchestrator.protocol.outputs import FinalOutput, ToolCallOutput, parse_output
from ai_agent_orchestrator.tools.registry import ToolRegistry


@dataclass
class AgentEvent:
    type: str
    content: str
    tool_name: str | None = None
    args: dict | None = None


@dataclass
class AgentResponse:
    content: str
    events: List[AgentEvent] = field(default_factory=list)


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

        for _ in range(self.max_steps):
            conversation = self.memory.get_conversation()
            raw_output = self.llm.generate(conversation)
            events.append(AgentEvent(type="llm_response", content=raw_output))
            parsed = parse_output(raw_output)

            if isinstance(parsed, ToolCallOutput):
                events.append(
                    AgentEvent(
                        type="tool_call",
                        content="",
                        tool_name=parsed.tool_name,
                        args=parsed.args,
                    )
                )
                tool_result = self.tools.run(parsed.tool_name, parsed.args)
                self.memory.add(
                    Message(role="tool", content=tool_result, name=parsed.tool_name)
                )
                events.append(
                    AgentEvent(
                        type="tool_result",
                        content=tool_result,
                        tool_name=parsed.tool_name,
                    )
                )
                continue

            if isinstance(parsed, FinalOutput):
                self.memory.add(Message(role="assistant", content=parsed.content))
                events.append(AgentEvent(type="final", content=parsed.content))
                return AgentResponse(content=parsed.content, events=events)

        fallback = "Max steps reached without final response."
        self.memory.add(Message(role="assistant", content=fallback))
        events.append(AgentEvent(type="final", content=fallback))
        return AgentResponse(content=fallback, events=events)
