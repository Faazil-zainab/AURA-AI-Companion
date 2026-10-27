"""Environment-backed settings for the AURA backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - requirements install supplies this
    load_dotenv = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if load_dotenv is not None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PROJECT_ROOT / "backend" / ".env")


def _path_from_env(name: str, default: Path) -> Path:
    value = os.getenv(name)
    path = Path(value) if value else default
    return path if path.is_absolute() else PROJECT_ROOT / path


@dataclass(frozen=True)
class Settings:
    """Runtime settings shared by API services.

    Paths are resolved relative to the project root so the backend behaves the
    same when launched from the root or from ``backend``.
    """

    app_name: str = "AURA Local Companion"
    app_version: str = "0.2.0-phase2"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"
    database_path: Path = PROJECT_ROOT / "backend" / "data" / "aura.db"
    model_dir: Path = PROJECT_ROOT / "models" / "llm"
    stt_model_dir: Path = PROJECT_ROOT / "models" / "stt"
    tts_model_dir: Path = PROJECT_ROOT / "models" / "tts"
    llm_model_path: Path | None = None
    llm_server_url: str = "http://127.0.0.1:8080"
    llm_chat_endpoint: str = "/v1/chat/completions"
    llm_model_name: str | None = None
    llm_system_prompt_mode: str = "system"
    llm_context_size: int = 2048
    llm_max_tokens: int = 256
    llm_timeout_seconds: float = 60.0
    llm_temperature: float = 0.8
    llm_top_p: float = 0.9
    max_history_messages: int = 12
    character_profile_path: Path = PROJECT_ROOT / "character" / "personality.json"

    @classmethod
    def from_environment(cls) -> "Settings":
        model_path = os.getenv("AURA_LLM_MODEL_PATH")
        return cls(
            app_name=os.getenv("AURA_APP_NAME", cls.app_name),
            app_version=os.getenv("AURA_APP_VERSION", cls.app_version),
            host=os.getenv("AURA_HOST", cls.host),
            port=int(os.getenv("AURA_PORT", str(cls.port))),
            log_level=os.getenv("AURA_LOG_LEVEL", cls.log_level).upper(),
            database_path=_path_from_env("AURA_DATABASE_PATH", cls.database_path),
            model_dir=_path_from_env("AURA_MODEL_DIR", cls.model_dir),
            stt_model_dir=_path_from_env("AURA_STT_MODEL_DIR", cls.stt_model_dir),
            tts_model_dir=_path_from_env("AURA_TTS_MODEL_DIR", cls.tts_model_dir),
            llm_model_path=(
                _path_from_env("AURA_LLM_MODEL_PATH", Path(model_path))
                if model_path
                else None
            ),
            llm_server_url=os.getenv("AURA_LLM_SERVER_URL", cls.llm_server_url).rstrip("/"),
            llm_chat_endpoint=os.getenv(
                "AURA_LLM_CHAT_ENDPOINT", cls.llm_chat_endpoint
            ),
            llm_model_name=os.getenv("AURA_LLM_MODEL_NAME") or None,
            llm_system_prompt_mode=os.getenv(
                "AURA_LLM_SYSTEM_PROMPT_MODE", cls.llm_system_prompt_mode
            ),
            llm_context_size=int(
                os.getenv("AURA_LLM_CONTEXT_SIZE", str(cls.llm_context_size))
            ),
            llm_max_tokens=int(os.getenv("AURA_LLM_MAX_TOKENS", str(cls.llm_max_tokens))),
            llm_timeout_seconds=float(
                os.getenv("AURA_LLM_TIMEOUT_SECONDS", str(cls.llm_timeout_seconds))
            ),
            llm_temperature=float(
                os.getenv("AURA_LLM_TEMPERATURE", str(cls.llm_temperature))
            ),
            llm_top_p=float(os.getenv("AURA_LLM_TOP_P", str(cls.llm_top_p))),
            max_history_messages=int(
                os.getenv("AURA_MAX_HISTORY_MESSAGES", str(cls.max_history_messages))
            ),
            character_profile_path=_path_from_env(
                "AURA_CHARACTER_PROFILE_PATH", cls.character_profile_path
            ),
        )


def get_settings() -> Settings:
    """Return settings loaded from the current process environment."""

    return Settings.from_environment()
