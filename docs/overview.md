# Project Overview

## Project Charter

### Problem
Teams building agentic LLM systems often need a lightweight, provider-agnostic core for coordinating tools, routing, memory, and structured outputs without committing to a web framework or a hosted service.

### Audience
- Engineers building local prototypes and internal tools.
- Teams that need deterministic, offline testability.
- Libraries and platforms that want a clean orchestration core they can embed.

### Use cases
- Run agent loops with tool calling and structured responses.
- Route between multiple agents based on simple rules.
- Integrate custom tools and memory backends.
- Validate deterministic behavior via an offline `FakeLLM`.

### Non-goals
- Providing a FastAPI server or hosted service.
- Providing vendor-specific integrations by default.
- Delivering a full UI or productized application.

## Concepts

- **Agent**: Orchestrates the loop, manages conversation state, and delegates tool execution.
- **Tools**: Callable capabilities exposed to agents (e.g., math, retrieval, side effects).
- **ToolRegistry**: Catalog and dispatcher for tool definitions and executions.
- **Router**: Selects the next agent based on routing rules or signals.
- **Memory**: Persistence abstraction for conversation history.
- **Protocol**: JSON-structured outputs that describe tool calls and final responses.

## Walkthrough

1. **User message** enters the agent.
2. The agent requests an LLM completion and receives a structured JSON message.
3. If the message is a **tool_call**, the agent executes it via the ToolRegistry.
4. The tool returns a **tool_result** payload to the agent.
5. The agent sends the tool result back to the LLM and receives a **final** response.

```
user -> agent -> tool_call -> tool_result -> final
```
