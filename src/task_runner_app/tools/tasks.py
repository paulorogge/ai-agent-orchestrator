from __future__ import annotations

import json
from pathlib import Path

from pydantic import Field

from ai_agent_orchestrator.tools.base import Tool, ToolInput
from task_runner_app.tools.sandbox import resolve_path


class TaskAddInput(ToolInput):
    title: str
    notes: str = ""
    priority: str = Field(default="normal")


class TaskAddTool(Tool[TaskAddInput]):
    name = "tasks.add"
    description = "Add a task entry to the workspace task list."
    input_model = TaskAddInput

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def run(self, validated_input: TaskAddInput) -> str:
        tasks_path = resolve_path(
            str(self._workspace_root / "tasks.json"),
            [self._workspace_root],
        )
        tasks = _load_tasks(tasks_path)
        tasks.append(
            {
                "title": validated_input.title,
                "notes": validated_input.notes,
                "priority": validated_input.priority,
            }
        )
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2))
        return f"Added task '{validated_input.title}'"


class TaskListInput(ToolInput):
    pass


class TaskListTool(Tool[TaskListInput]):
    name = "tasks.list"
    description = "List tasks from the workspace task list."
    input_model = TaskListInput

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def run(self, validated_input: TaskListInput) -> str:
        tasks_path = resolve_path(
            str(self._workspace_root / "tasks.json"),
            [self._workspace_root],
        )
        tasks = _load_tasks(tasks_path)
        return json.dumps(tasks, ensure_ascii=False, indent=2)


def _load_tasks(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("tasks.json must contain a list")
    return data
