"""Shared test fixtures."""

from __future__ import annotations

import pytest

from jarvis.core.config import JarvisConfig


@pytest.fixture()
def config(tmp_path, monkeypatch) -> JarvisConfig:
    """Isolated JarvisConfig with a temp data dir and no env leakage."""
    monkeypatch.setenv("JARVIS_DATA_DIR", str(tmp_path / "jarvis-data"))
    for var in (
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
        "DEEPSEEK_API_KEY",
        "MISTRAL_API_KEY",
    ):
        monkeypatch.delenv(var, raising=False)
    cfg = JarvisConfig(_env_file=None)
    cfg.ensure_dirs()
    return cfg
