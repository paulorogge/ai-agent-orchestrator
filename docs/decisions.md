# Decisions

## Key Decisions

1. **Core is a library, not a web framework dependency**
   - The orchestration core is framework-agnostic and does not depend on a
     server runtime.

2. **Provider-agnostic LLM boundary**
   - `LLMClient` is the only required integration point; LM Studio is an
     optional adapter via an OpenAI-compatible API for the task runner.

3. **Deterministic `FakeLLM` for offline repeatability**
   - Local, predictable execution is prioritized for tests, demos, and
     reproducible behavior.

4. **Strict JSON protocol for tool calls**
   - Tool calls and final responses are encoded as JSON to make execution
     predictable and machine-verifiable. Non-JSON outputs are treated as final
     responses; the LM Studio task runner may retry once with a protocol reminder
     when output is non-compliant.

5. **Simple memory by default**
   - The default memory stores an in-memory list of messages without persistence
     or summarization to keep the core deterministic and extensible.

6. **Loop safety via `max_steps`**
   - Infinite loops are prevented by a maximum number of steps, not by limiting
     tool reuse or forbidding multi-step tasks.

7. **Python 3.11+ support policy**
   - The project targets modern Python features and maintains a minimal support
     window.
