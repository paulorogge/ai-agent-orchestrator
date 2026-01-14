from __future__ import annotations

import importlib
import importlib.util
import json
import os
from dataclasses import dataclass
from typing import Any, Sequence

from ai_agent_orchestrator.llm import LLMClient
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
    ) -> None:
        if importlib.util.find_spec("httpx") is None:
            raise RuntimeError(
                "httpx is required for LM Studio support. Install with: "
                'pip install -e ".[lmstudio]"'
            )
        httpx_module = importlib.import_module("httpx")
        resolved_base_url = base_url or os.getenv("LMSTUDIO_BASE_URL", DEFAULT_BASE_URL)
        resolved_model = model or os.getenv("LMSTUDIO_MODEL", "")
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

    def generate(self, conversation: Sequence[Message]) -> str:
        raw = self._request(conversation)
        if _is_protocol_compliant(raw):
            return raw

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
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("LM Studio response was missing message content") from exc


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
