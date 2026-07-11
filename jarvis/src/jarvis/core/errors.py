"""Exception hierarchy for JARVIS.

Every subsystem raises exceptions derived from :class:`JarvisError` so callers
can catch a single base class at API boundaries while still being able to
distinguish failure categories.
"""

from __future__ import annotations


class JarvisError(Exception):
    """Base class for all JARVIS errors."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class ConfigurationError(JarvisError):
    """Raised when configuration is missing or invalid."""


class ProviderError(JarvisError):
    """Raised when an LLM provider request fails."""

    def __init__(
        self,
        message: str,
        *,
        provider: str = "",
        status_code: int | None = None,
        cause: Exception | None = None,
    ) -> None:
        super().__init__(message, cause=cause)
        self.provider = provider
        self.status_code = status_code


class ProviderUnavailableError(ProviderError):
    """Raised when a provider is not reachable or not configured."""


class ToolError(JarvisError):
    """Raised when a tool invocation fails."""

    def __init__(self, message: str, *, tool: str = "", cause: Exception | None = None) -> None:
        super().__init__(message, cause=cause)
        self.tool = tool


class AgentError(JarvisError):
    """Raised when an agent run fails."""


class MemoryStoreError(JarvisError):
    """Raised when a memory backend operation fails."""


class PluginError(JarvisError):
    """Raised when plugin discovery, loading or execution fails."""


class PermissionDeniedError(JarvisError):
    """Raised when the security layer denies an action."""

    def __init__(self, capability: str, message: str | None = None) -> None:
        super().__init__(message or f"Permission denied for capability '{capability}'")
        self.capability = capability


class VoiceError(JarvisError):
    """Raised by the voice pipeline (wake word, STT, TTS, audio I/O)."""


class VisionError(JarvisError):
    """Raised by the vision pipeline (camera, screen, OCR, detection)."""


class DesktopError(JarvisError):
    """Raised by desktop automation."""


class BrowserError(JarvisError):
    """Raised by browser automation."""


class IntegrationError(JarvisError):
    """Raised by third-party service integrations."""
