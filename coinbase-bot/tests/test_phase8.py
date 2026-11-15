"""Phase 8 tests: categorisation, MC/FDV, missing supply, dedup, scam flags,
liquidity/slippage, non-sellable veto, partial/failed fills, portfolio metrics.
No network, no real orders."""

from multimarket import (
    ADAPTERS,
    AdapterStatus,
    MarketCapCategory,
    MicroCapPaperBroker,
    Portfolio,
    Token,
    assess_memecoin_risk,
    categorize_market_cap,
    should_veto,
    valuation,
)
from multimarket.core import OnChain, RiskLevel
from multimarket.discovery import TokenScanner


def tok(**kw):
    base = dict(address="Addr1", symbol="X", name="X", network="solana", source="test")
    base.update(kw)
    return Token(**base)


# ---- categorisation / valuation ------------------------------------------


def test_market_cap_categories():
    assert categorize_market_cap(250_000_000) == MarketCapCategory.CAT1_OVER_100M
    assert categorize_market_cap(50_000_000) == MarketCapCategory.CAT2_10M_100M
    assert categorize_market_cap(5_000_000) == MarketCapCategory.CAT3_1M_10M
    assert categorize_market_cap(750_000) == MarketCapCategory.CAT4_500K_1M
    assert categorize_market_cap(250_000) == MarketCapCategory.CAT5_100K_500K
    assert categorize_market_cap(50_000) == MarketCapCategory.CAT6_UNDER_100K
    assert categorize_market_cap(None) == MarketCapCategory.UNKNOWN


def test_valuation_uses_fdv_and_flags_uncertain_when_no_supply():
    t = tok(market_cap_usd=None, fdv_usd=800_000, circulating_supply=None)
    v = valuation(t)
    assert v["basis"] == "fdv"
    assert v["uncertain"] is True
    assert v["category"] == MarketCapCategory.CAT4_500K_1M


def test_valuation_true_mc_not_uncertain():
    t = tok(market_cap_usd=2_000_000, fdv_usd=9_000_000, circulating_supply=1_000_000)
    v = valuation(t)
    assert v["basis"] == "market_cap"
    assert v["uncertain"] is False


# ---- dedup ---------------------------------------------------------------


class _Src:
    def __init__(self, tokens):
        self._t = tokens

    def new_pools(self):
        return self._t


def test_scanner_deduplicates_tokens():
    a = tok(address="Dup", market_cap_usd=1_000_000)
    b = tok(address="Dup", market_cap_usd=1_000_000)
    c = tok(address="Other", market_cap_usd=50_000)
    results = TokenScanner([_Src([a, b]), _Src([c])]).scan()
    assert len(results) == 2


# ---- memecoin risk -------------------------------------------------------


def test_missing_data_is_unknown_not_safe():
    r = assess_memecoin_risk(tok())
    assert r.level == RiskLevel.UNKNOWN
    assert r.veto is False
    assert r.level != RiskLevel.SAFE


def test_honeypot_is_critical_and_vetoes():
    r = assess_memecoin_risk(tok(liquidity_usd=50_000), OnChain(honeypot=True))
    assert r.level == RiskLevel.CRITICAL
    assert should_veto(r) is True
    assert r.sell_feasible is False


def test_no_exit_liquidity_vetoes():
    r = assess_memecoin_risk(
        tok(liquidity_usd=100.0), OnChain(mint_authority_active=False)
    )
    assert r.veto is True
    assert r.sell_feasible is False
    assert "NO_EXIT_LIQUIDITY" in r.flags


def test_active_mint_authority_is_critical():
    r = assess_memecoin_risk(
        tok(liquidity_usd=50_000), OnChain(mint_authority_active=True)
    )
    assert r.level == RiskLevel.CRITICAL
    assert r.veto is True


def test_high_concentration_is_high_risk_no_veto():
    r = assess_memecoin_risk(
        tok(liquidity_usd=50_000),
        OnChain(top_holder_pct=70, mint_authority_active=False),
    )
    assert r.level == RiskLevel.HIGH
    assert r.veto is False


# ---- micro-cap paper broker ----------------------------------------------


def test_insufficient_liquidity_is_no_trade():
    b = MicroCapPaperBroker(min_liquidity_usd=5_000)
    f = b.estimate("BUY", 100, 1.0, liquidity_usd=1_000)
    assert f.status == "no_trade"
    assert f.filled_usd == 0.0


def test_extreme_slippage_fails_order():
    b = MicroCapPaperBroker(
        max_pool_fraction=1.0, max_slippage_pct=5.0, impact_coeff=1.0
    )
    f = b.estimate("BUY", 5_000, 1.0, liquidity_usd=10_000)
    assert f.status == "failed"
    assert f.filled_usd == 0.0


def test_partial_fill_capped_by_pool_fraction():
    b = MicroCapPaperBroker(max_pool_fraction=0.02, max_slippage_pct=50.0)
    f = b.estimate("BUY", 10_000, 1.0, liquidity_usd=100_000)  # cap = 2000
    assert f.status == "partial"
    assert abs(f.filled_usd - 2_000) < 1e-6
    assert f.fee_usd > 0


def test_price_impact_grows_with_size():
    b = MicroCapPaperBroker(max_pool_fraction=1.0, max_slippage_pct=100.0)
    small = b.estimate("BUY", 1_000, 1.0, liquidity_usd=100_000)
    big = b.estimate("BUY", 10_000, 1.0, liquidity_usd=100_000)
    assert big.price_impact_pct > small.price_impact_pct


def test_buy_slips_up_sell_slips_down():
    b = MicroCapPaperBroker(max_pool_fraction=1.0, max_slippage_pct=100.0)
    buy = b.estimate("BUY", 1_000, 1.0, liquidity_usd=100_000)
    sell = b.estimate("SELL", 1_000, 1.0, liquidity_usd=100_000)
    assert buy.avg_price > 1.0 > sell.avg_price


# ---- adapters ------------------------------------------------------------


def test_no_adapter_is_live_ready_and_coinbase_is_paper():
    by_name = {a.name: a for a in ADAPTERS}
    assert by_name["coinbase_spot"].status == AdapterStatus.PAPER
    assert all(a.status != AdapterStatus.LIVE_READY for a in ADAPTERS)
    assert by_name["solana_dex_paper"].status == AdapterStatus.PAPER
    assert by_name["jupiter_quote"].status == AdapterStatus.READ_ONLY


# ---- portfolio metrics ---------------------------------------------------


def test_portfolio_metrics_count_failed_orders():
    p = Portfolio("D", "microcap", cash_usd=17.10)
    p.record({"pnl": 0.5, "status": "filled"})
    p.record({"pnl": -0.2, "status": "filled"})
    p.record({"status": "no_trade"})
    p.record({"status": "failed"})
    m = p.metrics()
    assert m["trades"] == 2
    assert m["failed_or_no_trade"] == 2
    assert 0 <= m["win_rate_pct"] <= 100
