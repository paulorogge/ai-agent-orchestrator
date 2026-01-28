"""Optional LM Studio integration example.

Requires a running LM Studio server plus LMSTUDIO_BASE_URL and LMSTUDIO_MODEL
(LMSTUDIO_API_KEY optional). Not exercised in CI or offline environments.
"""

import asyncio
import time

from ai_agent_orchestrator.protocol.messages import Message
from task_runner_app.llm import LMStudioClient


async def main() -> None:
    llm = LMStudioClient(timeout=120.0)

    msg = (
        'Responda SOMENTE com JSON no formato: {"type":"final","content":"..."}.\n'
        "Conteúdo: escreva 30 linhas numeradas (1..30), uma por linha, com frases curtas."
    )

    t0 = time.perf_counter()
    first = None

    conversation = [Message(role="user", content=msg)]

    async for chunk in llm.stream(conversation):
        if chunk.content and first is None:
            first = time.perf_counter()
            print(f"\n[first chunk after] {first - t0:.3f}s\n")

        if chunk.content:
            print(chunk.content, end="", flush=True)

        if chunk.is_final:
            tf = time.perf_counter()
            if first is None:
                first = tf
                print(f"\n[first chunk after] {first - t0:.3f}s\n")
            print(f"\n\n[final after] {tf - t0:.3f}s")
            break


if __name__ == "__main__":
    asyncio.run(main())
