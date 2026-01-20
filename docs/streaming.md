# Streaming

The agent supports streaming model output via `Agent.stream_async(...)`. This async generator
lets you render incremental output while the agent buffers the full model response for
protocol parsing and tool execution.

Streaming can be real-time when the configured provider exposes a streaming-capable
`stream(...)` method; otherwise the agent falls back to a buffered response.

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

## Provider notes

- LM Studio can now stream over SSE (OpenAI-compatible) when the server has streaming
  enabled. If streaming is not available, the agent uses the buffered fallback.

## LM Studio examples

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
