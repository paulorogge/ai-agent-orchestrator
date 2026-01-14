# ai-agent-orchestrator

Provider-agnostic Python library for orchestrating LLM agents with tools, routing, memory, and structured outputs. It is a core orchestration framework, not a toy agent library.

## What this is

- A core orchestration framework that applies Clean Architecture to LLM agent systems.
- A deterministic, offline-first runtime via `FakeLLM` for reproducible execution and tests.
- A set of independent components—Agent, Router, Tools, Memory, Protocol—designed with explicit boundaries and separation of concerns.

## What this is not

- NOT a FastAPI application.
- NOT a hosted service.
- NOT vendor-locked to any LLM provider.

## Design goals

- Clean Architecture at the core.
- SOLID principles across components.
- Provider-agnostic LLM abstraction.
- Deterministic structured outputs for predictable tool-calling.
- Testability and offline execution.
- Explicit boundaries between orchestration logic and external integrations.

## Quickstart

```bash
pip install -e ".[dev]"
```

## LM Studio Task Runner

Looking for the LM Studio-powered task runner CLI? See
[docs/task-runner.md](docs/task-runner.md).

```bash
ai-agent-orchestrator run-example --name basic_chat
ai-agent-orchestrator run-example --name tool_calling
ai-agent-orchestrator run-example --name routed_flow
```

```bash
pytest
```

## Structured output protocol (example)

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

## Docs

- [Overview](docs/overview.md)
- [Architecture](docs/architecture.md)
- [Decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)
