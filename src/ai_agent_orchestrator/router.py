from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List

from ai_agent_orchestrator.agent import Agent, AgentResponse


@dataclass
class Route:
    name: str
    predicate: Callable[[str], bool]
    agent: Agent


class Router:
    """Routes user input to the appropriate agent."""

    def __init__(self, default_agent: Agent) -> None:
        self.default_agent = default_agent
        self._routes: List[Route] = []

    def add_route(self, route: Route) -> None:
        self._routes.append(route)

    def route(self, user_input: str) -> AgentResponse:
        for route in self._routes:
            if route.predicate(user_input):
                return route.agent.run(user_input)
        return self.default_agent.run(user_input)
