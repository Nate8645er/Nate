"""Tests für das Laden der API-Schlüssel und die Platzhalter-Erkennung."""

import json

from jarvis.utils import secrets as secrets_module
from jarvis.utils.secrets import ensure_secrets_file, load_secret


def _use_tmp_secrets(monkeypatch, tmp_path, content: dict | None):
    path = tmp_path / "secrets.json"
    if content is not None:
        path.write_text(json.dumps(content), encoding="utf-8")
    monkeypatch.setattr(secrets_module, "SECRETS_PATH", path)
    return path


def test_platzhalter_zaehlt_nicht_als_schluessel(monkeypatch, tmp_path):
    _use_tmp_secrets(monkeypatch, tmp_path, {
        "anthropic_api_key": "sk-ant-HIER-DEINEN-SCHLUESSEL-EINFUEGEN",
        "deepgram_api_key": "dg-echter-schluessel",
    })
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    assert load_secret("anthropic_api_key", "ANTHROPIC_API_KEY") is None
    assert load_secret("deepgram_api_key", "DEEPGRAM_API_KEY") == "dg-echter-schluessel"


def test_umgebungsvariable_hat_vorrang(monkeypatch, tmp_path):
    _use_tmp_secrets(monkeypatch, tmp_path, {"anthropic_api_key": "aus-datei"})
    monkeypatch.setenv("ANTHROPIC_API_KEY", "aus-umgebung")
    assert load_secret("anthropic_api_key", "ANTHROPIC_API_KEY") == "aus-umgebung"


def test_fehlende_datei_ergibt_none(monkeypatch, tmp_path):
    _use_tmp_secrets(monkeypatch, tmp_path, None)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    assert load_secret("elevenlabs_api_key", "ELEVENLABS_API_KEY") is None


def test_ensure_legt_datei_mit_platzhaltern_an(monkeypatch, tmp_path):
    path = _use_tmp_secrets(monkeypatch, tmp_path, None)
    assert ensure_secrets_file() is True
    assert path.exists()
    inhalt = json.loads(path.read_text(encoding="utf-8"))
    assert "anthropic_api_key" in inhalt
    # Beim zweiten Aufruf existiert die Datei schon - nichts überschreiben
    assert ensure_secrets_file() is False
