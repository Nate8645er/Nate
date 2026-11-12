# Hyperliquid Spot Connector

Connector for real spot trading on Hyperliquid mainnet through the official
`hyperliquid-python-sdk`. There is no paper mode.

**Status: no real order has been sent.** Read-only calls and local order
signing were run against mainnet. Buying and selling are not verified.

## Configuration

| Variable                  | Meaning                                                     |
| ------------------------- | ----------------------------------------------------------- |
| `HL_MAIN_WALLET_ADDRESS`  | Public address of the main wallet                           |
| `HL_API_WALLET_KEY`       | Private key of an API wallet approved by the main wallet    |
| `HL_LIVE_TRADING_ENABLED` | Must be `1` before any real order is sent. Unset by default |

Locally, copy `.env.local.example` to `.env.local` and fill it in. `.env.local`
is ignored by git. In a cloud environment, set the variables in the
environment's settings instead of a project file.

Use an API wallet, never the key of the main wallet. Never commit a key and
never paste one into a chat.

## Read-only check

```
pip install -r requirements.txt
python verify_readonly.py UBTC/USDC 12
```

Prints account state, balances, API wallet authorization, live price, fee
rate, a prepared buy and sell order, and whether they can be signed locally.
It sends no order.

## Safety rules in the connector

- Spot pairs only. Perpetual assets are refused, and the connector has no
  transfer or withdrawal call.
- A real order needs `HL_LIVE_TRADING_ENABLED=1` and a confirmation string
  equal to `EXECUTE <SIDE> <PAIR> <SIZE> LIMIT <PRICE>` of the prepared order.
- Per-order capital limit (`max_usdc_per_order`, default 15 USDC).
- Each order has a client order id that is journaled in `state/orders.jsonl`
  before it is sent. An id that was already submitted is refused.
- `emergency_stop()` writes `state/KILL_SWITCH`. While that file exists, no
  order is sent.
- Orders are immediate-or-cancel limit orders with a 1 % price bound, which is
  how the SDK itself implements market orders.

A returned status means Hyperliquid accepted the order. Read the result back
with `get_order_status` and `get_order_fills`.

## Tests

```
python -m pytest tests
```
