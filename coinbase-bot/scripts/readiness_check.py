"""Run the LIVE_READINESS_CHECK from the command line.

    python scripts/readiness_check.py

Reads COINBASE_API_KEY / COINBASE_API_SECRET and HYPERGROK_PORTFOLIO_ID from
the environment (never from a file in the repository). Sends no order and arms
nothing. Exit code 0 = READY, 1 = NOT READY.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.auth import AUDIT_FILE, AuthStore  # noqa: E402
from trading_team.modes import ModeController  # noqa: E402
from trading_team.persistence import SafetyStore  # noqa: E402
from trading_team.readiness import KNOWN_ORDERS, READY, run_readiness_check  # noqa: E402
from trading_team.risk_config import NATE_CONFIRMED_LIMITS  # noqa: E402


def main() -> int:
    connector, note = None, "COINBASE_API_KEY nicht gesetzt"
    if os.environ.get("COINBASE_API_KEY"):
        try:
            from coinbase_connector.connector import CoinbaseLiveConnector
            connector, note = CoinbaseLiveConnector(max_quote_per_order="17.10"), "verbunden"
        except Exception as exc:  # noqa: BLE001
            note = f"{type(exc).__name__}: {exc}"
    market_ts = None
    try:
        from server.app import _fetch_prices
        if _fetch_prices():
            market_ts = time.time()
    except Exception:  # noqa: BLE001
        market_ts = None
    controller = ModeController(NATE_CONFIRMED_LIMITS, store=SafetyStore(ROOT / "state"))
    report = run_readiness_check(
        controller=controller, connector=connector, auth_store=AuthStore.load(),
        audit_file=AUDIT_FILE, market_updated_at=market_ts,
        expected_portfolio_id=os.environ.get("HYPERGROK_PORTFOLIO_ID") or None,
        known_orders=KNOWN_ORDERS)
    print(f"Connector: {note}")
    for c in report["criteria"]:
        print(f"{c['number']:>2}. {'PASS' if c['passed'] else 'FAIL'}  {c['title']}")
        for line in c["evidence"]:
            print(f"      {line}")
    print()
    print(f"{report['verdict']}  ({report['passed']}/{report['total']})")
    print(f"LIVE_AUTONOMOUS_ENABLED = {report['live_autonomous_enabled']}")
    if "--json" in sys.argv:
        print(json.dumps(report, indent=2, default=str))
    return 0 if report["verdict"] == READY else 1


if __name__ == "__main__":
    raise SystemExit(main())
