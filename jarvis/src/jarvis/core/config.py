"""Central configuration for JARVIS.

Configuration is layered (lowest to highest precedence):

1. Built-in defaults defined on the models below.
2. ``config.yaml`` in the data directory (optional).
3. Environment variables / ``.env`` file, prefixed with ``JARVIS_`` and using
   ``__`` as the nesting delimiter (e.g. ``JARVIS_LLM__DEFAULT_PROVIDER=ollama``).

API keys are read from conventional environment variables
(``ANTHROPIC_API_KEY``, ``OPENAI_API_KEY``, ...) so existing setups work
without renaming anything.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


def default_data_dir() -> Path:
    """Return the per-user JARVIS data directory."""
    override = os.environ.get("JARVIS_DATA_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".jarvis"


class ProviderConfig(BaseModel):
    """Connection settings for a single LLM provider."""

    enabled: bool = True
    api_key: SecretStr | None = None
    base_url: str | None = None
    default_model: str | None = None
    timeout_seconds: float = 120.0
    extra_headers: dict[str, str] = Field(default_factory=dict)


class LLMConfig(BaseModel):
    """LLM routing and provider settings."""

    default_provider: str | None = None  # None => auto-select
    default_model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 4096
    # Routing preferences used by the model router.
    prefer_local: bool = False
    max_cost_tier: int = 3  # 0=free/local .. 3=premium
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)


class MemoryConfig(BaseModel):
    """Memory subsystem settings."""

    short_term_max_messages: int = 60
    short_term_max_chars: int = 60_000
    database_file: str = "memory.db"
    vector_backend: Literal["auto", "chroma", "local"] = "auto"
    vector_collection: str = "jarvis"
    embedding_provider: str | None = None  # e.g. "openai", "ollama"; None => local hashing
    embedding_model: str | None = None
    rag_chunk_size: int = 900
    rag_chunk_overlap: int = 150
    rag_top_k: int = 6


class VoiceConfig(BaseModel):
    """Voice pipeline settings."""

    enabled: bool = False
    wake_word: str = "jarvis"
    wake_word_threshold: float = 0.5
    stt_model: str = "large-v3"
    stt_device: Literal["auto", "cuda", "cpu"] = "auto"
    stt_language: str | None = None  # None => autodetect
    tts_backend: Literal["auto", "piper", "xtts", "coqui", "none"] = "auto"
    tts_voice: str | None = None
    tts_speaker_wav: str | None = None  # reference clip for XTTS voice cloning
    tts_emotion: str = "neutral"
    sample_rate: int = 16_000
    input_device: int | None = None
    output_device: int | None = None
    allow_interruption: bool = True


class VisionConfig(BaseModel):
    """Vision pipeline settings."""

    enabled: bool = False
    camera_index: int = 0
    ocr_languages: str = "eng+deu"
    face_detection: bool = True
    object_detection_model: str = "yolov8n.pt"


class DesktopConfig(BaseModel):
    """Desktop automation settings."""

    enabled: bool = False
    failsafe: bool = True  # pyautogui corner failsafe
    action_pause_seconds: float = 0.05
    terminal_timeout_seconds: float = 120.0
    allowed_directories: list[str] = Field(default_factory=list)  # empty => home dir only


class BrowserConfig(BaseModel):
    """Browser automation settings."""

    enabled: bool = False
    headless: bool = True
    browser: Literal["chromium", "firefox", "webkit"] = "chromium"
    executable_path: str | None = None
    downloads_dir: str = "downloads"
    default_timeout_ms: int = 30_000
    user_agent: str | None = None


class ApiConfig(BaseModel):
    """FastAPI server settings."""

    host: str = "127.0.0.1"
    port: int = 8765
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost", "http://127.0.0.1"])
    auth_token: SecretStr | None = None  # optional bearer token for the HTTP API


class GuiConfig(BaseModel):
    """PySide6 HUD settings."""

    theme: Literal["jarvis", "dark"] = "jarvis"
    accent_color: str = "#28c8ff"
    secondary_color: str = "#ffb02e"
    transparency: float = 0.92
    always_on_top: bool = False
    fps: int = 60
    monitor_index: int = 0


class SecurityConfig(BaseModel):
    """Security and permission settings."""

    policy_file: str = "permissions.yaml"
    default_policy: Literal["allow", "ask", "deny"] = "ask"
    audit_log: bool = True
    sandbox_python: bool = True
    confirm_capabilities: list[str] = Field(
        default_factory=lambda: [
            "desktop.input",
            "desktop.terminal",
            "files.delete",
            "files.write",
            "browser.forms",
            "integrations.send",
        ]
    )


class PluginConfig(BaseModel):
    """Plugin system settings."""

    enabled: bool = True
    directories: list[str] = Field(default_factory=lambda: ["plugins"])
    hot_reload: bool = True
    mcp_servers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    rest_plugins: list[str] = Field(default_factory=list)  # paths to REST plugin descriptors


class JarvisConfig(BaseSettings):
    """Root configuration object, resolved once at startup and injected everywhere."""

    model_config = SettingsConfigDict(
        env_prefix="JARVIS_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    data_dir: Path = Field(default_factory=default_data_dir)
    log_level: str = "INFO"
    language: str = "en"
    assistant_name: str = "JARVIS"
    user_name: str = "Sir"

    llm: LLMConfig = Field(default_factory=LLMConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    desktop: DesktopConfig = Field(default_factory=DesktopConfig)
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    gui: GuiConfig = Field(default_factory=GuiConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    plugins: PluginConfig = Field(default_factory=PluginConfig)

    def ensure_dirs(self) -> None:
        """Create the data directory layout."""
        for sub in ("", "logs", "memory", "downloads", "cache", "voices"):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)

    def resolve_path(self, name: str) -> Path:
        """Resolve a file name relative to the data directory."""
        path = Path(name).expanduser()
        return path if path.is_absolute() else self.data_dir / path

    def provider(self, name: str) -> ProviderConfig:
        """Return provider settings, materialising env-var API keys on demand."""
        cfg = self.llm.providers.get(name, ProviderConfig())
        if cfg.api_key is None:
            env_key = _API_KEY_ENV.get(name)
            if env_key and os.environ.get(env_key):
                cfg = cfg.model_copy(update={"api_key": SecretStr(os.environ[env_key])})
        return cfg


_API_KEY_ENV: dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "mistral": "MISTRAL_API_KEY",
}


def load_config(config_file: Path | None = None) -> JarvisConfig:
    """Load configuration from YAML file + environment, with env taking precedence."""
    file_values: dict[str, Any] = {}
    candidate = config_file or default_data_dir() / "config.yaml"
    if candidate.is_file():
        loaded = yaml.safe_load(candidate.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            file_values = loaded
    # BaseSettings gives env > init kwargs? No: init kwargs win over env, so feed
    # file values through a nested-merge against env-built settings instead.
    env_config = JarvisConfig()
    if not file_values:
        return env_config
    merged = _deep_merge(file_values, env_config.model_dump(exclude_unset=True, mode="python"))
    return JarvisConfig(**merged)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into ``base`` (override wins)."""
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
