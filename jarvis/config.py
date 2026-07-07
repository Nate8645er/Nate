"""Central configuration, driven by environment variables / .env file.

Every subsystem reads its settings from here so the whole OS can be
configured from one place (env, .env, docker-compose, or the Settings UI).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="JARVIS_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- Server ---
    host: str = "127.0.0.1"
    port: int = 8765
    debug: bool = False

    # --- Paths ---
    data_dir: Path = Field(default=Path.home() / ".jarvis")
    plugins_dir: Path = Field(default=Path("plugins"))
    workflows_dir: Path = Field(default=Path("workflows"))

    # --- Identity ---
    assistant_name: str = "Jarvis"
    wake_word: str = "jarvis"
    language: str = "de"

    # --- LLM providers ---
    llm_provider: str = "auto"  # auto | anthropic | openai | ollama | echo
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # --- Memory backends ---
    vector_backend: str = "auto"  # auto | chroma | qdrant | naive
    qdrant_url: str = "http://localhost:6333"
    database_url: str = ""  # empty -> SQLite in data_dir
    redis_url: str = ""  # optional, for distributed event bus

    # --- Voice ---
    voice_enabled: bool = True
    stt_model: str = "small"  # faster-whisper model size
    tts_voice: str = "de_DE-thorsten-medium"  # piper voice

    # --- Safety ---
    # Actions with risk >= this level always require explicit user approval.
    # 0 = ask for everything, 1 = ask for writes, 2 = ask for system-level, 3 = never ask (unsafe)
    approval_threshold: int = 1
    approval_timeout_seconds: float = 120.0

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(exist_ok=True)


settings = Settings()
