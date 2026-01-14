from __future__ import annotations

import os
from pathlib import Path
from typing import Annotated

import typer

from ai_agent_orchestrator.agent import Agent, AgentEventType
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.protocol.messages import Message
from task_runner_app.llm import LMStudioClient
from task_runner_app.tools import build_tool_registry

app = typer.Typer(help="Run tasks with LM Studio and ai-agent-orchestrator.")

DEFAULT_WORKSPACE = Path(os.getenv("WORKSPACE_DIR", "workspace"))

SYSTEM_PROMPT = """You are a task runner assistant. Follow the protocol strictly.

You must respond ONLY with valid JSON of one of these forms:
{"type":"tool_call","tool_name":"...","args":{...}}
{"type":"final","content":"..."}

Available tools:
- files.read_text(path): Read a UTF-8 text file within the repo or workspace.
- files.list_dir(path): List directory contents within the repo or workspace.
- files.write_text(path, content): Write text to a file within the workspace only.
- text.search(path, query): Search for a string within a text file.
- tasks.add(title, notes, priority): Add a task entry to workspace/tasks.json.
- tasks.list(): List tasks from workspace/tasks.json.
"""


@app.command()
def task_runner(
    instruction: Annotated[str, typer.Argument(..., help="Instruction to execute")],
    workspace: Annotated[
        Path, typer.Option("--workspace", help="Workspace directory")
    ] = DEFAULT_WORKSPACE,
    max_steps: Annotated[
        int, typer.Option("--max-steps", help="Maximum tool steps")
    ] = 6,
) -> None:
    repo_root = Path.cwd().resolve()
    workspace_root = (
        (repo_root / workspace).resolve()
        if not workspace.is_absolute()
        else workspace.resolve()
    )
    workspace_root.mkdir(parents=True, exist_ok=True)

    memory = InMemoryMemory()
    memory.add(Message(role="system", content=SYSTEM_PROMPT))

    tools = build_tool_registry(repo_root, workspace_root)
    llm = LMStudioClient()
    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=max_steps)
    response = agent.run(instruction)

    typer.echo("Final Answer:\n" + response.content)
    typer.echo("\nExecution Trace:")
    for event in response.events:
        if event.type == AgentEventType.TOOL_CALL:
            typer.echo(f"- Tool call: {event.tool_name} {event.args}")
        elif event.type == AgentEventType.TOOL_RESULT:
            summary = (event.content or "")
            if len(summary) > 200:
                summary = summary[:200] + "..."
            typer.echo(f"  Result: {summary}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
