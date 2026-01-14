from __future__ import annotations

import json
from pathlib import Path

import pytest

from task_runner_app.tools import build_tool_registry
from task_runner_app.tools.files import (
    FilesListDirTool,
    FilesReadTextTool,
    FilesWriteTextTool,
    TextSearchTool,
)
from task_runner_app.tools.sandbox import SandboxPathError


def test_files_tools_allow_within_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    sample = workspace / "sample.txt"
    sample.write_text("hello\nworld", encoding="utf-8")

    read_tool = FilesReadTextTool([workspace])
    list_tool = FilesListDirTool([workspace])
    search_tool = TextSearchTool([workspace])

    assert read_tool.run(read_tool.validate({"path": str(sample)})) == "hello\nworld"

    entries = json.loads(list_tool.run(list_tool.validate({"path": str(workspace)})))
    assert "sample.txt" in entries

    results = json.loads(
        search_tool.run(search_tool.validate({"path": str(sample), "query": "world"}))
    )
    assert results == [{"line": 2, "text": "world"}]


def test_files_tools_reject_outside_root(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside_file = tmp_path / "outside.txt"
    outside_file.write_text("nope", encoding="utf-8")

    read_tool = FilesReadTextTool([workspace])
    list_tool = FilesListDirTool([workspace])
    search_tool = TextSearchTool([workspace])

    with pytest.raises(SandboxPathError):
        read_tool.run(read_tool.validate({"path": str(outside_file)}))

    with pytest.raises(SandboxPathError):
        list_tool.run(list_tool.validate({"path": str(tmp_path)}))

    with pytest.raises(SandboxPathError):
        search_tool.run(search_tool.validate({"path": str(outside_file), "query": "no"}))


def test_write_tool_restricts_to_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_tool = FilesWriteTextTool(workspace)

    allowed_path = workspace / "notes" / "todo.txt"
    message = write_tool.run(
        write_tool.validate({"path": str(allowed_path), "content": "hello"})
    )
    assert allowed_path.read_text(encoding="utf-8") == "hello"
    assert "Wrote" in message

    outside_path = tmp_path / "nope.txt"
    with pytest.raises(SandboxPathError):
        write_tool.run(
            write_tool.validate({"path": str(outside_path), "content": "blocked"})
        )


def test_tasks_alias_matches_list_output(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    tasks_path = workspace / "tasks.json"
    tasks_path.write_text(
        json.dumps(
            [{"title": "Plan", "notes": "Outline", "priority": "normal"}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    registry = build_tool_registry(tmp_path, workspace)

    list_output = registry.run("tasks.list", {})
    alias_output = registry.run("tasks", {})

    assert alias_output == list_output
