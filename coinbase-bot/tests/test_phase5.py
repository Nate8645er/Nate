"""Phase 5/7 tests: indicators, collaborative debate, backtest validation,
capital ceiling. No network, no real orders."""

from decimal import Decimal as D

from trading_team import (
    CAPITAL_LIMIT_USDC,
    DebateRoom,
    MarketAnalyst,
    RiskConfig,
    RiskManager,
    backtest,
    collaborative_cycle,
    indicators,
    paper_risk_config,
)
from trading_team.collaboration import Opinion


def uptrend(n=60, start=100.0, step=0.5):
    return [D(str(start + i * step)) for i in range(n)]


def downtrend(n=60, start=130.0, step=0.5):
    return [D(str(start - i * step)) for i in range(n)]


def choppy(n=60):
    return [D(str(100 + (i % 2) * 2)) for i in range(n)]


# ---- indicators ----------------------------------------------------------


def test_rsi_bounds_and_direction():
    assert indicators.rsi(uptrend()) > 70
    assert indicators.rsi(downtrend()) < 30
    assert 0 <= indicators.rsi(choppy()) <= 100


def test_macd_and_bollinger_shapes():
    m = indicators.macd(uptrend())
    assert set(m) == {"macd", "signal", "hist"}
    b = indicators.bollinger(uptrend())
    assert b["lower"] < b["mid"] < b["upper"]


# ---- collaboration (Phase 7.1, 7.2, 7.3, 7.7) ----------------------------


def test_all_voices_see_same_data_and_can_disagree():
    room = DebateRoom()
    report = MarketAnalyst().analyse("BTC-USDC", uptrend())
    consensus = room.deliberate(report, uptrend())
    assert len(consensus.opinions) == len(room.voices)
    assert consensus.challenges  # non-empty -> genuine disagreement recorded


def test_risk_manager_can_veto_consensus_buy():
    room = DebateRoom()
    analyst = MarketAnalyst()
    risk = RiskManager(
        RiskConfig(allocated_capital_usdc=D("0.5"), min_order_usdc=D("1"))
    )
    rec = collaborative_cycle("BTC-USDC", uptrend(), analyst, risk, room)
    if rec["signal"] == "BUY":
        assert rec["decision"] == "rejected_by_risk"
        assert rec["risk_approved"] is False


def test_team_accepts_no_trade_on_chop():
    room = DebateRoom()
    analyst = MarketAnalyst()
    risk = RiskManager(paper_risk_config())
    rec = collaborative_cycle("BTC-USDC", choppy(), analyst, risk, room)
    assert rec["decision"] in {"no_trade", "rejected_by_risk"}


def test_emergency_stop_blocks_collaborative_buy():
    room = DebateRoom()
    analyst = MarketAnalyst()
    risk = RiskManager(paper_risk_config())
    risk.emergency_stop("Not-Aus Test")
    rec = collaborative_cycle("BTC-USDC", uptrend(), analyst, risk, room)
    assert rec["decision"] != "prepare_buy"


def test_custom_voices_feed_the_same_report():
    seen = []

    def spy(report, closes):
        seen.append(id(report))
        return Opinion("Spy", "HOLD", D("0.5"), "x")

    room = DebateRoom(voices=[spy, spy, spy])
    report = MarketAnalyst().analyse("BTC-USDC", uptrend())
    room.deliberate(report, uptrend())
    assert len(set(seen)) == 1  # identical report object handed to all voices


# ---- backtest / validation (Phase 3) -------------------------------------


def sma_cross(window, fast=10, slow=30):
    if len(window) < slow:
        return "HOLD"
    f = sum(window[-fast:]) / fast
    s = sum(window[-slow:]) / slow
    return "BUY" if f > s else "SELL"


def test_backtest_counts_fees_and_trades():
    res = backtest.backtest(uptrend() + downtrend(), sma_cross)
    assert res.trades >= 1
    assert res.fees_paid > 0
    assert res.max_drawdown_pct >= 0


def test_walk_forward_runs_each_fold():
    wf = backtest.walk_forward(
        uptrend() + downtrend() + uptrend(), sma_cross, folds=3, warmup=10
    )
    assert wf.folds == 3
    assert len(wf.fold_returns) == 3


def test_overfitting_check_reports_degradation():
    report = backtest.overfitting_check(uptrend() + downtrend(), sma_cross, warmup=10)
    assert hasattr(report, "likely_overfit")
    assert report.in_sample_return is not None


def test_backtest_reports_winrate_and_profit_factor():
    res = backtest.backtest(uptrend() + downtrend() + uptrend(), sma_cross, warmup=10)
    assert res.trades >= 1
    assert 0.0 <= res.win_rate_pct <= 100.0
    assert res.profit_factor >= 0.0
    # net P&L must reconcile with final equity vs the 100 start cash
    assert abs(res.net_pnl - (res.final_equity - 100.0)) < 1e-6
    # gross profit/loss consistency
    assert res.gross_profit >= 0 and res.gross_loss >= 0


# ---- capital ceiling (Phase 5) -------------------------------------------


def test_capital_ceiling_is_17_10_and_live_off():
    assert CAPITAL_LIMIT_USDC == D("17.10")
    cfg = paper_risk_config()
    assert cfg.allocated_capital_usdc == D("17.10")
    assert cfg.absolute_max_loss_usdc == D("17.10")
    assert cfg.live_allowed() is False  # LIVE stays disabled


def test_risk_manager_cannot_raise_absolute_ceiling_via_tighten():
    risk = RiskManager(paper_risk_config())
    risk.tighten(daily_loss_limit=D("100"), max_position_fraction=D("5"))
    assert risk.config.absolute_max_loss_usdc == D("17.10")
    assert risk.config.max_position_fraction <= D("1.0")
    assert risk.config.daily_loss_limit_usdc <= D("2.00")
