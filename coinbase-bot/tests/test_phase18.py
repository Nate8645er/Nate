"""Phase 18 — secure CDP key-file import. All keys here are synthetic; the
real key is never used in tests. No network, no real order."""

import json

import pytest

from coinbase_connector.connector import CoinbaseLiveConnector, ConnectorError
from coinbase_connector.keyfile import (
    KeyFileError,
    describe,
    load_key_file,
    resolve_credentials,
)

# A fake Ed25519-shaped secret: 88 base64 chars, not a real key.
FAKE_ED = "A" * 87 + "="
FAKE_NAME = "organizations/11111111-1111-1111-1111-111111111111/apiKeys/22222222"
FAKE_PEM = "-----BEGIN EC PRIVATE KEY-----\nMHc==\n-----END EC PRIVATE KEY-----"


def write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    p.chmod(0o600)
    return p


def test_detects_cdp_json(tmp_path):
    f = write(
        tmp_path, "k.json", json.dumps({"name": FAKE_NAME, "privateKey": FAKE_ED})
    )
    creds = load_key_file(f)
    assert creds["api_key"] == FAKE_NAME and creds["api_secret"] == FAKE_ED
    d = describe(f)
    assert d["secret_kind"] == "Ed25519-base64" and d["key_id_suffix"] == FAKE_NAME[-6:]
    assert "A" * 10 not in json.dumps(d)  # describe never leaks the secret


def test_detects_pem_needs_name_from_env(tmp_path, monkeypatch):
    f = write(tmp_path, "k.pem", FAKE_PEM)
    monkeypatch.delenv("COINBASE_API_KEY", raising=False)
    with pytest.raises(KeyFileError):
        load_key_file(f)  # PEM carries no name
    monkeypatch.setenv("COINBASE_API_KEY", FAKE_NAME)
    creds = load_key_file(f)
    assert creds["api_key"] == FAKE_NAME and "BEGIN" in creds["api_secret"]


def test_detects_dotenv_text(tmp_path):
    f = write(
        tmp_path,
        "k.txt",
        f'COINBASE_API_KEY="{FAKE_NAME}"\nCOINBASE_API_SECRET={FAKE_ED}\n',
    )
    creds = load_key_file(f)
    assert creds["api_key"] == FAKE_NAME and creds["api_secret"] == FAKE_ED


def test_rejects_unknown_and_empty(tmp_path):
    with pytest.raises(KeyFileError):
        load_key_file(write(tmp_path, "bad.txt", "irgendwas ohne struktur"))
    with pytest.raises(KeyFileError):
        load_key_file(write(tmp_path, "empty.txt", "   "))
    with pytest.raises(KeyFileError):
        load_key_file(tmp_path / "missing.txt")


def test_json_missing_fields_is_rejected(tmp_path):
    f = write(tmp_path, "part.json", json.dumps({"name": FAKE_NAME}))
    with pytest.raises(KeyFileError):
        load_key_file(f)


def test_describe_reports_world_readable(tmp_path):
    f = write(
        tmp_path, "k.json", json.dumps({"name": FAKE_NAME, "privateKey": FAKE_ED})
    )
    f.chmod(0o644)
    d = describe(f)
    assert d["world_readable"] is True and d["permissions_octal"] == "0o644"


def test_resolve_credentials_prefers_key_file(tmp_path, monkeypatch):
    f = write(
        tmp_path, "k.json", json.dumps({"name": FAKE_NAME, "privateKey": FAKE_ED})
    )
    monkeypatch.setenv("COINBASE_KEY_FILE", str(f))
    assert resolve_credentials()["api_key"] == FAKE_NAME
    monkeypatch.delenv("COINBASE_KEY_FILE")
    monkeypatch.delenv("COINBASE_API_KEY", raising=False)
    monkeypatch.delenv("COINBASE_API_SECRET", raising=False)
    assert resolve_credentials() is None


class PermClient:
    def __init__(self, can_transfer):
        self._t = can_transfer

    def get_api_key_permissions(self):
        return {
            "can_view": True,
            "can_trade": True,
            "can_transfer": self._t,
            "portfolio_uuid": "pf",
            "portfolio_type": "DEFAULT",
        }


def test_connector_refuses_transfer_key_like_the_real_one():
    # A View+Trade key is accepted; a transfer-capable key is refused - exactly
    # the situation found with the real uploaded key (can_transfer=True).
    c = CoinbaseLiveConnector(client=PermClient(can_transfer=False))
    assert c.permissions["can_trade"]
    with pytest.raises(ConnectorError):
        CoinbaseLiveConnector(client=PermClient(can_transfer=True))
