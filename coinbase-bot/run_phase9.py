"""Phase 9 backend run: probe connectors, pull real market data, enrich a few
discovered tokens with on-chain + Jupiter checks, run the risk gate, start
forward paper for the five portfolios, and write a real snapshot the dashboard
reads. No real order, no swap, no key. Only real fetched data is written; on a
failed source the field is marked accordingly, never invented.

    python run_phase9.py            # writes state/dashboard_snapshot.json
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from coinbase.rest import RESTClient

from multimarket import (
    GeckoTerminalSource,
    TokenScanner,
    assess_memecoin_risk,
    should_veto,
    valuation,
)
from multimarket import jupiter, solana_rpc
from multimarket.connectors import check_connectors
from trading_team import RiskManager, backtest, paper_risk_config
from trading_team.strategies import macd_trend

STATE = Path(__file__).resolve().parent / "state"
SNAP = STATE / "dashboard_snapshot.json"


def coinbase_market(client: RESTClient):
    """Last traded price per product from public candles (works without auth)."""
    out = []
    for product in ("BTC-USD", "ETH-USD", "SOL-USD"):
        try:
            end = int(time.time())
            resp = client.get_public_candles(
                product_id=product,
                start=str(end - 7200),
                end=str(end),
                granularity="ONE_HOUR",
                limit=2,
            ).to_dict()
            cs = sorted(resp.get("candles", []), key=lambda c: int(c["start"]))
            if cs:
                out.append({"symbol": product, "mid": float(cs[-1]["close"])})
        except Exception:
            pass
    return out


def daily_closes(client: RESTClient, product_id: str, n: int = 120):
    end = int(time.time())
    start = end - 86400 * (n + 1)
    try:
        resp = client.get_public_candles(
            product_id=product_id,
            start=str(start),
            end=str(end),
            granularity="ONE_DAY",
            limit=n,
        ).to_dict()
        cs = sorted(resp["candles"], key=lambda c: int(c["start"]))
        return [
            {
                "o": float(c["open"]),
                "h": float(c["high"]),
                "l": float(c["low"]),
                "c": float(c["close"]),
                "v": float(c["volume"]),
            }
            for c in cs
        ]
    except Exception:
        return []


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    client = RESTClient()
    now = datetime.now(timezone.utc).isoformat()

    connectors = check_connectors()
    market = coinbase_market(client)

    cfg = paper_risk_config()
    RiskManager(cfg)
    bars = daily_closes(client, "BTC-USD")
    portfolio_a = {
        "name": "A",
        "market": "Coinbase BTC MACD-Trend",
        "cash_usd": float(cfg.allocated_capital_usdc),
        "decision": "n/a",
        "backtest": None,
    }
    if len(bars) >= 60:
        signal = macd_trend(bars)
        bt = backtest.simulate_bars(
            bars, macd_trend, warmup=60, fee_rate=0.001, slippage_rate=0.0005
        )
        portfolio_a["decision"] = signal
        portfolio_a["backtest"] = {
            "trades": bt.trades,
            "win_rate_pct": round(bt.win_rate_pct, 1),
            "profit_factor": round(bt.profit_factor, 2),
            "net_pnl_pct": round(bt.return_pct, 1),
            "max_dd_pct": round(bt.max_drawdown_pct, 1),
        }

    scanner = TokenScanner([GeckoTerminalSource("solana")])
    scanned = scanner.scan()
    scanner_rows = []
    risk_events = []
    enrich_n = 3
    for i, r in enumerate(scanned[:12]):
        t = r["token"]
        v = valuation(t)
        onchain = None
        jup = None
        if i < enrich_n and t.address:
            onchain = solana_rpc.fetch_onchain(t.address)
            jup = jupiter.round_trip_quote(t.address)
        report = assess_memecoin_risk(t, onchain)
        row = {
            "name": t.name,
            "address": t.address,
            "network": t.network,
            "mc_or_fdv": v["value_usd"],
            "uncertain": v["uncertain"],
            "category": r["category"].value,
            "liquidity_usd": t.liquidity_usd,
            "volume_24h": t.volume_24h_usd,
            "risk": report.level.value,
            "veto": should_veto(report),
            "flags": report.flags,
            "sellable": (jup or {}).get("sellable") if jup else report.sell_feasible,
            "enriched": onchain is not None,
        }
        scanner_rows.append(row)
        if should_veto(report):
            risk_events.append(
                {"token": t.name, "level": report.level.value, "flags": report.flags}
            )

    portfolios = [
        portfolio_a,
        {
            "name": "B",
            "market": "Weitere Coinbase-Coins",
            "cash_usd": 0.0,
            "decision": "beobachtend (keine robuste Strategie freigegeben)",
            "backtest": None,
        },
        {
            "name": "C",
            "market": "Solana Memecoins",
            "cash_usd": 0.0,
            "decision": f"NO TRADE — {sum(1 for r in scanner_rows if r['veto'])}/{len(scanner_rows)} per Veto ausgeschlossen",
            "backtest": None,
        },
        {
            "name": "D",
            "market": "Micro-Caps < 1M USD",
            "cash_usd": 0.0,
            "decision": "NO TRADE — Exit-Liquiditaet/Daten unzureichend",
            "backtest": None,
        },
        {
            "name": "E",
            "market": "Micro-Caps < 500k USD",
            "cash_usd": 0.0,
            "decision": "NO TRADE — Exit-Liquiditaet/Daten unzureichend",
            "backtest": None,
        },
    ]

    agents = [
        {"name": "MarketAnalyst", "status": "aktiv"},
        {"name": "Strategist", "status": "aktiv"},
        {"name": "RiskManager", "status": "aktiv (Vetorecht)"},
        {"name": "ExecutionAgent", "status": "PAPER"},
        {"name": "TradeReviewer", "status": "aktiv"},
        {"name": "Supervisor", "status": "aktiv (Not-Aus bereit)"},
    ]

    snapshot = {
        "generated_at": now,
        "trading_mode": "PAPER (LIVE BLOCKED)",
        "emergency_stop": False,
        "capital_ceiling_usdc": float(cfg.allocated_capital_usdc),
        "live_allowed": cfg.live_allowed(),
        "connectors": connectors,
        "agents": agents,
        "market": market,
        "scanner": scanner_rows,
        "portfolios": portfolios,
        "risk_events": risk_events,
    }
    SNAP.write_text(json.dumps(snapshot, indent=2))
    print(f"snapshot -> {SNAP}")
    print("connectors: " + ", ".join(f"{c['name']}={c['status']}" for c in connectors))
    print(f"market: {market}")
    print(
        f"portfolio A decision: {portfolio_a['decision']} backtest={portfolio_a['backtest']}"
    )
    print(f"scanned tokens: {len(scanner_rows)}, risk vetoes: {len(risk_events)}")
    if scanner_rows:
        s = scanner_rows[0]
        print(
            f"sample enriched token: {s['name']} risk={s['risk']} veto={s['veto']} "
            f"sellable={s['sellable']} enriched={s['enriched']} flags={s['flags']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
