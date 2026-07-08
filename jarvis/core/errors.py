"""Gemeinsame Fehlerklassen für alle Modell-Anbindungen."""


class LLMError(Exception):
    """Basisfehler für alle Sprachmodell-Anbindungen (Ollama, Claude, ...)."""
