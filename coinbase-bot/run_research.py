"""Phase 7 advanced strategy research on multi-year REAL daily candles.

Paper only, public candles (no key, no paid API). Fills next-bar open, forces
a final close, charges fees + slippage. For every candidate strategy and asset
it reports trades, win rate, profit factor, net P&L, max drawdown, walk-forward,
out-of-sample, overfitting, a sensitivity check, and the RiskManager decision.
Prints NO TRADE if nothing is robust. No invented data.

    python run_research.py
"""

import time
from decimal import Decimal as D

from coinbase.rest import RESTClient

from trading_team import (
    DebateRoom,
    MarketAnalyst,
    RiskManager,
    Signal,
    backtest,
    paper_risk_config,
)
from trading_team.strategies import ALL_STRATEGIES

FEE, SLIP = 0.001, 0.0005
DAY = 86400


def daily_bars(client: RESTClient, product_id: str, days: int = 1100) -> list:
    """Paginate ONE_DAY candles back `days` (Coinbase caps 350/request)."""
    end = int(time.time())
    out: dict = {}
    while days > 0 and end > 1_400_000_000:
        chunk = min(300, days)
        start = end - DAY * chunk
        try:
            resp = client.get_public_candles(
                product_id=product_id,
                start=str(start),
                end=str(end),
                granularity="ONE_DAY",
                limit=350,
            ).to_dict()
        except Exception:
            break
        cs = resp.get("candles", [])
        if not cs:
            break
        for c in cs:
            t = int(c["start"])
            out[t] = {
                "o": float(c["open"]),
                "h": float(c["high"]),
                "l": float(c["low"]),
                "c": float(c["close"]),
                "v": float(c["volume"]),
            }
        end = start
        days -= chunk
    return [out[t] for t in sorted(out)]


def phase_label(bars: list) -> str:
    c = [b["c"] for b in bars]
    drift = (c[-1] / c[0] - 1) * 100
    rets = [(c[i] - c[i - 1]) / c[i - 1] for i in range(1, len(c)) if c[i - 1]]
    mean = sum(rets) / len(rets)
    vol = (sum((x - mean) ** 2 for x in rets) / len(rets)) ** 0.5 * 100
    d = "steigend" if drift > 20 else "fallend" if drift < -20 else "seitwaerts"
    return f"{d}, Tagesvol {vol:.1f}%"


def sensitivity(bars: list, strat) -> bool:
    """Sign of the full-sample return should survive doubled fees and a small
    data shift. True = stable."""
    base = backtest.simulate_bars(
        bars, strat, warmup=60, fee_rate=FEE, slippage_rate=SLIP
    ).return_pct
    hi_fee = backtest.simulate_bars(
        bars, strat, warmup=60, fee_rate=FEE * 2, slippage_rate=SLIP * 2
    ).return_pct
    shifted = backtest.simulate_bars(
        bars[2:], strat, warmup=60, fee_rate=FEE, slippage_rate=SLIP
    ).return_pct
    signs = [1 if x > 0 else -1 if x < 0 else 0 for x in (base, hi_fee, shifted)]
    return len(set(signs)) == 1


def robust(bt, wf, of, stable) -> bool:
    return (
        bt.trades >= 8
        and bt.profit_factor > 1.2
        and not of.likely_overfit
        and of.out_of_sample_return > 0
        and wf.mean_return > 0
        and wf.worst_return > -20
        and stable
    )


def risk_decision(ok: bool, risk: RiskManager) -> str:
    if not ok:
        return "NO TRADE"
    sig = Signal(
        "BTC-USDC",
        "BUY",
        "robust",
        entry=D("100"),
        stop_loss=D("98"),
        size_fraction=D("1.0"),
    )
    d = risk.evaluate(sig)
    return "paper-freigabe" if d.approved else "veto"


def main() -> int:
    client = RESTClient()
    products = ["BTC-USD", "ETH-USD", "SOL-USD"]
    cfg = paper_risk_config()
    print(
        f"Kapitalgrenze {cfg.allocated_capital_usdc} USDC | live_allowed={cfg.live_allowed()}\n"
    )
    header = (
        f"{'asset/strategy':30} {'trades':>6} {'win%':>5} {'PF':>6} {'net%':>7} "
        f"{'maxDD%':>6} {'OOS%':>6} {'ovft':>5} {'WFmean':>7} {'sens':>5} {'risk':>14}"
    )
    passed = []
    for product in products:
        bars = daily_bars(client, product)
        if len(bars) < 200:
            print(f"{product}: zu wenig Historie ({len(bars)} Tage) — uebersprungen")
            continue
        print(f"=== {product} | {len(bars)} Tageskerzen | {phase_label(bars)} ===")
        print(header)
        for name, strat in ALL_STRATEGIES.items():
            bt = backtest.simulate_bars(
                bars, strat, warmup=60, fee_rate=FEE, slippage_rate=SLIP
            )
            of = backtest.overfitting_check(bars, strat, warmup=60, bars_mode=True)
            try:
                wf = backtest.walk_forward(
                    bars, strat, folds=5, warmup=60, bars_mode=True
                )
                wfm = wf.mean_return
            except ValueError:
                wf = None
                wfm = 0.0
            stable = sensitivity(bars, strat)
            ok = robust(bt, wf, of, stable) if wf else False
            rd = risk_decision(ok, RiskManager(cfg))
            print(
                f"{product + '/' + name:30} {bt.trades:6d} {bt.win_rate_pct:5.0f} "
                f"{bt.profit_factor:6.2f} {bt.return_pct:7.1f} {bt.max_drawdown_pct:6.1f} "
                f"{of.out_of_sample_return:6.1f} {str(of.likely_overfit):>5} {wfm:7.2f} "
                f"{str(stable):>5} {rd:>14}"
            )
            if ok:
                passed.append((product, name))
        print()

    print("--- Team-Debatte (gleiche Daten, Gegenargumente) ---")
    analyst, room = MarketAnalyst(), DebateRoom()
    for product in products:
        bars = daily_bars(client, product, 120)
        if len(bars) < 40:
            continue
        closes = [D(str(b["c"])) for b in bars]
        rec = room.deliberate(analyst.analyse(product, closes), closes)
        print(
            f"  {product}: Konsens {rec.stance} (agreed={rec.agreed}) | "
            f"Gegenargumente: {'; '.join(rec.challenges) or 'keine'}"
        )

    print("\n=== VERDICT ===")
    if passed:
        for p, s in passed:
            print(f"ROBUST (-> unabhaengiges Forward-Paper-Trading): {s} @ {p}")
    else:
        print(
            "NO TRADE — keine Strategie besteht Walk-Forward + OOS + Overfitting + Sensitivitaet."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
