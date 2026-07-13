"""Tests fuer die Modell-Registry des JARVIS-Agenten (inkl. Fable 5)."""

from __future__ import annotations

import pytest

from open_jarvis.agent import models


def test_fable5_is_default_and_present() -> None:
    default = models.default_model()
    assert default.key == "fable-5"
    assert default.model_id == "claude-fable-5"
    assert default.provider == "claude"
    assert default.needs_key is True


def test_brain_is_fable5_not_haiku() -> None:
    # Laut Systemarchitektur ist das Gehirn Fable 5, NICHT Haiku.
    assert models.BRAIN_MODEL_KEY == "fable-5"
    assert models.brain_model().key == "fable-5"
    assert models.brain_model().model_id == "claude-fable-5"
    assert models.brain_model().key != "haiku-4.5"


def test_registry_contains_expected_engines() -> None:
    keys = {m.key for m in models.list_models()}
    assert {"fable-5", "opus-4.8", "sonnet-5", "haiku-4.5", "groq", "local"} <= keys


def test_local_model_is_keyless() -> None:
    local = models.fallback_model()
    assert local.key == "local"
    assert local.needs_key is False


@pytest.mark.parametrize(
    "alias,expected",
    [
        ("fable", "fable-5"),
        ("fable5", "fable-5"),
        ("claude-fable-5", "fable-5"),
        ("opus", "opus-4.8"),
        ("HAIKU", "haiku-4.5"),
        ("offline", "local"),
        (None, "fable-5"),
        ("", "fable-5"),
    ],
)
def test_resolve_aliases(alias, expected) -> None:
    assert models.resolve_model(alias).key == expected


def test_resolve_unknown_raises() -> None:
    with pytest.raises(ValueError):
        models.resolve_model("gpt-4")
