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
- Provider-agnostic LLM interface (`LLMClient`) with optional async adapters.
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

- **Agent**: Runs a multi-step loop that parses structured outputs and executes
  tools until a final response or `max_steps` is reached. The same tool can be
  called multiple times within a single user instruction if the task requires it.
- **Tools**: Typed inputs via Pydantic; tools return string outputs.
- **ToolRegistry**: Registers tools and validates inputs before execution.
- **Router**: Simple rule-based routing between agents.
- **Memory**: Pluggable conversation storage (default: in-memory buffer).
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

Tool calls and final responses must follow this minimal JSON protocol. The
agent only acts on valid `tool_call` or `final` objects; anything else (including
non-JSON or invalid JSON) is treated as a plain final response and does not
trigger tool execution. When using LM Studio, the task runner may issue a
single corrective retry if the model violates the protocol (this retry is not
guaranteed or recursive).

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
  Infinite loops are prevented via `max_steps`, not by restricting tool usage.

## Async + streaming (optional)

The core loop remains synchronous, but `Agent.run_async` provides an async-compatible
entrypoint that preserves the same tool-call protocol and behavior as `run`. If the
LLM client already exposes an async `generate`, it is awaited directly; otherwise the
sync client is executed in a worker thread for compatibility. Async support is
additive and optional: you can keep using `run` with the same protocol semantics.

Streaming is also optional via `LLMStreamClient` and the stable `StreamChunk` shape.
It does not change the JSON protocol or the agent loop; it is an opt-in interface
for providers that implement streaming. See [docs/streaming.md](docs/streaming.md)
for the chunk schema and usage examples.

Non-goals remain unchanged: there is no persistent memory and no restriction on
tool usage beyond `max_steps`.

## Multi-step example

A single instruction can require multiple tool calls. For example, in the task
runner the agent can add a task and then list tasks before responding:

1. `{"type":"tool_call","tool_name":"tasks.add","args":{"title":"Draft launch email","notes":"Add outline","priority":"high"}}`
2. `{"type":"tool_call","tool_name":"tasks.list","args":{}}`
3. `{"type":"final","content":"Added the task and listed current tasks."}`

## Memory model

The current `Memory` implementation is a simple conversation buffer. It stores
messages in-order and returns the full conversation to the agent. It does not
summarize, prune, persist, or reason over history. This is an intentional design
choice to keep separation of concerns, deterministic behavior, testability, and
future extensibility.

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

Required environment variables:

- `LMSTUDIO_MODEL` (required)
- `LMSTUDIO_BASE_URL` (optional, defaults to `http://localhost:1234/v1`)
- `LMSTUDIO_API_KEY` (optional, for servers that require auth)
- `WORKSPACE_DIR` (optional, workspace path for task runner tools)

The task runner calls LM Studio through its OpenAI-compatible API, but the core
orchestrator remains provider-agnostic via the synchronous `LLMClient` interface
with additive async adapters when needed. See
[docs/task-runner.md](docs/task-runner.md) for setup details. The task runner
enforces the same JSON protocol and uses the core agent loop with tool calls.
LM Studio support is sync-only unless explicit async or streaming support is
implemented in `src/task_runner_app/llm.py`.

## Testing

```bash
pytest
```

If you need annotated tags locally or in CI for release automation, run:

```bash
git fetch --tags
```

## Docs

- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Observability](docs/observability.md)
- [Plugins](docs/plugins.md)
- [Roadmap](docs/roadmap.md)
- [Streaming](docs/streaming.md)
