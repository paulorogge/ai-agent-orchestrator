from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from ai_agent_orchestrator.tools.base import Tool, ToolInput
from task_runner_app.tools.sandbox import resolve_path

MAX_SEARCH_FILE_SIZE = 200_000


class ReadTextInput(ToolInput):
    path: str


class ListDirInput(ToolInput):
    path: str


class WriteTextInput(ToolInput):
    path: str
    content: str


class SearchTextInput(ToolInput):
    path: str
    query: str = Field(min_length=1)


class FilesReadTextTool(Tool[ReadTextInput]):
    name = "files.read_text"
    description = "Read a UTF-8 text file within the repo or workspace."
    input_model = ReadTextInput

    def __init__(self, allowed_roots: list[Path]) -> None:
        self._allowed_roots = allowed_roots

    def run(self, validated_input: ReadTextInput) -> str:
        resolved = resolve_path(validated_input.path, self._allowed_roots)
        if not resolved.is_file():
            raise ValueError(f"{resolved} is not a file")
        return resolved.read_text(encoding="utf-8", errors="replace")


class FilesListDirTool(Tool[ListDirInput]):
    name = "files.list_dir"
    description = "List directory contents within the repo or workspace."
    input_model = ListDirInput

    def __init__(self, allowed_roots: list[Path]) -> None:
        self._allowed_roots = allowed_roots

    def run(self, validated_input: ListDirInput) -> str:
        resolved = resolve_path(validated_input.path, self._allowed_roots)
        if not resolved.is_dir():
            raise ValueError(f"{resolved} is not a directory")
        entries = sorted(path.name for path in resolved.iterdir())
        return json.dumps(entries, ensure_ascii=False)


class FilesWriteTextTool(Tool[WriteTextInput]):
    name = "files.write_text"
    description = "Write text to a file within the workspace only."
    input_model = WriteTextInput

    def __init__(self, workspace_root: Path) -> None:
        self._workspace_root = workspace_root

    def run(self, validated_input: WriteTextInput) -> str:
        resolved = resolve_path(validated_input.path, [self._workspace_root])
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(validated_input.content, encoding="utf-8")
        return f"Wrote {len(validated_input.content)} characters to {resolved}"


class TextSearchTool(Tool[SearchTextInput]):
    name = "text.search"
    description = "Search for a string within a text file (size-limited)."
    input_model = SearchTextInput

    def __init__(self, allowed_roots: list[Path]) -> None:
        self._allowed_roots = allowed_roots

    def run(self, validated_input: SearchTextInput) -> str:
        resolved = resolve_path(validated_input.path, self._allowed_roots)
        if not resolved.is_file():
            raise ValueError(f"{resolved} is not a file")
        if resolved.stat().st_size > MAX_SEARCH_FILE_SIZE:
            raise ValueError("File too large to search")

        results: list[dict[str, str | int]] = []
        for idx, line in enumerate(
            resolved.read_text(encoding="utf-8", errors="replace").splitlines(),
            start=1,
        ):
            if validated_input.query in line:
                results.append({"line": idx, "text": line})
        return json.dumps(results, ensure_ascii=False)
