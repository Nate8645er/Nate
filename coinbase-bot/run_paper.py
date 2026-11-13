"""Run the HyperGrok trading team in PAPER mode against real Coinbase candles.

No API key and no real order: public market data only, simulated fills.

    python run_paper.py BTC-USDC ETH-USDC SOL-USDC
"""

import sys
import time
from decimal import Decimal as D
from pathlib import Path

from coinbase.rest import RESTClient

from trading_team import (
    ExecutionAgent,
    MarketAnalyst,
    PaperBroker,
    RiskConfig,
    RiskManager,
    Strategist,
    Supervisor,
    TradeReviewer,
)

GRANULARITY_SECONDS = 3600


def real_closes(client: RESTClient, product_id: str, n: int = 60) -> list[D]:
    end = int(time.time())
    start = end - GRANULARITY_SECONDS * (n + 1)
    resp = client.get_public_candles(
        product_id=product_id,
        start=str(start),
        end=str(end),
        granularity="ONE_HOUR",
        limit=n,
    )
    data = resp.to_dict() if hasattr(resp, "to_dict") else resp
    candles = sorted(data["candles"], key=lambda c: int(c["start"]))
    return [D(c["close"]) for c in candles]


def main() -> int:
    symbols = sys.argv[1:] or ["BTC-USDC", "ETH-USDC", "SOL-USDC"]
    client = RESTClient()

    # Paper config: 100 USDC of pretend capital, up to 100% per position.
    # These paper limits are NOT the user's real confirmed limits.
    config = RiskConfig(
        allocated_capital_usdc=D("100"),
        max_position_fraction=D("1.0"),
        daily_loss_limit_usdc=D("10"),
        per_trade_risk_usdc=D("5"),
        taker_fee_rate=D("0.001"),
        min_order_usdc=D("1"),
        limits_confirmed=False,  # live stays OFF
    )
    broker = PaperBroker(
        cash_usdc=config.allocated_capital_usdc,
        taker_fee_rate=config.taker_fee_rate,
        journal=Path(__file__).resolve().parent / "state" / "paper_trades.jsonl",
    )
    risk = RiskManager(config)
    reviewer = TradeReviewer()
    sup = Supervisor(
        config,
        MarketAnalyst(),
        Strategist(),
        risk,
        ExecutionAgent(config, broker),
        reviewer,
    )

    prices: dict[str, D] = {}
    for symbol in symbols:
        closes = real_closes(client, symbol)
        prices[symbol] = closes[-1]
        result = sup.run_cycle(symbol, closes, mode="paper")
        print(
            f"{symbol}: trend={result.get('trend')} price={result.get('price')} "
            f"-> {result['action']} ({result.get('reason') or result.get('risk')})"
        )

    print(f"\nlive_allowed: {config.live_allowed()}  (muss False sein)")
    print(f"paper cash: {broker.cash_usdc:.4f} USDC")
    print(
        f"paper positions: { {k: str(v) for k, v in broker.positions.items() if v > 0} }"
    )
    print(f"paper equity (mark-to-market): {broker.equity(prices):.4f} USDC")
    return 0


if __name__ == "__main__":
    sys.exit(main())
