"""Local llama.cpp HTTP adapter for Phase 2.

The adapter uses llama.cpp's OpenAI-compatible chat endpoint. Role messages
are deliberately sent unchanged so the llama.cpp server can use the selected
GGUF model's embedded chat template or its explicitly configured
``--chat-template``; this client does not hard-code a Qwen or other template.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from typing import Any, Protocol

import httpx

from app.config import Settings
from app.models.schemas import ChatMessage


logger = logging.getLogger("aura.llm")


class LLMError(RuntimeError):
    """Base class for safe, user-facing local inference failures."""


class LLMUnavailableError(LLMError):
    """The local model server could not be reached or is not ready."""


class LLMResponseError(LLMError):
    """The local model server returned an unusable response."""


class AsyncPostClient(Protocol):
    async def post(self, url: str, **kwargs: Any) -> httpx.Response: ...


class LLMService:
    """Call a local llama.cpp server without owning conversation persistence."""

    def __init__(
        self,
        settings: Settings,
        http_client: AsyncPostClient | None = None,
    ) -> None:
        self.settings = settings
        self._http_client = http_client

    @property
    def endpoint_url(self) -> str:
        endpoint = self.settings.llm_chat_endpoint
        if endpoint.startswith("http://") or endpoint.startswith("https://"):
            return endpoint
        return f"{self.settings.llm_server_url}/{endpoint.lstrip('/')}"

    def build_messages(
        self,
        message: str,
        history: Sequence[ChatMessage] = (),
    ) -> list[dict[str, str]]:
        """Build a bounded prompt from the configured fictional character."""

        system_prompt = self._load_character_prompt()
        context_limit = max(1024, self.settings.llm_context_size * 4)
        prompt_mode = self.settings.llm_system_prompt_mode.strip().lower()
        if prompt_mode not in {"system", "merge_user", "omit"}:
            logger.warning("Unknown system prompt mode; using system role")
            prompt_mode = "system"
        messages: list[dict[str, str]] = []
        if prompt_mode == "system":
            messages.append({"role": "system", "content": system_prompt})

        # Keep the newest turns while leaving room for the current user turn.
        selected: list[ChatMessage] = []
        used_chars = len(system_prompt) + len(message)
        for item in reversed(history):
            item_chars = len(item.content)
            if len(selected) >= self.settings.max_history_messages:
                break
            if used_chars + item_chars > context_limit:
                break
            selected.append(item)
            used_chars += item_chars

        conversation = [
            {"role": item.role, "content": item.content}
            for item in reversed(selected)
        ]
        conversation.append({"role": "user", "content": message})
        if prompt_mode == "merge_user":
            prefix = f"{system_prompt}\n\n"
            for index, item in enumerate(conversation):
                if item["role"] == "user":
                    conversation[index] = {
                        "role": "user",
                        "content": prefix + item["content"],
                    }
                    break
        messages.extend(conversation)
        return messages

    async def generate(self, messages: Sequence[dict[str, str]]) -> str:
        """Generate one response or raise without fabricating fallback text."""

        payload: dict[str, Any] = {
            "messages": list(messages),
            "temperature": self.settings.llm_temperature,
            "top_p": self.settings.llm_top_p,
            "max_tokens": self.settings.llm_max_tokens,
            "stream": False,
        }
        if self.settings.llm_model_name:
            payload["model"] = self.settings.llm_model_name

        try:
            if self._http_client is not None:
                response = await self._http_client.post(
                    self.endpoint_url,
                    json=payload,
                    timeout=self.settings.llm_timeout_seconds,
                )
            else:
                async with httpx.AsyncClient(
                    timeout=self.settings.llm_timeout_seconds
                ) as client:
                    response = await client.post(self.endpoint_url, json=payload)
        except (httpx.TimeoutException, httpx.NetworkError, httpx.ProtocolError) as exc:
            logger.warning("Local llama.cpp request failed: %s", type(exc).__name__)
            raise LLMUnavailableError("The local model server is unavailable") from exc
        except httpx.HTTPError as exc:
            logger.warning("Local llama.cpp HTTP request failed: %s", type(exc).__name__)
            raise LLMUnavailableError("The local model server is unavailable") from exc

        if response.status_code >= 500 or response.status_code == 429:
            logger.warning("llama.cpp server returned HTTP %s", response.status_code)
            raise LLMUnavailableError("The local model server is unavailable")
        if response.is_error:
            logger.warning("llama.cpp server returned HTTP %s", response.status_code)
            raise LLMResponseError("The local model server rejected the request")

        try:
            body = response.json()
            reply = body["choices"][0]["message"]["content"]
        except (ValueError, TypeError, KeyError, IndexError) as exc:
            logger.warning("llama.cpp server returned a malformed response")
            raise LLMResponseError("The local model server returned an invalid response") from exc

        if not isinstance(reply, str) or not reply.strip():
            logger.warning("llama.cpp server returned an empty response")
            raise LLMResponseError("The local model server returned an invalid response")
        return reply.strip()

    def _load_character_prompt(self) -> str:
        fallback = (
            "You are AURA, a fictional adult AI companion. Be warm, honest, "
            "respectful, and consent-aware. Never sexualize or roleplay as a "
            "minor, and never impersonate a real person."
        )
        try:
            profile = json.loads(
                self.settings.character_profile_path.read_text(encoding="utf-8")
            )
            name = str(profile.get("name", "AURA"))
            description = str(profile.get("description", "A fictional adult companion."))
            traits = ", ".join(str(item) for item in profile.get("traits", []))
            style = str(profile.get("communication_style", "natural and respectful"))
            boundaries = profile.get("boundaries", {})
            return (
                f"You are {name}. {description} "
                f"Your traits are: {traits or 'warm and respectful'}. "
                f"Communication style: {style}. "
                "You must respect consent and user boundaries. "
                f"Minor sexual content is prohibited: "
                f"{bool(boundaries.get('must_refuse_minor_sexual_content', True))}. "
                f"Real-person impersonation is prohibited: "
                f"{bool(boundaries.get('must_not_impersonate_real_people', True))}."
            )
        except (OSError, json.JSONDecodeError, AttributeError, TypeError) as exc:
            logger.warning("Character profile unavailable: %s", type(exc).__name__)
            return fallback
