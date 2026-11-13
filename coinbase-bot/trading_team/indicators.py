"""Technical indicators, pure standard-library Python. No third-party deps.

Inputs are sequences of closing prices (Decimal or float); outputs are floats.
Inspired by common quant skills but implemented from scratch so nothing is
copied and no package is pulled in.
"""

from __future__ import annotations

from typing import Sequence


def _f(values: Sequence) -> list[float]:
    return [float(v) for v in values]


def sma(closes: Sequence, period: int) -> float:
    c = _f(closes)
    if len(c) < period:
        raise ValueError("not enough data for SMA")
    return sum(c[-period:]) / period


def ema(closes: Sequence, period: int) -> float:
    c = _f(closes)
    if len(c) < period:
        raise ValueError("not enough data for EMA")
    k = 2 / (period + 1)
    e = sum(c[:period]) / period
    for price in c[period:]:
        e = price * k + e * (1 - k)
    return e


def rsi(closes: Sequence, period: int = 14) -> float:
    """Relative Strength Index, 0..100."""
    c = _f(closes)
    if len(c) < period + 1:
        raise ValueError("not enough data for RSI")
    gains, losses = [], []
    for i in range(1, len(c)):
        diff = c[i] - c[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - 100 / (1 + rs)


def macd(closes: Sequence, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """MACD line, signal line, histogram."""
    c = _f(closes)
    if len(c) < slow + signal:
        raise ValueError("not enough data for MACD")
    macd_series = []
    for end in range(slow, len(c) + 1):
        window = c[:end]
        macd_series.append(ema(window, fast) - ema(window, slow))
    sig = ema(macd_series, signal) if len(macd_series) >= signal else macd_series[-1]
    line = macd_series[-1]
    return {"macd": line, "signal": sig, "hist": line - sig}


def atr(highs: Sequence, lows: Sequence, closes: Sequence, period: int = 14) -> float:
    """Average True Range — a volatility measure in price units."""
    h, low, c = _f(highs), _f(lows), _f(closes)
    if min(len(h), len(low), len(c)) < period + 1:
        raise ValueError("not enough data for ATR")
    trs = []
    for i in range(1, len(c)):
        trs.append(max(h[i] - low[i], abs(h[i] - c[i - 1]), abs(low[i] - c[i - 1])))
    return sum(trs[-period:]) / period


def bollinger(closes: Sequence, period: int = 20, k: float = 2.0) -> dict:
    """Bollinger bands: middle SMA and upper/lower k-sigma bands."""
    c = _f(closes)
    if len(c) < period:
        raise ValueError("not enough data for Bollinger")
    window = c[-period:]
    mid = sum(window) / period
    var = sum((x - mid) ** 2 for x in window) / period
    sd = var**0.5
    return {"mid": mid, "upper": mid + k * sd, "lower": mid - k * sd, "sd": sd}
