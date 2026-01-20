import asyncio
import time

from ai_agent_orchestrator.agent import Agent
from ai_agent_orchestrator.memory.in_memory import InMemoryMemory
from ai_agent_orchestrator.tools.registry import ToolRegistry
from task_runner_app.llm import LMStudioClient


def _preview(text: str, limit: int = 80) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}…"


async def main() -> None:
    llm = LMStudioClient(timeout=120.0)
    agent = Agent(llm=llm, tools=ToolRegistry(), memory=InMemoryMemory(), max_steps=3)

    msg = (
        'Responda SOMENTE com JSON no formato: {"type":"final","content":"..."}.\n'
        "Conteúdo: escreva 12 linhas curtas numeradas (1..12)."
    )

    start = time.perf_counter()
    chunk_index = 0

    async for chunk in agent.stream_async(msg):
        if not chunk.text and not chunk.is_final:
            continue

        chunk_index += 1
        now = time.perf_counter()
        delta = now - start
        text = chunk.text
        text_len = len(text)
        preview = _preview(text)
        final_flag = "True" if chunk.is_final else "False"

        print(
            f"[{delta:7.3f}s] chunk#{chunk_index:02d} "
            f"len={text_len:03d} final={final_flag} | {preview}",
            flush=True,
        )

        if chunk.is_final:
            break


if __name__ == "__main__":
    asyncio.run(main())
