"""Phase 9 tests: Solana RPC parsing, Jupiter round-trip logic, connector
status mapping, on-chain -> risk veto. No network (calls are monkeypatched)."""

from multimarket import connectors, jupiter, solana_rpc
from multimarket.core import RiskLevel, Token, assess_memecoin_risk


def tok(**kw):
    base = dict(address="Mint1", symbol="X", name="X", network="solana", source="test")
    base.update(kw)
    return Token(**base)


SPL = solana_rpc.SPL_TOKEN
T22 = solana_rpc.TOKEN_2022


# ---- RPC parsing ---------------------------------------------------------


def test_parse_mint_revoked_authorities_is_good():
    result = {
        "value": {
            "owner": SPL,
            "data": {
                "parsed": {
                    "info": {
                        "mintAuthority": None,
                        "freezeAuthority": None,
                        "decimals": 6,
                        "supply": "1000000000",
                    }
                }
            },
        }
    }
    p = solana_rpc.parse_mint_account(result)
    assert p["mint_authority_active"] is False
    assert p["freeze_authority_active"] is False
    assert p["is_token_2022"] is False
    assert p["supply"] == 1000.0


def test_parse_mint_active_authority_and_token2022():
    result = {
        "value": {
            "owner": T22,
            "data": {
                "parsed": {
                    "info": {
                        "mintAuthority": "SomeAuth",
                        "freezeAuthority": "SomeAuth",
                        "decimals": 0,
                        "supply": "10",
                    }
                }
            },
        }
    }
    p = solana_rpc.parse_mint_account(result)
    assert p["mint_authority_active"] is True
    assert p["freeze_authority_active"] is True
    assert p["is_token_2022"] is True


def test_parse_mint_missing_result_is_unknown():
    p = solana_rpc.parse_mint_account(None)
    assert p["mint_authority_active"] is None
    assert p["is_token_2022"] is None


def test_top_holder_pct():
    largest = {"value": [{"uiAmount": 500.0}, {"uiAmount": 100.0}]}
    assert solana_rpc.top_holder_pct(largest, 1000.0) == 50.0
    assert solana_rpc.top_holder_pct(None, 1000.0) is None
    assert solana_rpc.top_holder_pct(largest, None) is None


def test_fetch_onchain_all_none_when_rpc_down(monkeypatch):
    monkeypatch.setattr(solana_rpc, "rpc_call", lambda *a, **k: None)
    oc = solana_rpc.fetch_onchain("Mint1")
    assert oc.mint_authority_active is None
    assert oc.freeze_authority_active is None
    r = assess_memecoin_risk(tok(), oc)
    assert r.level == RiskLevel.UNKNOWN


def test_fetch_onchain_active_mint_triggers_critical(monkeypatch):
    def fake(method, params, *a, **k):
        if method == "getAccountInfo":
            return {
                "value": {
                    "owner": SPL,
                    "data": {
                        "parsed": {
                            "info": {
                                "mintAuthority": "Auth",
                                "freezeAuthority": None,
                                "decimals": 6,
                                "supply": "1000000000",
                            }
                        }
                    },
                }
            }
        if method == "getTokenSupply":
            return {"value": {"uiAmount": 1000.0}}
        if method == "getTokenLargestAccounts":
            return {"value": [{"uiAmount": 100.0}]}
        return None

    monkeypatch.setattr(solana_rpc, "rpc_call", fake)
    oc = solana_rpc.fetch_onchain("Mint1")
    assert oc.mint_authority_active is True
    r = assess_memecoin_risk(tok(liquidity_usd=50_000), oc)
    assert r.level == RiskLevel.CRITICAL
    assert r.veto is True


# ---- Jupiter -------------------------------------------------------------


def test_round_trip_sellable(monkeypatch):
    monkeypatch.setattr(
        jupiter,
        "quote",
        lambda inp, outp, amount, slippage_bps=50: {
            "outAmount": "1000",
            "priceImpactPct": "0.5",
        },
    )
    rt = jupiter.round_trip_quote("Mint1")
    assert rt["buy_route"] is True
    assert rt["sell_route"] is True
    assert rt["sellable"] is True


def test_round_trip_no_sell_route_flags_unsellable(monkeypatch):
    calls = {"n": 0}

    def fake_quote(inp, outp, amount, slippage_bps=50):
        calls["n"] += 1
        return (
            {"outAmount": "1000", "priceImpactPct": "0.5"} if calls["n"] == 1 else None
        )

    monkeypatch.setattr(jupiter, "quote", fake_quote)
    rt = jupiter.round_trip_quote("Mint1")
    assert rt["buy_route"] is True
    assert rt["sellable"] is False


def test_round_trip_no_buy_route(monkeypatch):
    monkeypatch.setattr(jupiter, "quote", lambda *a, **k: None)
    rt = jupiter.round_trip_quote("Mint1")
    assert rt["buy_route"] is False
    assert rt["sellable"] is None


# ---- connectors ----------------------------------------------------------


def test_connector_status_mapping(monkeypatch):
    monkeypatch.setattr(
        connectors,
        "safe_get_json",
        lambda url, *a, **k: (
            {"price": "1"}
            if "exchange.coinbase" in url
            else ({"data": [1]} if "geckoterminal" in url else [1])
        ),
    )
    monkeypatch.setattr(connectors.solana_rpc, "rpc_alive", lambda *a, **k: True)
    monkeypatch.setattr(connectors.jupiter, "alive", lambda *a, **k: True)
    status = {c["name"]: c["status"] for c in connectors.check_connectors()}
    assert status["Coinbase"] == "CONNECTED"
    assert status["Solana RPC"] == "CONNECTED"
    assert status["Jupiter"] == "CONNECTED"
    assert status["GeckoTerminal"] == "CONNECTED"
    assert status["DexScreener"] == "CONNECTED"
    assert status["Phantom"] == "NOT CONNECTED"


def test_connector_down_is_not_connected(monkeypatch):
    monkeypatch.setattr(connectors, "safe_get_json", lambda url, *a, **k: None)
    monkeypatch.setattr(connectors.solana_rpc, "rpc_alive", lambda *a, **k: False)
    monkeypatch.setattr(connectors.jupiter, "alive", lambda *a, **k: False)
    status = {c["name"]: c["status"] for c in connectors.check_connectors()}
    assert status["Coinbase"] == "NOT CONNECTED"
    assert status["Solana RPC"] == "NOT CONNECTED"
