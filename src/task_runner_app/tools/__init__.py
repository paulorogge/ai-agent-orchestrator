from __future__ import annotations

from pathlib import Path

from ai_agent_orchestrator.tools.registry import ToolRegistry

from task_runner_app.tools.files import (
    FilesListDirTool,
    FilesReadTextTool,
    FilesWriteTextTool,
    TextSearchTool,
)
from task_runner_app.tools.tasks import TaskAddTool, TaskListTool


def build_tool_registry(repo_root: Path, workspace_root: Path) -> ToolRegistry:
    registry = ToolRegistry()
    allowed_roots = [repo_root, workspace_root]

    registry.register(FilesReadTextTool(allowed_roots))
    registry.register(FilesListDirTool(allowed_roots))
    registry.register(TextSearchTool(allowed_roots))
    registry.register(FilesWriteTextTool(workspace_root))
    registry.register(TaskAddTool(workspace_root))
    registry.register(TaskListTool(workspace_root))

    return registry
