"""Backtesting and strategy validation (Phase 3), dependency-free.

Provides: a historical backtest with taker fees and slippage, max-drawdown,
an in-sample / out-of-sample split, walk-forward evaluation, and a simple
overfitting check (in-sample performance that does not carry over out of
sample). Works on real candle closes passed in by the caller — no invented
data.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

# A strategy maps a window of closes -> desired stance for the next bar.
Strategy = Callable[[list], str]  # returns "BUY" | "SELL" | "HOLD"


@dataclass(frozen=True)
class BacktestResult:
    bars: int
    trades: int
    return_pct: float
    max_drawdown_pct: float
    fees_paid: float
    final_equity: float


def backtest(
    closes: list,
    strategy: Strategy,
    *,
    warmup: int = 30,
    fee_rate: float = 0.001,
    slippage_rate: float = 0.0005,
    start_cash: float = 100.0,
) -> BacktestResult:
    """Long-flat backtest. Buys the full book on BUY, sells all on SELL.
    Fees and slippage apply on every fill."""
    prices = [float(c) for c in closes]
    cash, units, fees, trades = start_cash, 0.0, 0.0, 0
    peak_equity = start_cash
    max_dd = 0.0
    for i in range(warmup, len(prices)):
        window = prices[: i + 1]
        price = prices[i]
        stance = strategy(window)
        if stance == "BUY" and units == 0.0 and cash > 0:
            exec_price = price * (1 + slippage_rate)
            fee = cash * fee_rate
            units = (cash - fee) / exec_price
            fees += fee
            cash = 0.0
            trades += 1
        elif stance == "SELL" and units > 0:
            exec_price = price * (1 - slippage_rate)
            gross = units * exec_price
            fee = gross * fee_rate
            cash = gross - fee
            fees += fee
            units = 0.0
            trades += 1
        equity = cash + units * price
        peak_equity = max(peak_equity, equity)
        if peak_equity > 0:
            max_dd = max(max_dd, (peak_equity - equity) / peak_equity)
    final_equity = cash + units * prices[-1]
    return BacktestResult(
        bars=len(prices) - warmup,
        trades=trades,
        return_pct=(final_equity / start_cash - 1) * 100,
        max_drawdown_pct=max_dd * 100,
        fees_paid=fees,
        final_equity=final_equity,
    )


def split_in_out_of_sample(closes: list, in_fraction: float = 0.7) -> tuple[list, list]:
    cut = int(len(closes) * in_fraction)
    return closes[:cut], closes[cut:]


@dataclass(frozen=True)
class OverfitReport:
    in_sample_return: float
    out_of_sample_return: float
    degradation_pct: float
    likely_overfit: bool


def overfitting_check(
    closes: list,
    strategy: Strategy,
    *,
    in_fraction: float = 0.7,
    warmup: int = 30,
    degradation_threshold: float = 50.0,
) -> OverfitReport:
    """Compares in-sample and out-of-sample returns. A big drop out of sample
    flags likely overfitting."""
    in_s, out_s = split_in_out_of_sample(closes, in_fraction)
    r_in = backtest(in_s, strategy, warmup=warmup).return_pct
    r_out = backtest(
        out_s, strategy, warmup=min(warmup, max(len(out_s) // 2, 1))
    ).return_pct
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
    closes: list, strategy: Strategy, *, folds: int = 4, warmup: int = 30
) -> WalkForwardResult:
    """Splits the series into sequential out-of-sample folds and backtests each."""
    n = len(closes)
    size = n // folds
    if size < 10:
        raise ValueError("series too short for this many folds")
    returns = []
    for i in range(folds):
        segment = (
            closes[i * size : (i + 1) * size] if i < folds - 1 else closes[i * size :]
        )
        # Warm up on at most half a fold so each fold leaves bars to trade on.
        eff_warmup = min(warmup, max(len(segment) // 2, 5))
        returns.append(backtest(segment, strategy, warmup=eff_warmup).return_pct)
    return WalkForwardResult(folds, returns, sum(returns) / len(returns), min(returns))
