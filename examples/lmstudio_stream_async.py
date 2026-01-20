import asyncio

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.builtin.echo_tool import EchoTool
from ai_agent_orchestrator.tools.registry import ToolRegistry
from task_runner_app.llm import LMStudioClient


async def main() -> None:
    llm = LMStudioClient(timeout=120.0)
    memory = InMemoryMemory()
    tools = ToolRegistry()
    tools.register(EchoTool())

    agent = Agent(llm=llm, tools=tools, memory=memory, max_steps=3)

    msg = (
        'Responda SOMENTE com JSON no formato: {"type":"final","content":"..."}.\n'
        "Conteúdo: escreva uma frase curta dizendo que stream_async funciona."
    )

    full = ""
    async for chunk in agent.stream_async(msg):
        print(chunk.text, end="", flush=True)
        full += chunk.text
        if chunk.is_final:
            print("\n\n--- FINAL (buffer) ---")
            print(full)


if __name__ == "__main__":
    asyncio.run(main())
