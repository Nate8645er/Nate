"""Tests for the HyperGrok trading team: risk limits, emergency stop,
position sizing, and paper P&L. No network, no real orders."""

from decimal import Decimal as D

from trading_team import (
    ExecutionAgent,
    MarketAnalyst,
    PaperBroker,
    RiskConfig,
    RiskManager,
    Signal,
    Strategist,
    Supervisor,
    TradeReviewer,
)


def uptrend(n=40, start=100.0, step=0.5):
    return [D(str(start + i * step)) for i in range(n)]


def downtrend(n=40, start=120.0, step=0.5):
    return [D(str(start - i * step)) for i in range(n)]


def build(config, cash="1000"):
    broker = PaperBroker(cash_usdc=D(cash), taker_fee_rate=config.taker_fee_rate)
    risk = RiskManager(config)
    execution = ExecutionAgent(config, broker)
    reviewer = TradeReviewer()
    sup = Supervisor(config, MarketAnalyst(), Strategist(), risk, execution, reviewer)
    return sup, broker, risk, reviewer


def test_analyst_detects_uptrend():
    report = MarketAnalyst().analyse("BTC-USDC", uptrend())
    assert report.trend == "up"
    assert report.momentum > 0


def test_live_disabled_until_limits_confirmed():
    assert RiskConfig(absolute_max_loss_usdc=D("5")).live_allowed() is False
    assert RiskConfig(limits_confirmed=True).live_allowed() is False
    assert (
        RiskConfig(limits_confirmed=True, absolute_max_loss_usdc=D("5")).live_allowed()
        is True
    )


def test_risk_manager_never_raises_absolute_loss_limit():
    risk = RiskManager(
        RiskConfig(absolute_max_loss_usdc=D("5"), daily_loss_limit_usdc=D("3"))
    )
    assert risk.config.daily_loss_limit_usdc == D("3")
    risk.tighten(daily_loss_limit=D("2"))
    assert risk.config.daily_loss_limit_usdc == D("2")
    assert risk.config.absolute_max_loss_usdc == D("5")
    risk.tighten(daily_loss_limit=D("4"))
    assert risk.config.daily_loss_limit_usdc == D("2")


def test_daily_limit_clamped_to_absolute_at_construction():
    risk = RiskManager(
        RiskConfig(absolute_max_loss_usdc=D("5"), daily_loss_limit_usdc=D("99"))
    )
    assert risk.config.daily_loss_limit_usdc == D("5")


def test_position_sizing_supports_full_capital():
    cfg = RiskConfig(
        allocated_capital_usdc=D("100"),
        max_position_fraction=D("1.0"),
        min_order_usdc=D("1"),
    )
    risk = RiskManager(cfg)
    sig = Signal(
        "BTC-USDC",
        "BUY",
        "test",
        entry=D("100"),
        stop_loss=D("98"),
        size_fraction=D("1.0"),
    )
    d = risk.evaluate(sig)
    assert d.approved and d.quote_size_usdc == D("100.00")


def test_order_below_minimum_rejected():
    cfg = RiskConfig(allocated_capital_usdc=D("100"), min_order_usdc=D("10"))
    risk = RiskManager(cfg)
    sig = Signal(
        "BTC-USDC",
        "BUY",
        "t",
        entry=D("100"),
        stop_loss=D("98"),
        size_fraction=D("0.05"),
    )
    assert risk.evaluate(sig).approved is False


def test_trade_rejected_when_risk_exceeds_remaining_budget():
    cfg = RiskConfig(
        allocated_capital_usdc=D("100"),
        absolute_max_loss_usdc=D("1"),
        limits_confirmed=True,
        max_position_fraction=D("1.0"),
    )
    risk = RiskManager(cfg)
    sig = Signal(
        "BTC-USDC",
        "BUY",
        "t",
        entry=D("100"),
        stop_loss=D("98"),
        size_fraction=D("1.0"),
    )
    assert risk.evaluate(sig).approved is False


def test_emergency_stop_blocks_new_buys():
    cfg = RiskConfig(allocated_capital_usdc=D("100"))
    risk = RiskManager(cfg)
    risk.emergency_stop("manuell")
    sig = Signal(
        "BTC-USDC",
        "BUY",
        "t",
        entry=D("100"),
        stop_loss=D("98"),
        size_fraction=D("0.5"),
    )
    assert risk.evaluate(sig).approved is False


def test_absolute_loss_triggers_halt():
    risk = RiskManager(RiskConfig(absolute_max_loss_usdc=D("5")))
    risk.record_loss(D("5"))
    assert risk.halted is True


def test_paper_round_trip_accounts_for_fees():
    broker = PaperBroker(cash_usdc=D("100"), taker_fee_rate=D("0.001"))
    reviewer = TradeReviewer()
    reviewer.record(broker.market_buy("BTC-USDC", D("50"), D("100")))
    reviewer.record(
        broker.market_sell("BTC-USDC", broker.positions["BTC-USDC"], D("100"))
    )
    pnl = reviewer.round_trip_pnl("BTC-USDC")
    assert pnl < 0
    assert abs(pnl) < D("0.2")


def test_supervisor_paper_cycle_buys_on_uptrend_then_holds():
    cfg = RiskConfig(allocated_capital_usdc=D("100"), max_position_fraction=D("1.0"))
    sup, broker, risk, reviewer = build(cfg)
    first = sup.run_cycle("BTC-USDC", uptrend(), mode="paper")
    assert first["action"] == "paper_filled"
    assert broker.positions["BTC-USDC"] > 0
    second = sup.run_cycle("BTC-USDC", uptrend(), mode="paper")
    assert second["action"] == "flat"


def test_supervisor_live_mode_falls_back_to_paper_when_not_confirmed():
    cfg = RiskConfig(allocated_capital_usdc=D("100"), max_position_fraction=D("1.0"))
    sup, broker, risk, reviewer = build(cfg)
    result = sup.run_cycle("BTC-USDC", uptrend(), mode="live")
    assert result["action"] == "paper_filled"
    assert "Live gesperrt" in result["note"]


def test_supervisor_sells_on_trend_reversal():
    cfg = RiskConfig(allocated_capital_usdc=D("100"), max_position_fraction=D("1.0"))
    sup, broker, risk, reviewer = build(cfg)
    sup.run_cycle("BTC-USDC", uptrend(), mode="paper")
    assert broker.positions["BTC-USDC"] > 0
    out = sup.run_cycle("BTC-USDC", downtrend(), mode="paper")
    assert out["action"] == "paper_filled"
    assert broker.positions.get("BTC-USDC", D("0")) == 0
