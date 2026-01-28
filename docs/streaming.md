# Streaming

The agent supports streaming model output via `Agent.stream_async(...)`. This async generator
lets you render incremental output while the agent buffers the full model response for
protocol parsing and tool execution. The buffering step means the agent-level stream is a
safe, parsed view of the final response rather than a real-time token stream.

Streaming output from the agent is buffered: the agent always collects the full model
response, parses it, and then emits chunks that subdivide the final response content. If
you need the full response, you must concatenate all `chunk.text` values in order.

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

- `text`: a slice of the final response content for the current step.
- `step`: the agent step that produced the chunk.
- `is_final`: `True` only when the agent has produced a final response (or the max-steps
  fallback). The final chunk's `text` is the last slice of the response, not the full
  response content. Consumers should concatenate all chunks to reconstruct the full text.

## Usage

```python
from ai_agent_orchestrator.agent import Agent

async def stream(agent: Agent, prompt: str) -> str:
    full_text = ""
    async for chunk in agent.stream_async(prompt):
        full_text += chunk.text
        if chunk.is_final:
            break
    return full_text
```

## Protocol safety

Streaming is incremental, but tool calls are still executed only after the full model
response is buffered and parsed. This preserves the existing tool-call protocol and ensures
that tools never run on partial output.

## Provider notes

Provider-level streaming can be real-time, but the agent stream stays buffered. The agent
waits for the provider output, parses it, and then emits sliced chunks based on the final
response content.

- LM Studio can stream over SSE (OpenAI-compatible) when the server has streaming enabled.
  The agent still buffers the response before emitting `StreamChunk` values.
- `LMStudioClient.stream` preserves the same protocol compliance retry as `generate()`
  (one retry) when responses are not valid tool-call/final JSON.

## LM Studio examples

> These examples are optional, best-effort integrations that require a running LM Studio
> server. They are not run in CI or offline environments.

Set the environment variables (PowerShell examples):

```powershell
$env:LMSTUDIO_BASE_URL = "http://localhost:1234/v1"
$env:LMSTUDIO_MODEL = "your-model-name"
$env:LMSTUDIO_API_KEY = "optional"
```

Run the examples:

```powershell
python examples/lmstudio_run_async.py
python examples/lmstudio_stream_async.py
python examples/lmstudio_stream_timing.py
python examples/lmstudio_stream_visual.py
```

If you want to confirm the SSE stream manually, use `curl.exe` with a JSON file:

```powershell
@'
{
  "model": "your-model-name",
  "messages": [
    { "role": "user", "content": "Say hello in one short sentence." }
  ],
  "stream": true
}
'@ | Set-Content -Path .\lmstudio_request.json -Encoding UTF8

curl.exe http://localhost:1234/v1/chat/completions `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $env:LMSTUDIO_API_KEY" `
  --data-binary "@lmstudio_request.json"
```

If you are not using an API key, omit the `Authorization` header.
