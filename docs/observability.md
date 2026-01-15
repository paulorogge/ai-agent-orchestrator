# Observability

The agent loop can emit a small, stable set of structured events. You provide a sink to consume
those events (for logging, tests, or custom exporters). No backends or exporters are built in.
Events are emitted only when an event_sink is provided.

## Event envelope

Each event is JSON-safe and follows this envelope:

```json
{
  "name": "agent.tool.finished",
  "time_ms": 1736950000123,
  "run_id": "run_...",
  "step": 3,
  "span_id": "sp_...",
  "parent_span_id": "sp_...",
  "data": {}
}
```

## Event names

- `agent.run.started`
- `agent.step.started`
- `agent.model.requested`
- `agent.model.responded`
- `agent.output.parsed`
- `agent.tool.started`
- `agent.tool.finished`
- `agent.step.finished`
- `agent.run.finished`
- `agent.run.failed`

## Event data fields

Fields are intentionally minimal and safe. Raw prompts, memory contents, tool argument values,
and tool results are **not** emitted by default.

- `agent.run.started`
  - `max_steps: int`
- `agent.step.started`
  - `input_messages_count: int`
- `agent.model.requested`
  - `message_count: int`
  - `tool_count: int` (optional)
- `agent.model.responded`
  - `response_type: str` (e.g. "text")
  - `raw_length: int`
- `agent.output.parsed`
  - `parsed_type: "tool_call" | "final" | "invalid"`
  - `is_valid: bool`
  - `tool_name: str` (present only when parsed_type == "tool_call" and is_valid == True)
  - `args_keys: list[str]` (present only when parsed_type == "tool_call" and is_valid == True)
- `agent.tool.started`
  - `tool_name: str`
  - `args_keys: list[str]`
  - `args_count: int`
- `agent.tool.finished`
  - `tool_name: str`
  - `status: "ok" | "error"`
  - `error_type: str | None`
- `agent.step.finished`
  - `outcome: "tool_call" | "final" | "max_steps" | "error"`
- `agent.run.finished`
  - `steps_used: int`
  - `outcome: "final" | "max_steps"`
- `agent.run.failed`
  - `error_type: str`

## Hook locations

Hooks are emitted at the boundaries of the agent loop:

1. Run start/end/failure
2. Step start/end
3. Model request/response
4. Output parse
5. Tool start/finish (if tool call)

`agent.run.finished` is emitted only on non-exception completion; failures emit `agent.run.failed` instead.

## Example sinks

### JSONL print sink

```python
from ai_agent_orchestrator.observability.events import AgentEvent


def jsonl_sink(event: AgentEvent) -> None:
    # Tip: convert the event to a JSON dict before writing JSONL, if desired.
    print(event)
```

### List collector sink

```python
from ai_agent_orchestrator.observability.events import ListEventSink

sink = ListEventSink()
# pass sink into Agent.run(..., event_sink=sink)
print(sink.events)
```
