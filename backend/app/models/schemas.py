"""Public API schemas used by the AURA backend."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    service: str
    version: str
    request_id: str


class ChatMessage(BaseModel):
    """A prior turn supplied by the client until Phase 3 owns persistence."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("content must not be blank")
        return value


class ChatRequest(BaseModel):
    """Phase-2 chat input; history is bounded and is not stored yet."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(min_length=1, max_length=128)
    message: str = Field(min_length=1, max_length=4000)
    voice_enabled: bool = False
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator("session_id", "message")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("value must not be blank")
        return value


class ChatResponse(BaseModel):
    """The actual model response, without claiming audio exists."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    reply: str
    emotion: str = "neutral"
    audio_available: bool = False
    request_id: str
