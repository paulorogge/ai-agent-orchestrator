# Streaming

The agent supports streaming model output via `Agent.stream_async(...)`. This async generator
lets you render incremental output while the agent buffers the full model response for
protocol parsing and tool execution.

## StreamChunk shape

`Agent.stream_async(...)` yields `StreamChunk` values with a stable shape:

```python
from ai_agent_orchestrator.streaming import StreamChunk

StreamChunk(
    text="partial text",
    step=1,
    is_final=False,
)
```

Fields:

- `text`: the raw incremental model text for the current step.
- `step`: the agent step that produced the chunk.
- `is_final`: `True` only when the agent has produced a final response (or the max-steps
  fallback). The final chunk's `text` contains the final response content.

## Usage

```python
from ai_agent_orchestrator.agent import Agent

async def stream(agent: Agent, prompt: str) -> str:
    full_text = ""
    async for chunk in agent.stream_async(prompt):
        if chunk.is_final:
            return chunk.text
        full_text += chunk.text
    return full_text
```

## Protocol safety

Streaming is incremental, but tool calls are still executed only after the full model
response is buffered and parsed. This preserves the existing tool-call protocol and ensures
that tools never run on partial output.
