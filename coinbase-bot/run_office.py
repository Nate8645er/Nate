"""Phase 10 office run: hold a REAL team meeting on live market data and write
the office snapshot the AI-office view renders.

The real tradable balance is passed in (read beforehand from the authorised
Coinbase connector) so sizing is checked against actual funds. No order is
sent: the meeting stops at the gate, and the mode stays PAPER.

    python run_office.py 17.1068518096028
"""

import json
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal as D
from pathlib import Path

from coinbase.rest import RESTClient

from multimarket.connectors import check_connectors
from trading_team import MarketAnalyst, RiskManager, paper_risk_config
from trading_team.meeting import hold_meeting
from trading_team.modes import AbsoluteLimits, ModeController

STATE = Path(__file__).resolve().parent / "state"
OUT = STATE / "office_snapshot.json"
SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD"]


def daily_closes(client, product_id, n=120):
    end = int(time.time())
    try:
        resp = client.get_public_candles(product_id=product_id, start=str(end - 86400 * (n + 1)),
                                         end=str(end), granularity="ONE_DAY", limit=n).to_dict()
        cs = sorted(resp["candles"], key=lambda c: int(c["start"]))
        return [D(c["close"]) for c in cs]
    except Exception:
        return []


def main() -> int:
    STATE.mkdir(parents=True, exist_ok=True)
    available = D(sys.argv[1]) if len(sys.argv) > 1 else D("0")
    client = RESTClient()

    # Limits are NOT confirmed -> mode stays PAPER, live stays locked.
    controller = ModeController(AbsoluteLimits(total_capital_usdc=D("17.10")))
    meetings = []
    for symbol in SYMBOLS:
        closes = daily_closes(client, symbol)
        if len(closes) < 40:
            continue
        result = hold_meeting(symbol, closes, risk=RiskManager(paper_risk_config()),
                              controller=controller, available_usdc=available,
                              analyst=MarketAnalyst())
        meetings.append(result.to_dict())

    snapshot = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "real_balance_usdc": str(available),
        "real_balance_source": "Coinbase (autorisierter Connector, gelesen vor dem Meeting)",
        "mode": controller.mode.value,
        "status": controller.status(),
        "limits": {
            "total_capital_usdc": str(controller.limits.total_capital_usdc),
            "max_daily_loss_usdc": str(controller.limits.max_daily_loss_usdc),
            "max_total_loss_usdc": str(controller.limits.max_total_loss_usdc),
            "max_slippage_pct": str(controller.limits.max_slippage_pct),
            "max_open_exposure_usdc": str(controller.limits.max_open_exposure_usdc),
            "confirmed": controller.limits.confirmed,
        },
        "connectors": check_connectors(),
        "meetings": meetings,
    }
    OUT.write_text(json.dumps(snapshot, indent=2))
    print(f"office snapshot -> {OUT}")
    print(f"mode={snapshot['mode']} real_balance={available} limits_confirmed={controller.limits.confirmed}")
    for m in meetings:
        gate = [s for s in m["statements"] if s["agent"] == "Gate"]
        print(f"  {m['symbol']}: consensus={m['consensus']} agreed={m['agreed']} "
              f"final={m['final']} steps={len(m['statements'])} "
              f"order={'ja' if m['prepared_order'] else 'nein'} gate={'ja' if gate else 'nicht erreicht'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
