# Coinbase Live Execution Connector

Minimal connector for real spot trading on Coinbase through the official
Advanced Trade SDK (`coinbase-advanced-py`). There is no paper mode.

**Status: not verified against a live account.** The safety guards are unit
tested. No call has been made with a real API key yet, and no real order has
been placed.

## API key

Create a key in the Coinbase Developer Platform with **View + Trade only**.
The connector refuses to start if the key can transfer funds. Restrict the key
to the portfolio the bot may trade and, if possible, to fixed IP addresses.

Provide the key through the environment, never in code or in the repository:

```
export COINBASE_API_KEY="organizations/.../apiKeys/..."
export COINBASE_API_SECRET="$(cat /path/to/private_key.pem)"
```

## Read-only check

```
pip install -r requirements.txt
python verify_readonly.py BTC-EUR 2.00
```

Prints permissions, balances, live price, minimum order size and order
previews. It places no order.

## Real orders

`execute_real_buy` and `execute_real_sell` send an order only if

1. `LIVE_TRADING_ENABLED=1` is set,
2. the `confirmation` argument equals `EXECUTE <SIDE> <PRODUCT> <SIZE>` for
   exactly this order, and
3. the order is within `max_quote_per_order` (default 10).

A returned `order_id` means Coinbase accepted the order, not that it filled.
Read the result back with `get_real_order_status` and `get_real_fills`.

## Tests

```
python -m pytest tests
```
