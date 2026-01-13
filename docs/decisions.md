# Decisions

## Key Decisions

1. **Core is a library, not a web framework dependency**
   - The orchestration core is framework-agnostic and does not depend on FastAPI or any server runtime.

2. **FakeLLM for offline repeatability**
   - Deterministic, local execution is a priority for tests, demos, and reproducible behavior.

3. **JSON structured outputs for determinism**
   - Tool calls and final responses are encoded as JSON to make tool execution predictable and machine-verifiable.

4. **Python 3.11+ support policy**
   - The project targets modern Python features and maintains a minimal support window.

5. **Strict typing + CI choices**
   - Static typing and clear boundaries are enforced, supported by CI checks and a typed codebase.
