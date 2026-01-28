"""Optional LM Studio integration example.

Requires a running LM Studio server plus LMSTUDIO_BASE_URL and LMSTUDIO_MODEL
(LMSTUDIO_API_KEY optional). Not exercised in CI or offline environments.
"""

import asyncio

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.registry import ToolRegistry
from task_runner_app.llm import LMStudioClient


async def main() -> None:
    llm = LMStudioClient(timeout=120.0)  # lê LMSTUDIO_MODEL e LMSTUDIO_BASE_URL
    memory = InMemoryMemory()
    tools = ToolRegistry()
    tools.register(EchoTool())

    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=3)

    # Dica: pedir explicitamente o protocolo para evitar retry
    msg = (
        'Responda SOMENTE com JSON no formato: {"type":"final","content":"..."}.\n'
        "Conteúdo: diga apenas 'FUNCIONOU'."
    )
    resp = await agent.run_async(msg)
    print(resp.content)


if __name__ == "__main__":
    asyncio.run(main())
