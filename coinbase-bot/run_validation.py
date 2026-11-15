"""Phase 6 strategy validation on longer REAL Coinbase history.

Paper only, public candles (no key). Computes win rate, profit factor, net
P&L, max drawdown and trade count; runs walk-forward and an out-of-sample
overfitting check across whatever market phases the history contains; then
lets the debate room argue the verdict. Prints NO TRADE if nothing is robust.

    python run_validation.py
"""

import time
from decimal import Decimal as D

from coinbase.rest import RESTClient

from trading_team import (
    DebateRoom,
    MarketAnalyst,
    RiskManager,
    backtest,
    indicators,
    paper_risk_config,
)

FEE = 0.001  # Coinbase taker on USDC pairs
SLIP = 0.0005
GRAN = "SIX_HOUR"
GRAN_SECONDS = 6 * 3600


def history(client: RESTClient, product_id: str, n: int = 300) -> list:
    end = int(time.time())
    start = end - GRAN_SECONDS * (n + 1)
    resp = client.get_public_candles(
        product_id=product_id,
        start=str(start),
        end=str(end),
        granularity=GRAN,
        limit=n,
    ).to_dict()
    candles = sorted(resp["candles"], key=lambda c: int(c["start"]))
    return [D(c["close"]) for c in candles]


# --- strategies (see only past window; act on the window's last close) ----


def sma_cross(window, fast=10, slow=30):
    if len(window) < slow:
        return "HOLD"
    f = sum(window[-fast:]) / fast
    s = sum(window[-slow:]) / slow
    return "BUY" if f > s else "SELL"


def rsi_reversion(window, period=14, low=35, high=65):
    if len(window) < period + 1:
        return "HOLD"
    r = indicators.rsi(window, period)
    if r < low:
        return "BUY"
    if r > high:
        return "SELL"
    return "HOLD"


STRATEGIES = {"sma_cross": sma_cross, "rsi_reversion": rsi_reversion}


def phases(closes: list) -> str:
    """Rough description of the market phases contained in the series."""
    first, last = float(closes[0]), float(closes[-1])
    hi, lo = max(float(c) for c in closes), min(float(c) for c in closes)
    drift = (last / first - 1) * 100
    span = (hi / lo - 1) * 100
    direction = "up" if drift > 5 else "down" if drift < -5 else "sideways"
    return f"{direction} (drift {drift:+.1f}%, range {span:.1f}%)"


def robust(bt, wf, of) -> bool:
    return (
        bt.trades >= 5
        and bt.profit_factor > 1.1
        and not of.likely_overfit
        and of.out_of_sample_return > 0
        and wf.mean_return > 0
        and wf.worst_return > -10
    )


def main() -> int:
    client = RESTClient()
    products = ["BTC-USDC", "ETH-USDC", "SOL-USDC"]
    cfg = paper_risk_config()
    print(
        f"Capital ceiling: {cfg.allocated_capital_usdc} USDC | live_allowed={cfg.live_allowed()}"
    )
    passed = []
    for product in products:
        closes = history(client, product)
        print(
            f"\n=== {product} | {len(closes)} x 6h candles | phases: {phases(closes)} ==="
        )
        for name, strat in STRATEGIES.items():
            bt = backtest.backtest(
                closes, strat, warmup=30, fee_rate=FEE, slippage_rate=SLIP
            )
            of = backtest.overfitting_check(closes, strat, warmup=30)
            try:
                wf = backtest.walk_forward(closes, strat, folds=4, warmup=30)
                wf_txt = f"mean {wf.mean_return:+.2f}% worst {wf.worst_return:+.2f}%"
            except ValueError:
                wf = None
                wf_txt = "n/a"
            ok = robust(bt, wf, of) if wf else False
            print(
                f"  {name:14} trades={bt.trades:2d} win%={bt.win_rate_pct:5.1f} "
                f"PF={bt.profit_factor:5.2f} net={bt.net_pnl:+6.2f} "
                f"ret={bt.return_pct:+6.2f}% maxDD={bt.max_drawdown_pct:5.2f}% "
                f"| OOS={of.out_of_sample_return:+.2f}% overfit={of.likely_overfit} "
                f"| WF {wf_txt} -> {'ROBUST' if ok else 'reject'}"
            )
            if ok:
                passed.append((product, name))

    print("\n--- Team-Debatte ueber die Ergebnisse ---")
    analyst, risk, room = MarketAnalyst(), RiskManager(cfg), DebateRoom()
    for product in products:
        short = history(client, product, 120)
        rec = room.deliberate(analyst.analyse(product, short), short)
        counter = "; ".join(rec.challenges) or "keine"
        print(
            f"  {product}: Konsens {rec.stance} (agreed={rec.agreed}) | Gegenargumente: {counter}"
        )

    print("\n=== VERDICT ===")
    if passed:
        for p, s in passed:
            print(f"ROBUST auf ungesehenen Daten: {s} @ {p}")
    else:
        print(
            "NO TRADE — keine Strategie besteht die Out-of-Sample-/Walk-Forward-Pruefung."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
