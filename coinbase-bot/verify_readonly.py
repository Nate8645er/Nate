"""Read-only check of the real Coinbase account. Places no order.

Needs the API key in the environment (see README.md), then:
    python verify_readonly.py [PRODUCT_ID] [QUOTE_SIZE]
"""

import sys
from decimal import Decimal

from coinbase_connector import CoinbaseLiveConnector, ConnectorError


def main() -> int:
    product_id = sys.argv[1] if len(sys.argv) > 1 else "BTC-EUR"
    quote_size = sys.argv[2] if len(sys.argv) > 2 else "2.00"
    base, quote = product_id.split("-")

    connector = CoinbaseLiveConnector()
    perms = connector.permissions
    print(
        f"permissions: view={perms.get('can_view')} trade={perms.get('can_trade')} "
        f"transfer={perms.get('can_transfer')}"
    )

    for account in connector.get_real_balance():
        available = Decimal(account["available_balance"]["value"])
        if available:
            print(f"balance: {account['currency']} {available}")
    print(f"available {quote}: {connector.get_available_funds(quote)}")

    price = connector.get_market_price(product_id)
    print(f"{product_id}: bid {price['bid']} ask {price['ask']}")

    product = connector.get_product(product_id)
    print(
        f"minimum order: {product.get('quote_min_size')} {quote}, "
        f"trading_disabled={product.get('trading_disabled')}"
    )

    try:
        buy = connector.preview_buy_order(product_id, quote_size)
        print(
            f"buy preview {quote_size} {quote}: total {buy.get('order_total')}, "
            f"fee {buy.get('commission_total')}, receives {buy.get('base_size')} {base}"
        )
    except ConnectorError as error:
        print(f"buy preview BLOCKED: {error}")

    held = connector.get_available_funds(base)
    if held:
        try:
            sell = connector.preview_sell_order(product_id, str(held))
            print(
                f"sell preview {held} {base}: fee {sell.get('commission_total')}, "
                f"receives {sell.get('quote_size')} {quote}"
            )
        except ConnectorError as error:
            print(f"sell preview BLOCKED: {error}")
    else:
        print(f"sell preview skipped: no {base} held")
    return 0


if __name__ == "__main__":
    sys.exit(main())
