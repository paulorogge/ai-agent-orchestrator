# Changelog

## [Unreleased]

## [0.4.0]
### Added
- Agent.run_async.
- Streaming entrypoint with compatibility notes: protocol unchanged, sync tools compatible,
  memory remains non-persistent.

### Non-goals
- Protocol remains unchanged.
- Sync tools remain compatible.
- Memory remains non-persistent.

## [0.3.0]
### Added
- Opt-in structured observability events emitted from the agent loop.
- Deterministic testing via injectable clock, run_id, and span_id factories.
- No built-in exporters/backends.

## [0.2.0] - 2026-01-15
### Added
- Explicit callable tool plugin model.
- Plugin helper with unit tests.
- Runnable example.
- Cross-platform smoke test.

### Changed
- CLI cleanup for iter_tools and python -m support.

## [0.1.0] - 2026-01-15
- Initial open-source release.
