"""Backtesting and strategy validation, dependency-free.

Correctness guarantees (Phase 7 hardening):
  * No look-ahead. The signal at bar i is computed from completed candles only
    (bars[:i+1]); the resulting fill happens at bar i+1's OPEN, never on the
    same candle that produced the signal and never on a future candle's close.
  * Every open position is force-closed at the last candle so realised-trade
    metrics (win rate, profit factor) reconcile with net P&L — no silent
    open position inflating or masking the result.
  * Taker fee and slippage apply on every fill.

Works on real candles passed in by the caller — no invented data. Two entry
points: `backtest(closes, strategy)` for close-only strategies, and
`simulate_bars(bars, strategy)` for OHLCV strategies (bars are dicts with
keys o, h, l, c, v as floats).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# Close-only strategy: window of closes -> stance. OHLCV strategy: window of
# bar dicts -> stance. Both return "BUY" | "SELL" | "HOLD".
Strategy = Callable[[list], str]


@dataclass(frozen=True)
class BacktestResult:
    bars: int
    trades: int  # completed round trips (entry -> exit), incl. forced final close
    return_pct: float
    max_drawdown_pct: float
    fees_paid: float
    final_equity: float
    win_rate_pct: float = 0.0
    profit_factor: float = 0.0  # gross profit / gross loss; inf -> 999
    net_pnl: float = 0.0
    gross_profit: float = 0.0
    gross_loss: float = 0.0


def _closes_to_bars(closes: list) -> list[dict]:
    out = []
    for c in closes:
        p = float(c)
        out.append({"o": p, "h": p, "l": p, "c": p, "v": 0.0})
    return out


def simulate_bars(
    bars: list[dict],
    strategy: Strategy,
    *,
    warmup: int = 30,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    start_cash: float = 100.0,
) -> BacktestResult:
    """Long-flat simulation over OHLCV bars. Signal on completed bar i, fill at
    bar i+1 open. Any open position is closed at the final bar's close."""
    n = len(bars)
    cash, units, fees = start_cash, 0.0, 0.0
    entry_cost = 0.0
    peak_equity = start_cash
    max_dd = 0.0
    round_trips: list[float] = []

    def mark(price: float) -> None:
        nonlocal peak_equity, max_dd
        equity = cash + units * price
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            max_dd = max(max_dd, (peak_equity - equity) / peak_equity)

    # Decide on bar i (completed), act on bar i+1 open. Stop at n-1 so i+1 exists.
    for i in range(warmup, n - 1):
        stance = strategy(bars[: i + 1])
        fill_open = bars[i + 1]["o"]
        if stance == "BUY" and units == 0.0 and cash > 0:
            exec_price = fill_open * (1 + slippage_rate)
            fee = cash * fee_rate
            entry_cost = cash
            units = (cash - fee) / exec_price
            fees += fee
            cash = 0.0
        elif stance == "SELL" and units > 0:
            exec_price = fill_open * (1 - slippage_rate)
            gross = units * exec_price
            fee = gross * fee_rate
            cash = gross - fee
            fees += fee
            round_trips.append(cash - entry_cost)
            units = 0.0
            entry_cost = 0.0
        mark(bars[i + 1]["c"])

    # Force-close any open position at the last close.
    if units > 0:
        last = bars[-1]["c"]
        gross = units * last * (1 - slippage_rate)
        fee = gross * fee_rate
        cash = gross - fee
        fees += fee
        round_trips.append(cash - entry_cost)
        units = 0.0

    final_equity = cash
    wins = [p for p in round_trips if p > 0]
    losses = [p for p in round_trips if p < 0]
    gross_profit = sum(wins)
    gross_loss = -sum(losses)
    trades = len(round_trips)
    win_rate = (len(wins) / trades * 100) if trades else 0.0
    if gross_loss > 0:
        profit_factor = gross_profit / gross_loss
    else:
        profit_factor = 999.0 if gross_profit > 0 else 0.0
    return BacktestResult(
        bars=max(n - warmup, 0),
        trades=trades,
        return_pct=(final_equity / start_cash - 1) * 100,
        max_drawdown_pct=max_dd * 100,
        fees_paid=fees,
        final_equity=final_equity,
        win_rate_pct=win_rate,
        profit_factor=profit_factor,
        net_pnl=final_equity - start_cash,
        gross_profit=gross_profit,
        gross_loss=gross_loss,
    )


def backtest(
    closes: list,
    strategy: Strategy,
    *,
    warmup: int = 30,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    start_cash: float = 100.0,
) -> BacktestResult:
    """Close-only convenience wrapper around simulate_bars. The strategy still
    receives a window of closes; fills use the next bar (next close, since this
    path has no separate open)."""
    bars = _closes_to_bars(closes)

    def bar_strategy(window: list) -> str:
        return strategy([b["c"] for b in window])

    return simulate_bars(
        bars,
        bar_strategy,
        warmup=warmup,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        start_cash=start_cash,
    )


def split_in_out_of_sample(seq: list, in_fraction: float = 0.7) -> tuple[list, list]:
    cut = int(len(seq) * in_fraction)
    return seq[:cut], seq[cut:]


@dataclass(frozen=True)
class OverfitReport:
    in_sample_return: float
    out_of_sample_return: float
    degradation_pct: float
    likely_overfit: bool


def _return_pct(seq: list, strategy: Strategy, warmup: int, bars_mode: bool) -> float:
    fn = simulate_bars if bars_mode else backtest
    return fn(seq, strategy, warmup=warmup).return_pct


def overfitting_check(
    seq: list,
    strategy: Strategy,
    *,
    in_fraction: float = 0.7,
    warmup: int = 30,
    degradation_threshold: float = 50.0,
    bars_mode: bool = False,
) -> OverfitReport:
    """Compares in-sample and out-of-sample returns. A big drop out of sample,
    or an out-of-sample loss after an in-sample gain, flags overfitting."""
    in_s, out_s = split_in_out_of_sample(seq, in_fraction)
    r_in = _return_pct(in_s, strategy, warmup, bars_mode)
    r_out = _return_pct(
        out_s, strategy, min(warmup, max(len(out_s) // 2, 1)), bars_mode
    )
    if r_in <= 0:
        degradation = 0.0 if r_out >= r_in else 100.0
    else:
        degradation = max(0.0, (r_in - r_out) / abs(r_in) * 100)
    overfit = r_in > 0 and (r_out < 0 or degradation > degradation_threshold)
    return OverfitReport(r_in, r_out, degradation, overfit)


@dataclass(frozen=True)
class WalkForwardResult:
    folds: int
    fold_returns: list
    mean_return: float
    worst_return: float


def walk_forward(
    seq: list,
    strategy: Strategy,
    *,
    folds: int = 4,
    warmup: int = 30,
    bars_mode: bool = False,
) -> WalkForwardResult:
    """Splits the series into sequential out-of-sample folds and backtests each."""
    n = len(seq)
    size = n // folds
    if size < 10:
        raise ValueError("series too short for this many folds")
    returns = []
    for i in range(folds):
        segment = seq[i * size : (i + 1) * size] if i < folds - 1 else seq[i * size :]
        eff_warmup = min(warmup, max(len(segment) // 2, 5))
        returns.append(_return_pct(segment, strategy, eff_warmup, bars_mode))
    return WalkForwardResult(folds, returns, sum(returns) / len(returns), min(returns))
