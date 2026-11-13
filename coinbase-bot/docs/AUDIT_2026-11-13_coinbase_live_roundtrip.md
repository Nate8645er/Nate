# Coinbase Live Execution Audit — 2026-11-13

Verified round-trip of one real BTC buy and one real BTC sell on the user's
Coinbase account (portfolio "Default"), read back from Coinbase order data.
No API keys or personal data are included.

## 1. Orders (re-read from Coinbase)

|                  | Buy                                    | Sell                                   |
| ---------------- | -------------------------------------- | -------------------------------------- |
| Order ID         | `66b81bf7-fe78-4f48-9d0e-32b015e2ab8c` | `fcda9f60-6378-4c73-a118-467acee76271` |
| Client order ID  | `nate-test-buy-btcusdc-20261113-01`    | `nate-test-sell-btcusdc-20261113-01`   |
| Product          | BTC-USDC (spot)                        | BTC-USDC (spot)                        |
| Type             | market IOC                             | market IOC                             |
| Status           | FILLED (100%)                          | FILLED (100%)                          |
| Fills            | 1                                      | 3                                      |
| Filled size      | 0.00016017 BTC                         | 0.00016017 BTC                         |
| Avg price        | 68 549.80 USDC                         | 68 541.14 USDC                         |
| Fee (taker)      | 0.010979621466 USDC                    | 0.010978234131 USDC                    |
| Value after fees | 10.990601087466 USDC                   | 10.967255897069 USDC                   |

## 2. All fills

Buy — 1 fill (`size_in_quote=true`, so size is the quote amount):

- trade `c9d78c77…`: 10.979621466 USDC @ 68 549.80, fee 0.010979621466, TAKER

Sell — 3 fills (`size_in_quote=false`, base BTC):

- trade `672f66ae…`: 0.00014042 BTC @ 68 541.11, fee 0.0096245426662, TAKER
- trade `70090038…`: 0.00001910 BTC @ 68 541.34, fee 0.001309139594, TAKER
- trade `b8671cca…`: 0.00000065 BTC @ 68 541.34, fee 0.000044551871, TAKER
- Sum of fills: 0.00016017 BTC, total fee 0.0109782341312 USDC ✓

## 3. Cost, proceeds, fees (from fill data)

- Buy cost (debited): 10.990601 USDC (BTC 10.979621 + fee 0.010980)
- Sell proceeds (credited): 10.967256 USDC (gross 10.978234 − fee 0.010978)
- Total fees: 0.010980 + 0.010978 = **0.021958 USDC**
- Price drift over the ~21 s between fills: 0.00016017 × (68 549.80 − 68 541.14) ≈ **0.001387 USDC**
- Round-trip cost: 0.021958 + 0.001387 ≈ **0.023345 USDC**

## 4. Order statement vs. balance change

| Event      | USDC balance | Δ             |
| ---------- | ------------ | ------------- |
| Before buy | 17.130197    | —             |
| After buy  | 6.139596     | −10.990601    |
| After sell | 17.106852    | +10.967256    |
| Net        | —            | **−0.023345** |

The buy was requested with `quote_size = 11`, and the preview/`order_total`
showed 11. The account was debited only **10.990601 USDC**, not 11: a market
IOC buy rounds the acquired base amount down to the product increment, so part
of the 11 budget was not spent. This is fully explained — the balance delta
equals `total_value_after_fees` to the cent, and the net −0.023345 equals the
two fees plus price drift. **No unexplained discrepancy.**

## 5. Current balances (confirmed)

- USDC: 17.1068518096028
- BTC: 0 (position fully closed)

## 6. Open orders

`orders_list(status=OPEN)` → none. No resting or recurring orders.

## 7. Connector permissions (as observed)

- Read balances/portfolios: YES
- Read products, prices, candles: YES
- Preview orders: YES
- Place spot orders (buy/sell): YES (demonstrated)
- Single portfolio visible: "Default" (`26329da5-…`)

## 8. Transfers and withdrawals

- The connector exposes **no external withdrawal / send tool**. External
  payouts are therefore not possible through it.
- A portfolio-to-portfolio `transfer` tool exists but was **not used**; with
  only one portfolio it has no external effect. No transfer was executed.

## 9. User authorization of the real orders

- The buy was proposed explicitly (BTC-USDC, 11 USDC, fee shown) and the user
  approved it, also pre-approving the matching sell, before either was sent.
- Both orders stayed within the agreed one-buy / one-sell verification scope.
- No further real orders have been placed since.

## 10. Result

LIVE TRADING VERIFIED — one real buy and one real sell executed and proven
against Coinbase order and fill data, balances reconciled to the cent.
