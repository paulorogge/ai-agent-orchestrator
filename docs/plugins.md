# Plugins (v0.2.0 scope)

## Definition

A plugin is an explicitly imported Python callable (a function or an object with a
`register()` method) that application code passes in directly. The plugin is
responsible for registering tools and, in future iterations, may optionally provide
adapter factories (such as a `Memory` factory).

## How plugins are applied

Plugins are applied explicitly by the host application; there is no discovery or
dynamic loading in the core library. The host code imports the plugin and calls it
(or calls its `register()` method) with the objects it wants to extend.

## Scope for v0.2.0

- Plugins can register tools with a `ToolRegistry`.
- Plugins may optionally provide a `Memory` factory later (tentative, not required
  for the first iteration).

## Non-goals

- No auto-discovery or entrypoints.
- No plugin base classes or lifecycle hooks.
- No changes to default runtime behavior or CLI behavior.

## Minimal pseudo-code example

```python
from ai_agent_orchestrator.tools import ToolRegistry
# from my_app.plugins import my_plugin

registry = ToolRegistry()
# Explicitly apply a plugin callable (function or object with register()).
# my_plugin(registry)
# or: my_plugin.register(registry)
```

Plugin shape (no implementation):

```python
# def my_plugin(registry: ToolRegistry) -> None: ...
# class MyPlugin:
#     def register(self, registry: ToolRegistry) -> None: ...
```
