# ai-agent-orchestrator

A Clean Architecture framework for orchestrating LLM agents with tools, routing,
memory, and structured JSON outputs. It ships with a deterministic `FakeLLM`
for offline runs, plus an optional LM Studio-powered task runner CLI.

## What this is

- A composable orchestration core with explicit boundaries (Agent, Router, Tools,
  Memory, Protocol).
- A deterministic, offline-first runtime via `FakeLLM` for repeatable examples
  and tests.
- A small, testable surface area meant to be embedded in other apps.

## What this is not

- Not a FastAPI app or a hosted service.
- Not a full product or UI.
- Not a vendor-specific SDK (LM Studio support is optional and isolated in the
  task runner).

## Design goals

- Clean Architecture and SOLID-friendly components.
- Provider-agnostic LLM interface (`LLMClient`).
- Structured outputs with a minimal JSON protocol.
- Testability, deterministic execution, and clear error boundaries.

## Requirements

- Python 3.11+

## Install

```bash
pip install -e ".[dev]"
```

For LM Studio support (task runner only):

```bash
pip install -e ".[dev,lmstudio]"
```

## Core concepts

- **Agent**: Runs a loop that parses structured outputs and executes tools.
- **Tools**: Typed inputs via Pydantic; tools return string outputs.
- **ToolRegistry**: Registers tools and validates inputs before execution.
- **Router**: Simple rule-based routing between agents.
- **Memory**: Pluggable conversation storage (default: in-memory).
- **Protocol**: JSON outputs with `tool_call` and `final` message types.

## Structured output protocol

Tool call:

```json
{
  "type": "tool_call",
  "tool_name": "math.add",
  "args": {
    "a": 2,
    "b": 3
  }
}
```

Final:

```json
{
  "type": "final",
  "content": "result is 5"
}
```

If a model returns non-JSON output, the agent treats it as a final response.

## Quickstart (library)

```python
from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.llm import FakeLLM
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.builtin.math_tool import MathAddTool
from ai_agent_orchestrator.tools.registry import ToolRegistry

llm = FakeLLM()
memory = InMemoryMemory()
tools = ToolRegistry()
tools.register(MathAddTool())
agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=5)

response = agent.run("Compute 2 + 3")
print(response.content)
```

Notes:

- Built-in tools include `math.add` and `echo` (see `ai-agent-orchestrator list-tools`).
- The agent stops after `max_steps` tool iterations and returns a fallback message.

## CLI examples

Run packaged examples:

```bash
ai-agent-orchestrator run-example --name basic_chat
ai-agent-orchestrator run-example --name tool_calling
ai-agent-orchestrator run-example --name routed_flow
```

List built-in tools:

```bash
ai-agent-orchestrator list-tools
```

## LM Studio task runner

This repo also includes a task runner CLI that talks to the LM Studio
OpenAI-compatible API.

```bash
task-runner "Add a high priority task to draft the launch email."
```

See [docs/task-runner.md](docs/task-runner.md) for setup and environment
variables. The task runner enforces the same JSON protocol and uses the core
agent loop with tool calls.

## Testing

```bash
pytest
```

## Docs

- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)
