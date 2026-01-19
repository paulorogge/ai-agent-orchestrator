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
- Minimal scope: emit a small, stable set of structured events/spans from the agent loop.
- Minimal scope: document extension points for consuming events (no built-in exporters).
- Non-goal: adding new observability backends or metrics dashboards.
- Non-goal: changing core agent behavior or tool execution semantics.
- Acceptance: events/spans can be captured in tests via a simple hook with deterministic fields.
- Acceptance: docs describe the event payload shape and where hooks are invoked.

### v0.4.0 Async + streaming (planned)
- Minimal scope: async-compatible agent loop entrypoint with parity to sync behavior.
- Minimal scope: optional streaming interface for incremental model output.
- Non-goal: reworking all tools to be async-first or adding new streaming protocols.
- Non-goal: guaranteeing streaming support across all LLM providers.
- Non-goal: adding persistent memory or restricting tool usage beyond `max_steps`.
- Acceptance: async loop passes existing tests (or equivalent async variants) without behavior drift.
- Acceptance: streaming path emits incremental chunks in a documented, stable shape
  (see `docs/streaming.md`).

### v0.5.x+ Persistent memory adapters exploration (tentative)
- Minimal scope: outline a thin adapter interface for persistence experiments.
- Minimal scope: one example adapter behind a clearly experimental flag or namespace.
- Non-goal: committing to a long-term storage backend or migration strategy.
- Non-goal: expanding memory features beyond what exists today.
- Acceptance: adapter interface is documented with explicit stability caveats.
- Acceptance: example adapter can be enabled in a demo/test without affecting defaults.

### v1.0.0 Stable API + compatibility guarantees (planned)
- Stabilized public API surface.
- Versioning and compatibility commitments.
