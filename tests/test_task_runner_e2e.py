from __future__ import annotations

import json
from pathlib import Path

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.messages import Message
from task_runner_app.tools import build_tool_registry


def test_task_runner_flow_with_fake_llm(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    tool_call = {
        "type": "tool_call",
        "tool_name": "tasks.add",
        "args": {"title": "Ship release", "notes": "Prep", "priority": "high"},
    }
    final_response = {"type": "final", "content": "Added!"}

    llm = FakeLLM(
        responses=[json.dumps(tool_call, ensure_ascii=False), json.dumps(final_response)]
    )
    memory = InMemoryMemory()
    memory.add(Message(role="system", content="You are a test."))

    tools = build_tool_registry(tmp_path, workspace)
    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=3)

    response = agent.run("Add a task")

    assert response.content == "Added!"

    tasks_path = workspace / "tasks.json"
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    assert tasks == [
        {"title": "Ship release", "notes": "Prep", "priority": "high"}
    ]
