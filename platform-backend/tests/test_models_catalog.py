"""Unit-Tests des Modell-Katalogs — ohne DB."""
from app.models_catalog import KNOWN_MODELS, is_registered, models_for_plan, supports_vision


def test_is_registered():
    assert is_registered("ollama/llama3.2") is True
    assert is_registered("openai/gpt-4o") is True
    assert is_registered("erfundenes/modell") is False


def test_supports_vision_true_for_documented_vision_models():
    assert supports_vision("anthropic/claude-sonnet-5") is True
    assert supports_vision("openai/gpt-4o") is True


def test_supports_vision_false_for_local_text_only_llama():
    # ollama/llama3.2 ist die reine Text-Variante (kein "-vision"-Suffix).
    assert supports_vision("ollama/llama3.2") is False


def test_supports_vision_false_for_unregistered_model():
    assert supports_vision("erfundenes/modell") is False


def test_every_catalog_entry_has_bool_vision_field():
    for m in KNOWN_MODELS:
        assert isinstance(m.get("vision"), bool)


def test_wildcard_returns_all_registered():
    got = models_for_plan(["*"])
    assert len(got) == len(KNOWN_MODELS)
    assert {m["id"] for m in got} == {m["id"] for m in KNOWN_MODELS}


def test_plan_intersection_only_registered():
    # Ein im Tarif gelistetes, aber nicht registriertes Modell taucht nicht auf.
    got = models_for_plan(["ollama/llama3.2", "nicht/registriert"])
    ids = {m["id"] for m in got}
    assert ids == {"ollama/llama3.2"}


def test_empty_plan_yields_nothing():
    assert models_for_plan([]) == []
