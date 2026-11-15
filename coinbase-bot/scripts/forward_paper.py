"""Forward paper trading on REAL Coinbase market data (Phase 15 section 10).

Pulls real public candles (no API key needed), runs the full championship +
meeting + risk gates for each product, simulates fills in the paper book, and
monitors open paper positions for stop-loss / take-profit / time exits.

Sends NO real order. Books nothing real: paper positions and the paper ledger
live in a SEPARATE state directory so they can never be confused with live
money. Run it for a fixed number of ticks, or as a loop:

    python scripts/forward_paper.py --ticks 1          # one pass, print result
    python scripts/forward_paper.py --loop --interval 300

The real loss ledger, the real positions and the emergency stop are never
touched here.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from decimal import Decimal as D
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from trading_team.core import RiskManager  # noqa: E402
from trading_team.engine import (
    ExitRule,
    monitor_positions,
    read_paper_ledger,  # noqa: E402
    read_paper_positions,
    run_once,
)
from trading_team.modes import ModeController, TradingMode  # noqa: E402
from trading_team.persistence import SafetyStore  # noqa: E402
from trading_team.risk_config import (
    NATE_CONFIRMED_LIMITS,
    live_risk_config,
)  # noqa: E402

SYMBOLS = ("BTC-USDC", "ETH-USDC", "SOL-USDC")
PAPER_STATE = ROOT / "state" / "paper"  # separate from the live state/
STORE = SafetyStore(PAPER_STATE)


def fetch_ohlcv(symbol: str, n: int = 120) -> list:
    """Real completed daily candles from Coinbase's public endpoint (no key)."""
    from coinbase.rest import RESTClient

    client = RESTClient()
    end = int(time.time())
    resp = client.get_public_candles(
        product_id=symbol,
        start=str(end - 86400 * (n + 1)),
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


def spot_prices() -> dict:
    from coinbase.rest import RESTClient

    client = RESTClient()
    now = int(time.time())
    out = {}
    for p in SYMBOLS:
        try:
            resp = client.get_public_candles(
                product_id=p,
                start=str(now - 7200),
                end=str(now),
                granularity="ONE_HOUR",
                limit=2,
            ).to_dict()
            cs = sorted(resp.get("candles", []), key=lambda c: int(c["start"]))
            if cs:
                out[p] = {"price": float(cs[-1]["close"])}
        except Exception:  # noqa: BLE001
            continue
    return out


class PublicConnector:
    """Read-only market data + balance stub for the PAPER runner. It never
    sends an order and needs no API key; the balance is the allocated capital
    minus what paper positions already tie up."""

    def __init__(self, allocated="17.10"):
        self.allocated = D(allocated)

    def get_available_funds(self, currency: str) -> D:
        exposure = sum(
            (D(str(p["cost_usdc"])) for p in read_paper_positions(STORE).values()),
            D("0"),
        )
        return max(D("0"), self.allocated - exposure)

    def get_market_price(self, product_id: str) -> dict:
        price = spot_prices().get(product_id, {}).get("price")
        if price is None:
            raise RuntimeError("keine Kursdaten")
        p = D(str(price))  # public candles give no book; tight synthetic spread
        return {"bid": p * D("0.9995"), "ask": p * D("1.0005")}

    def get_open_orders(self) -> list:
        return []


def tick() -> dict:
    controller = ModeController(NATE_CONFIRMED_LIMITS, store=STORE)
    controller.mode = TradingMode.PAPER
    conn = PublicConnector()
    results = []
    for symbol in SYMBOLS:
        try:
            ohlcv = fetch_ohlcv(symbol)
        except Exception as exc:  # noqa: BLE001
            results.append({"symbol": symbol, "result": f"DATA STALE: {exc}"})
            continue
        out = run_once(
            symbol,
            ohlcv,
            controller=controller,
            risk=RiskManager(live_risk_config()),
            connector=conn,
            store=STORE,
            market_updated_at=time.time(),
            fee_rate=D("0.001"),
            min_order_usdc=D("1"),
            mode=TradingMode.PAPER,
        )
        results.append(
            {
                "symbol": symbol,
                "result": out["result"],
                "championship": out.get("championship", {}).get("note"),
            }
        )
    mon = monitor_positions(
        spot_prices(),
        controller=controller,
        connector=conn,
        store=STORE,
        paper=True,
        rule=ExitRule(max_hold_seconds=7 * 86400),
    )
    ledger = read_paper_ledger(STORE)
    return {
        "entries": results,
        "monitor": mon,
        "open_paper_positions": list(read_paper_positions(STORE)),
        "paper_realised_usdc": str(ledger["total_realised"]),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticks", type=int, default=1)
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--interval", type=int, default=300)
    args = ap.parse_args()
    PAPER_STATE.mkdir(parents=True, exist_ok=True)
    n = 0
    while True:
        n += 1
        print(
            json.dumps(
                {
                    "tick": n,
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    **tick(),
                },
                indent=2,
                default=str,
            )
        )
        if not args.loop and n >= args.ticks:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
