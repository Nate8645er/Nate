"""Unit-Tests der reinen Tarif-Logik — laufen ohne DB/Gateway."""
from app.plans import model_allowed


def test_wildcard_allows_everything():
    assert model_allowed("anything/at-all", ["*"]) is True


def test_membership():
    allowed = ["anthropic/claude-sonnet-5", "ollama/llama3.2"]
    assert model_allowed("ollama/llama3.2", allowed) is True
    assert model_allowed("openai/gpt-4o", allowed) is False


def test_empty_denies():
    assert model_allowed("anything", []) is False
