# Roadmap

## Milestones

### v0.1.0 MVP (released)
- Core agent loop with tool calling.
- Router and memory abstractions.
- Deterministic `FakeLLM` for offline usage.

### v0.2.0 Explicit tool plugin callable model (in development)
- Explicit, opt-in callable model for tools only.
- No discovery, lifecycle, or plugin framework.
- Example + tests, including a cross-platform smoke test.
- CLI uses `ToolRegistry.iter_tools()` (no direct `_tools` access).

### v0.3.0 Observability hooks / tracing improvements (planned)
- Structured events, spans, and trace-friendly hooks.
- Debugging and metrics integration points.

### v0.4.0 Async + streaming (planned)
- Async agent loop support.
- Streaming outputs for intermediate tokens or tool calls.

### v0.5.x+ Persistent memory adapters exploration (tentative)
- Explore persistent memory adapters (no commitments).

### v1.0.0 Stable API + compatibility guarantees (planned)
- Stabilized public API surface.
- Versioning and compatibility commitments.
