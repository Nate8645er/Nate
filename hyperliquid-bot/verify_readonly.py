"""Read-only check of the real Hyperliquid mainnet account. Sends no order.

Reads HL_MAIN_WALLET_ADDRESS and the API wallet key from the environment or
from .env.local next to this file. The key is never printed.

    python verify_readonly.py [PAIR] [USDC_AMOUNT]
"""

import sys
from decimal import Decimal
from pathlib import Path

from hl_connector import ConnectorError, HyperliquidSpotConnector, load_env_file


def main() -> int:
    pair = sys.argv[1] if len(sys.argv) > 1 else "UBTC/USDC"
    usdc_amount = sys.argv[2] if len(sys.argv) > 2 else "12"
    load_env_file(Path(__file__).resolve().parent / ".env.local")

    connector = HyperliquidSpotConnector()
    print(f"main wallet: {connector.main_address}")
    print(f"account exists on Hyperliquid: {connector.account_exists()}")

    balances = connector.get_real_balance()
    print(f"spot balances: {balances if balances else 'none'}")
    print(f"available USDC: {connector.get_available('USDC')}")

    print(f"API wallet address: {connector.api_wallet_address() or 'no key set'}")
    print(f"API wallet authorized: {connector.api_wallet_authorized()}")

    print(f"spot pairs: {len(connector.get_spot_markets())}")
    price = connector.get_market_price(pair)
    print(f"{pair}: bid {price['bid']} ask {price['ask']}")
    print(f"taker fee rate: {connector.get_taker_fee_rate()}")

    buy = connector.prepare_buy_order(pair, usdc_amount, check_funds=False)
    print(
        f"prepared buy: {buy['confirmation']} | value {Decimal(buy['est_notional']):.2f} "
        f"USDC, fee about {Decimal(buy['est_fee']):.4f} USDC"
    )
    sell = connector.prepare_sell_order(pair, buy["size"], check_funds=False)
    print(f"prepared sell: {sell['confirmation']}")

    for label, order in (("buy", buy), ("sell", sell)):
        try:
            signed = connector.sign_order(order)
            print(f"{label} signed locally by {signed['signer']} (not sent)")
        except ConnectorError as error:
            print(f"{label} signing FAILED: {error}")

    try:
        connector.prepare_buy_order(pair, usdc_amount)
        print("funds check for buy: OK")
    except ConnectorError as error:
        print(f"funds check for buy: BLOCKED: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
