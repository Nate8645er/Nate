"""Candidate strategies for Phase 7 research (dependency-free).

Each strategy takes a window of completed OHLCV bars (dicts with o,h,l,c,v)
and returns "BUY" | "SELL" | "HOLD". They are stateless: the backtester owns
position state and fills at the next bar's open, so there is no look-ahead.
"""

from __future__ import annotations

from . import indicators as ind


def _c(bars: list) -> list:
    return [b["c"] for b in bars]


def macd_trend(bars: list, slow: int = 26) -> str:
    """MACD histogram with an SMA trend filter (long only above the SMA)."""
    closes = _c(bars)
    if len(closes) < slow + 9:
        return "HOLD"
    m = ind.macd(closes)
    trend_up = closes[-1] > ind.sma(closes, slow)
    if m["hist"] > 0 and trend_up:
        return "BUY"
    if m["hist"] < 0 or not trend_up:
        return "SELL"
    return "HOLD"


def breakout_volume(bars: list, lookback: int = 20, vol_mult: float = 1.3) -> str:
    """Donchian-style breakout confirmed by above-average volume."""
    if len(bars) < lookback + 1:
        return "HOLD"
    window = bars[-(lookback + 1) : -1]
    highs = [b["h"] for b in window]
    lows = [b["l"] for b in window]
    vols = [b["v"] for b in window]
    avg_vol = sum(vols) / len(vols) if vols else 0.0
    last = bars[-1]
    if last["c"] > max(highs) and (avg_vol == 0 or last["v"] > avg_vol * vol_mult):
        return "BUY"
    if last["c"] < min(lows):
        return "SELL"
    return "HOLD"


def rsi_trend(bars: list, period: int = 14, low: float = 40, long_ma: int = 50) -> str:
    """RSI pullback, but only long while price is above a long SMA (trend filter)."""
    closes = _c(bars)
    if len(closes) < max(period + 1, long_ma):
        return "HOLD"
    r = ind.rsi(closes, period)
    trend_up = closes[-1] > ind.sma(closes, long_ma)
    if r < low and trend_up:
        return "BUY"
    if not trend_up or r > 70:
        return "SELL"
    return "HOLD"


def ema_atr_stop(
    bars: list, fast: int = 12, slow: int = 26, atr_mult: float = 2.0
) -> str:
    """EMA trend entry; exit when price falls an ATR multiple below the fast EMA
    (a stateless trailing-stop proxy) or the EMA trend turns down."""
    closes = _c(bars)
    if len(closes) < slow + 1 or len(bars) < 15:
        return "HOLD"
    ef, es = ind.ema(closes, fast), ind.ema(closes, slow)
    a = ind.atr([b["h"] for b in bars], [b["l"] for b in bars], closes)
    if ef > es and closes[-1] > ef - atr_mult * a:
        return "BUY"
    if ef < es or closes[-1] < ef - atr_mult * a:
        return "SELL"
    return "HOLD"


def momentum_vol_filter(
    bars: list, ma: int = 30, mom_thr: float = 0.01, vol_cap: float = 0.05
) -> str:
    """Momentum entry, suppressed when realised volatility is too high."""
    closes = _c(bars)
    if len(closes) < ma + 1:
        return "HOLD"
    base = ind.sma(closes, ma)
    momentum = closes[-1] / base - 1 if base else 0.0
    rets = [
        (closes[i] - closes[i - 1]) / closes[i - 1]
        for i in range(1, len(closes))
        if closes[i - 1]
    ]
    recent = rets[-ma:]
    mean = sum(recent) / len(recent)
    vol = (sum((x - mean) ** 2 for x in recent) / len(recent)) ** 0.5
    if momentum > mom_thr and vol < vol_cap:
        return "BUY"
    if momentum < 0:
        return "SELL"
    return "HOLD"


def mean_reversion(bars: list, period: int = 20, k: float = 2.0) -> str:
    """Bollinger mean reversion: buy the lower band, sell the upper band."""
    closes = _c(bars)
    if len(closes) < period:
        return "HOLD"
    b = ind.bollinger(closes, period, k)
    price = closes[-1]
    if price <= b["lower"]:
        return "BUY"
    if price >= b["upper"]:
        return "SELL"
    return "HOLD"


def multi_signal(bars: list) -> str:
    """Combine three independent signals; trade only on a majority."""
    votes = [macd_trend(bars), rsi_trend(bars), momentum_vol_filter(bars)]
    buys = votes.count("BUY")
    sells = votes.count("SELL")
    if buys >= 2 and buys > sells:
        return "BUY"
    if sells >= 2 and sells > buys:
        return "SELL"
    return "HOLD"


ALL_STRATEGIES = {
    "macd_trend": macd_trend,
    "breakout_volume": breakout_volume,
    "rsi_trend": rsi_trend,
    "ema_atr_stop": ema_atr_stop,
    "momentum_vol_filter": momentum_vol_filter,
    "mean_reversion": mean_reversion,
    "multi_signal": multi_signal,
}
