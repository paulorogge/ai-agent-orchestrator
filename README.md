# ai-agent-orchestrator

Framework open-source em Python 3.11 para orquestração de agentes LLM com arquitetura limpa, extensibilidade e execução offline.

## Visão geral

O projeto fornece um núcleo de orquestração para conversas, ferramentas e roteamento de agentes, com protocolo de saída estruturada e um backend de LLM fake para testes offline.

## Design goals

- Clean Architecture + SOLID
- Tipagem estática e validação com Pydantic v2
- Sem dependência obrigatória de provedores LLM
- CLI simples para experimentar o loop de agente

## Quickstart

```bash
pip install -e ".[dev]"
```

```bash
ai-agent-orchestrator chat "Olá"
```

```bash
pytest
```

## Exemplos

```bash
python examples/basic_chat.py
python examples/tool_calling.py
python examples/routed_flow.py
```

## Protocolo de saída estruturada

Tool call:

```json
{
  "type": "tool_call",
  "tool_name": "math.add",
  "args": {"a": 2, "b": 3}
}
```

Final:

```json
{
  "type": "final",
  "content": "texto"
}
```
