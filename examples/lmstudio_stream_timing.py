import asyncio
import time

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.registry import ToolRegistry
from task_runner_app.llm import LMStudioClient


async def main() -> None:
    llm = LMStudioClient()
    agent = Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory(), max_steps=3)

    msg = (
        'Responda SOMENTE com JSON no formato: {"type":"final","content":"..."}.\n'
        "Conteúdo: escreva 30 linhas numeradas (1..30), uma por linha, com frases curtas."
    )

    t0 = time.perf_counter()
    first = None
    full = ""

    async for chunk in agent.stream_async(msg):
        if first is None:
            first = time.perf_counter()
            print(f"\n[first chunk after] {first - t0:.3f}s\n")

        print(chunk.text, end="", flush=True)
        full += chunk.text

        if chunk.is_final:
            tf = time.perf_counter()
            print(f"\n\n[final after] {tf - t0:.3f}s")
            break


if __name__ == "__main__":
    asyncio.run(main())
