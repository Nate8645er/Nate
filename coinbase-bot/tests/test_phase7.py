"""Phase 7 regression tests: no look-ahead, forced final close, and that every
candidate strategy runs and reconciles. No network, no real orders."""

from trading_team import backtest
from trading_team.strategies import ALL_STRATEGIES


def bar(o, h, l, c, v=1.0):
    return {"o": o, "h": h, "l": l, "c": c, "v": v}


def test_fill_happens_at_next_bar_open_not_signal_bar():
    # Signal fires on bar 1 (close 100); next bar opens at 110. A same-bar fill
    # would buy at 100; the correct next-open fill buys at ~110.
    bars = [bar(100, 100, 100, 100), bar(100, 100, 100, 100), bar(110, 125, 108, 120)]

    def always_buy(window):
        return "BUY"

    res = backtest.simulate_bars(
        bars, always_buy, warmup=1, fee_rate=0.0, slippage_rate=0.0
    )
    # Bought at next open 110, force-closed at last close 120 -> ~9.09%.
    assert 8.0 < res.return_pct < 10.5
    # A same-bar (100) fill would have produced ~20%, which must NOT happen.
    assert res.return_pct < 15.0


def test_open_position_is_force_closed_and_metrics_reconcile():
    bars = [bar(100, 100, 100, 100)] * 2 + [
        bar(100, 100, 100, 100 + i) for i in range(1, 20)
    ]

    def buy_and_hold(window):
        return "BUY"

    res = backtest.simulate_bars(
        bars, buy_and_hold, warmup=1, fee_rate=0.0, slippage_rate=0.0
    )
    assert res.trades == 1  # the forced final close counts as one completed trade
    assert abs(res.net_pnl - (res.final_equity - 100.0)) < 1e-9


def test_sol_paradox_resolved_losing_hold_is_not_100pct_winrate():
    # Up then crash; buy-and-hold must end negative AND not show 100% win rate.
    up = [bar(100 + i, 100 + i, 100 + i, 100 + i) for i in range(40)]
    crash = [bar(140 - i * 5, 140, 60, 140 - i * 5) for i in range(16)]
    bars = up + crash

    def buy_and_hold(window):
        return "BUY"

    res = backtest.simulate_bars(
        bars, buy_and_hold, warmup=5, fee_rate=0.001, slippage_rate=0.0005
    )
    assert res.net_pnl < 0
    assert res.win_rate_pct < 100.0  # the contradiction is gone


def test_every_candidate_strategy_runs_and_reconciles():
    # Deterministic pseudo-random-ish OHLCV series.
    bars = []
    price = 100.0
    for i in range(400):
        price *= 1 + (0.02 if i % 7 < 4 else -0.025)
        o = price * 0.999
        bars.append(bar(o, price * 1.01, price * 0.98, price, v=1000 + (i % 10) * 100))
    for name, strat in ALL_STRATEGIES.items():
        res = backtest.simulate_bars(bars, strat, warmup=60)
        assert res.bars > 0, name
        assert res.profit_factor >= 0.0, name
        assert abs(res.net_pnl - (res.final_equity - 100.0)) < 1e-6, name
        assert 0.0 <= res.win_rate_pct <= 100.0, name


def test_walk_forward_and_overfit_accept_bars_mode():
    bars = [bar(100 + i, 100 + i, 100 + i, 100 + i, v=1000) for i in range(120)]
    strat = ALL_STRATEGIES["macd_trend"]
    wf = backtest.walk_forward(bars, strat, folds=3, warmup=30, bars_mode=True)
    assert wf.folds == 3
    of = backtest.overfitting_check(bars, strat, warmup=30, bars_mode=True)
    assert hasattr(of, "likely_overfit")
