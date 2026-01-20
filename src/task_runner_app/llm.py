from __future__ import annotations

import importlib
import importlib.util
import json
import os
from dataclasses import dataclass
from typing import Any, AsyncIterator, Sequence, cast

from ai_agent_orchestrator.llm import LLMClient, LLMStreamChunk
from ai_agent_orchestrator.protocol.messages import Message

DEFAULT_BASE_URL = "http://localhost:1234/v1"
DEFAULT_TIMEOUT = 30.0
PROTOCOL_REMINDER = (
    "Your response did not follow the required JSON protocol. "
    "Respond ONLY with a JSON object of the form "
    '{"type":"tool_call","tool_name":"...","args":{...}} '
    "or {\"type\":\"final\",\"content\":\"...\"}."
)


@dataclass
class LMStudioConfig:
    base_url: str = DEFAULT_BASE_URL
    model: str = ""
    api_key: str | None = None
    timeout: float = DEFAULT_TIMEOUT


class LMStudioClient(LLMClient):
    """LLM client for LM Studio's OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        client: Any | None = None,
        async_client: Any | None = None,
    ) -> None:
        if importlib.util.find_spec("httpx") is None:
            raise RuntimeError(
                "httpx is required for LM Studio support. Install with: "
                "pip install .[lmstudio]"
            )
        httpx_module = importlib.import_module("httpx")
        resolved_base_url = base_url or os.getenv("LMSTUDIO_BASE_URL") or DEFAULT_BASE_URL
        resolved_model = model or os.getenv("LMSTUDIO_MODEL") or ""
        if not resolved_model:
            raise ValueError("LMSTUDIO_MODEL is required to call LM Studio")
        resolved_api_key = api_key or os.getenv("LMSTUDIO_API_KEY")

        self._config = LMStudioConfig(
            base_url=resolved_base_url,
            model=resolved_model,
            api_key=resolved_api_key,
            timeout=timeout,
        )
        self._httpx = httpx_module
        self._client = client or httpx_module.Client(
            base_url=self._config.base_url,
            timeout=httpx_module.Timeout(self._config.timeout),
        )
        self._async_client = async_client

    def generate(self, conversation: Sequence[Message]) -> str:
        raw = self._request(conversation)
        return self._ensure_protocol_with_retry(raw, conversation)

    def _ensure_protocol_with_retry(
        self, raw_text: str, conversation: Sequence[Message]
    ) -> str:
        if _is_protocol_compliant(raw_text):
            return raw_text

        corrected_conversation = list(conversation) + [
            Message(role="system", content=PROTOCOL_REMINDER)
        ]
        return self._request(corrected_conversation)

    def _request(self, conversation: Sequence[Message]) -> str:
        payload = {
            "model": self._config.model,
            "messages": [_message_to_dict(msg) for msg in conversation],
        }
        headers = {}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"

        try:
            response = self._client.post(
                "/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        except self._httpx.HTTPError as exc:
            raise RuntimeError(f"LM Studio request failed: {exc}") from exc

        data = response.json()
        try:
            return cast(str, data["choices"][0]["message"]["content"])
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LM Studio response was missing message content") from exc

    async def stream(
        self, conversation: Sequence[Message]
    ) -> AsyncIterator[LLMStreamChunk]:
        payload = {
            "model": self._config.model,
            "messages": [_message_to_dict(msg) for msg in conversation],
            "stream": True,
        }
        headers = {}
        if self._config.api_key:
            headers["Authorization"] = f"Bearer {self._config.api_key}"
        buffer_parts: list[str] = []

        async def _stream_with_client(client: Any) -> AsyncIterator[LLMStreamChunk]:
            try:
                async with client.stream(
                    "POST",
                    "/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self._httpx.Timeout(self._config.timeout),
                ) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        data = line[len("data:") :].strip()
                        if not data:
                            continue
                        if data == "[DONE]":
                            return
                        try:
                            event = json.loads(data)
                        except json.JSONDecodeError as exc:
                            raise RuntimeError(
                                "LM Studio stream event was not valid JSON: "
                                f"{data}"
                            ) from exc
                        try:
                            delta = event["choices"][0].get("delta", {})
                        except (KeyError, IndexError, TypeError) as exc:
                            raise RuntimeError(
                                "LM Studio stream event was missing delta content"
                            ) from exc
                        text = delta.get("content")
                        if text is None:
                            continue
                        text_value = cast(str, text)
                        buffer_parts.append(text_value)
                        yield LLMStreamChunk(content=text_value)
            except self._httpx.HTTPError as exc:
                raise RuntimeError(f"LM Studio stream request failed: {exc}") from exc

        if self._async_client is not None:
            async for chunk in _stream_with_client(self._async_client):
                yield chunk
        else:
            async with self._httpx.AsyncClient(
                base_url=self._config.base_url,
                timeout=self._httpx.Timeout(self._config.timeout),
            ) as client:
                async for chunk in _stream_with_client(client):
                    yield chunk

        buffer_text = "".join(buffer_parts)
        if _is_protocol_compliant(buffer_text):
            yield LLMStreamChunk(content="", is_final=True)
            return

        corrected_text = self._ensure_protocol_with_retry(buffer_text, conversation)
        if corrected_text != buffer_text:
            yield LLMStreamChunk(content=corrected_text, is_final=True)
        else:
            yield LLMStreamChunk(content="", is_final=True)


def _message_to_dict(message: Message) -> dict[str, str]:
    payload = {"role": message.role, "content": message.content}
    if message.name:
        payload["name"] = message.name
    return payload


def _is_protocol_compliant(raw: str) -> bool:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False

    if not isinstance(data, dict):
        return False

    message_type = data.get("type")
    if message_type == "tool_call":
        tool_name = data.get("tool_name")
        args = data.get("args", {})
        return isinstance(tool_name, str) and isinstance(args, dict)
    if message_type == "final":
        return "content" in data

    return False
