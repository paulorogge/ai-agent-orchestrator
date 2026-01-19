# Architecture

## Components

- **Agent**: Execution loop, conversation history, and tool coordination.
- **LLMClient**: Abstract synchronous interface for generating responses (async adapters are additive).
- **FakeLLM**: Deterministic implementation for offline environments.
- **ToolRegistry**: Tool registration and execution.
- **Memory**: Message storage abstraction (default: in-memory list).
- **Router**: Agent selection via simple rules.
- **Protocol**: Structured message models and JSON outputs.

## Core flow

```
+---------+       +-----------+       +-------------+       +-----------+
|  User   |  -->  |   Agent   |  -->  | LLMClient   |  -->  |  Output   |
+---------+       +-----------+       +-------------+       +-----------+
                       |                       |
                       | tool_call             |
                       v                       |
                  +---------+                  |
                  |  Tool   |------------------+
                  +---------+
```

1. User sends a message.
2. Agent appends the message to memory.
3. LLMClient generates a structured JSON response.
4. Agent interprets the output and executes tools as needed.
5. Agent returns a final response after tool calls complete or `max_steps` is
   reached. Repeating the same tool within a single instruction is allowed when
   required by the task.

## Memory behavior

Memory exists to abstract conversation history storage and allow future adapters.
Today, `InMemoryMemory` stores messages in a simple in-memory list and returns a
copy of that list. There is no persistence, summarization, or pruning, and each
CLI run starts with a fresh memory instance unless the application reuses one.
It is not a vector store, not long-term knowledge, and not cross-run storage.
