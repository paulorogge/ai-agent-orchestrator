# Streaming

Streaming is an optional, additive capability. It does not change the core JSON
protocol, tool-calling semantics, or sync behavior. If you never implement or
consume streaming, the agent loop and `Agent.run` / `Agent.run_async` remain
unchanged.

## Stable chunk shape

Streaming-capable providers implement `LLMStreamClient.stream` and yield
`StreamChunk` values with a stable, documented shape:

```python
@dataclass(frozen=True)
class StreamChunk:
    content: str
    is_final: bool = False
```

- `content` is incremental text output.
- `is_final` indicates the end of the stream; providers may set it to `True` on
  the last chunk.

This schema is stable and intended to be shared across adapters.

## Usage example

```python
from collections.abc import AsyncIterator

from ai_agent_orchestrator.llm import LLMStreamClient, StreamChunk
from ai_agent_orchestrator.protocol.messages import Message


class MyStreamingClient(LLMStreamClient):
    async def stream(self, conversation: list[Message]) -> AsyncIterator[StreamChunk]:
        yield StreamChunk(content="Hello ")
        yield StreamChunk(content="world", is_final=True)
```

Consumers can iterate over the stream:

```python
async for chunk in client.stream(conversation):
    print(chunk.content, end="")
    if chunk.is_final:
        break
```

## Compatibility notes

- Async and streaming are optional. The synchronous `LLMClient` contract and
  `Agent.run` remain the default entrypoint.
- The JSON protocol is unchanged: streaming does not add new message types.
- LM Studio integration is sync-only unless explicit async or streaming support
  is implemented in `src/task_runner_app/llm.py`.

## Non-goals

- No persistent memory. The in-memory buffer remains the default storage model.
- No tool restrictions beyond `max_steps`. Tools remain callable multiple times
  within a single run.
