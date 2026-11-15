"""Phase 13 tests: authentication hardening and the three new agents.
No network (RPC/HTTP calls are monkeypatched), no real orders."""

import pytest

from multimarket import smart_money, social, whale
from server.auth import AuthStore, hash_password, verify_password


# ---- password hashing ----------------------------------------------------


def test_password_is_hashed_not_stored_plain():
    rec = hash_password("korrekt-pferd-batterie")
    assert "korrekt-pferd-batterie" not in str(rec)
    assert rec["iterations"] >= 100_000
    assert verify_password("korrekt-pferd-batterie", rec) is True
    assert verify_password("falsch", rec) is False


def test_same_password_gets_different_salt():
    a, b = hash_password("gleich"), hash_password("gleich")
    assert a["salt"] != b["salt"] and a["hash"] != b["hash"]


def test_verify_survives_broken_record():
    assert verify_password("x", {}) is False
    assert verify_password("x", {"salt": "zz", "hash": "zz"}) is False


# ---- sessions and roles --------------------------------------------------


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr("server.auth.USERS_FILE", tmp_path / "users.json")
    monkeypatch.setattr("server.auth.AUDIT_FILE", tmp_path / "audit.jsonl")
    monkeypatch.setattr("server.auth.STATE", tmp_path)
    s = AuthStore()
    s.add_user("admin", "pw-admin", "admin")
    s.add_user("gast", "pw-gast", "viewer")
    return s


def test_login_and_session(store):
    assert store.login("admin", "falsch") is None
    session = store.login("admin", "pw-admin")
    assert session is not None and session.role == "admin"
    assert store.session(session.token) is not None
    assert session.csrf and session.csrf != session.token


def test_logout_invalidates_session(store):
    session = store.login("gast", "pw-gast")
    store.logout(session.token)
    assert store.session(session.token) is None


def test_expired_session_is_rejected(store):
    session = store.login("gast", "pw-gast")
    session.expires_at = 0
    assert store.session(session.token) is None


def test_unknown_user_is_rejected(store):
    assert store.login("niemand", "egal") is None


def test_roles_are_recorded(store):
    assert store.login("gast", "pw-gast").role == "viewer"
    assert store.login("admin", "pw-admin").role == "admin"


def test_brute_force_lockout(store):
    for _ in range(5):
        store.login("admin", "falsch", ip="5.5.5.5")
    # correct password is now refused from that ip / for that user
    assert store.login("admin", "pw-admin", ip="5.5.5.5") is None


def test_audit_log_is_written(store, tmp_path):
    store.login("admin", "pw-admin")
    store.login("admin", "falsch")
    lines = (tmp_path / "audit.jsonl").read_text().strip().splitlines()
    events = [l for l in lines if "login_ok" in l or "login_failed" in l]
    assert len(events) >= 2


def test_invalid_role_rejected(store):
    with pytest.raises(ValueError):
        store.add_user("x", "y", "superuser")


# ---- whale tracker -------------------------------------------------------


def test_whale_reports_unknown_when_rpc_down(monkeypatch):
    monkeypatch.setattr(whale, "rpc_call", lambda *a, **k: None)
    r = whale.analyse("Mint1")
    assert r.supply is None and r.activity == "UNKNOWN"
    assert r.concentration == whale.UNAVAILABLE   # never guessed


def test_whale_computes_real_activity_rate(monkeypatch):
    def fake(method, params, *a, **k):
        if method == "getTokenSupply":
            return {"value": {"uiAmount": 1000.0}}
        if method == "getSignaturesForAddress":
            return [{"blockTime": 1_000_000 + i * 36} for i in range(100)]
        return None
    monkeypatch.setattr(whale, "rpc_call", fake)
    r = whale.analyse("Mint1")
    assert r.recent_tx_count == 100
    assert r.tx_per_hour and r.tx_per_hour > 90
    assert r.activity in ("NORMAL", "BURST")


def test_whale_never_claims_holder_concentration(monkeypatch):
    monkeypatch.setattr(whale, "rpc_call", lambda *a, **k: None)
    d = whale.analyse("Mint1").to_dict()
    assert d["top_holder_pct"] == "UNAVAILABLE_FREE_RPC"


# ---- smart money ---------------------------------------------------------


def test_smart_money_flags_active_mint_authority(monkeypatch):
    from multimarket.core import OnChain
    monkeypatch.setattr(smart_money, "fetch_onchain",
                        lambda *a, **k: OnChain(mint_authority_active=True, freeze_authority_active=False))
    monkeypatch.setattr(smart_money, "whale_analyse",
                        lambda *a, **k: whale.WhaleReport("m", 1.0, 10, 1.0, 10.0, "NORMAL",
                                                          whale.UNAVAILABLE, whale.UNAVAILABLE, []))
    r = smart_money.analyse("Mint1")
    assert r.structural_risk == "HIGH"
    assert r.early_buyer_analysis == "UNAVAILABLE_PAID_INDEXER"
    assert r.holder_concentration == "UNAVAILABLE_FREE_RPC"


def test_smart_money_unknown_without_data(monkeypatch):
    from multimarket.core import OnChain
    monkeypatch.setattr(smart_money, "fetch_onchain", lambda *a, **k: OnChain())
    monkeypatch.setattr(smart_money, "whale_analyse",
                        lambda *a, **k: whale.WhaleReport("m", None, None, None, None, "UNKNOWN",
                                                          whale.UNAVAILABLE, whale.UNAVAILABLE, []))
    assert smart_money.analyse("Mint1").structural_risk == "UNKNOWN"


# ---- social / attention --------------------------------------------------


def test_social_never_invents_sentiment(monkeypatch):
    monkeypatch.setattr(social, "safe_get_json", lambda *a, **k: None)
    r = social.trending_assets()
    assert r.available is False and r.trending == []
    assert r.sentiment_score == "UNAVAILABLE_NO_FREE_SOURCE"


def test_social_parses_real_trending_shape(monkeypatch):
    payload = {"coins": [{"item": {"name": "Demo", "symbol": "dem", "market_cap_rank": 42, "score": 0}}]}
    monkeypatch.setattr(social, "safe_get_json", lambda *a, **k: payload)
    r = social.trending_assets()
    assert r.available is True
    assert r.trending[0]["symbol"] == "DEM"
    assert r.sentiment_score == "UNAVAILABLE_NO_FREE_SOURCE"


def test_social_presence_handles_missing_token(monkeypatch):
    monkeypatch.setattr(social, "safe_get_json", lambda *a, **k: [])
    out = social.social_presence("Addr", "solana")
    assert out["available"] is True and out["has_profile"] is False
