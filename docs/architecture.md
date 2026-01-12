# Architecture

## Componentes

- **Agent**: loop de execução, histórico de conversas e coordenação de ferramentas.
- **LLMClient**: interface abstrata para geração de respostas.
- **FakeLLM**: implementação determinística para ambientes offline.
- **ToolRegistry**: registro e execução de ferramentas.
- **Memory**: abstração de armazenamento de mensagens.
- **Router**: seleção de agentes por regras simples.
- **Protocol**: modelos de mensagens e saída estruturada.

## Fluxo principal

```
+---------+       +-----------+       +-------------+       +-----------+
|  User   |  -->  |   Agent   |  -->  | LLMClient   |  -->  |  Output   |
+---------+       +-----------+       +-------------+       +-----------+
                       |                       |
                       | tool_call             |
                       v                       |
                  +---------+                  |
                  |  Tool   |------------------+
                  +---------+
```

1. Usuário envia mensagem.
2. Agent adiciona a mensagem à memória.
3. LLMClient gera uma resposta estruturada.
4. Agent interpreta o output e executa ferramentas quando necessário.
5. Agent retorna uma resposta final com eventos intermediários.
