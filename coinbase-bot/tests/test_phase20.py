"""Phase 20 — mobile key setup: encrypted secret store and the authenticated
key endpoints. All keys are synthetic; no network, no real order. The endpoint
functions are called directly with a fake session (no HTTP needed)."""

import json

import pytest

from coinbase_connector.keyfile import load_key_from_text
from server.secretstore import SecretError, SecretStore

FAKE = json.dumps(
    {
        "name": "organizations/x/apiKeys/abcdef",
        "privateKey": "Zx9Qw7Lp2Kv4Nm8Rt6Yb1Cd3Fg5Hj0" * 3,
    }
)


# ---- secret store ----------------------------------------------------------


def test_secret_is_encrypted_at_rest_and_round_trips(tmp_path):
    s = SecretStore(tmp_path / "secret.enc")
    s.store(FAKE, "passphrase123", key_id_suffix="abcdef")
    raw = (tmp_path / "secret.enc").read_text()
    assert "privateKey" not in raw and "Zx9Qw7Lp2Kv" not in raw  # ciphertext only
    assert set(json.loads(raw)) == {"salt", "token", "created_at", "key_id_suffix"}
    s2 = SecretStore(tmp_path / "secret.enc")  # fresh instance = restart
    assert not s2.is_unlocked
    with pytest.raises(SecretError):
        s2.unlock("falschXYZ123")
    s2.unlock("passphrase123")
    assert s2.is_unlocked and load_key_from_text(s2.plaintext())["api_key"].endswith(
        "abcdef"
    )


def test_short_passphrase_refused(tmp_path):
    with pytest.raises(SecretError):
        SecretStore(tmp_path / "secret.enc").store(FAKE, "short")


def test_clear_removes_file_and_memory(tmp_path):
    s = SecretStore(tmp_path / "secret.enc")
    s.store(FAKE, "passphrase123")
    s.clear()
    assert not s.is_configured() and not s.is_unlocked


def test_env_unlock_uses_host_passphrase(tmp_path, monkeypatch):
    s = SecretStore(tmp_path / "secret.enc")
    s.store(FAKE, "passphrase123")
    s.lock()
    monkeypatch.setenv("HYPERGROK_SECRET_PASSPHRASE", "passphrase123")
    assert s.try_env_unlock() and s.is_unlocked


def test_status_never_leaks_secret(tmp_path):
    s = SecretStore(tmp_path / "secret.enc")
    s.store(FAKE, "passphrase123", key_id_suffix="abcdef")
    st = s.status()
    assert st["configured"] and st["unlocked"] and st["key_id_suffix"] == "abcdef"
    assert "Zx9Qw7Lp2Kv" not in json.dumps(st)


# ---- key endpoints (direct calls, fake session, temp store) ----------------


class FakeSession:
    username, role, csrf = "admin", "admin", "x"


@pytest.fixture
def app_with_temp_store(tmp_path, monkeypatch):
    import server.app as app

    monkeypatch.setattr(app, "SECRETS", SecretStore(tmp_path / "secret.enc"))
    app.reset_connector()
    return app


def test_setup_stores_a_view_trade_key(app_with_temp_store, monkeypatch):
    app = app_with_temp_store
    monkeypatch.setattr(
        app,
        "_verify_key_readonly",
        lambda creds: {
            "ok": True,
            "checks": {"portfolio_isolated": True},
            "usdc_available": "17.10",
        },
    )
    out = app.key_setup(
        {"key": FAKE, "passphrase": "passphrase123"}, session=FakeSession()
    )
    assert out["stored"] and out["secret"]["configured"] and out["secret"]["unlocked"]
    assert out["verify"]["usdc_available"] == "17.10"


def test_setup_rejects_transfer_key_and_stores_nothing(
    app_with_temp_store, monkeypatch
):
    app = app_with_temp_store

    def refuse(creds):
        raise RuntimeError("API key has transfer permission")

    monkeypatch.setattr(app, "_verify_key_readonly", refuse)
    with pytest.raises(app.HTTPException):
        app.key_setup(
            {"key": FAKE, "passphrase": "passphrase123"}, session=FakeSession()
        )
    assert not app.SECRETS.is_configured()


def test_setup_rejects_unreadable_key(app_with_temp_store):
    app = app_with_temp_store
    with pytest.raises(app.HTTPException):
        app.key_setup(
            {"key": "nicht lesbar", "passphrase": "passphrase123"},
            session=FakeSession(),
        )


def test_unlock_lock_clear_cycle(app_with_temp_store, monkeypatch):
    app = app_with_temp_store
    monkeypatch.setattr(app, "_verify_key_readonly", lambda creds: {"ok": True})
    app.key_setup({"key": FAKE, "passphrase": "passphrase123"}, session=FakeSession())
    app.key_lock(session=FakeSession())
    assert not app.SECRETS.is_unlocked
    with pytest.raises(app.HTTPException):
        app.key_unlock({"passphrase": "falschXYZ"}, session=FakeSession())
    app.key_unlock({"passphrase": "passphrase123"}, session=FakeSession())
    assert app.SECRETS.is_unlocked
    app.key_clear(session=FakeSession())
    assert not app.SECRETS.is_configured()


def test_scheduler_toggle_and_status(app_with_temp_store):
    app = app_with_temp_store
    app.scheduler_toggle(enabled=True, interval=5, session=FakeSession())
    assert app.SCHED["enabled"] and app.SCHED["interval"] == 15  # min 15 enforced
    assert app.scheduler_status()["enabled"] is True
    app.scheduler_toggle(enabled=False, interval=60, session=FakeSession())
    assert app.SCHED["enabled"] is False
