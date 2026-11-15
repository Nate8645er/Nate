# Phase 17 — Connector vs. Coinbase Advanced Trade OpenAPI spec

Source: `advanced-trade-spec.yaml` (OpenAPI 3.1, 11 005 lines, 45 paths),
compared field by field with `coinbase_connector/connector.py`. No real order
was sent, no API key created or shown, no safety rule disabled.

## Result per check

| #   | Check               | Spec                                                                            | Before                                                               | Now                                                                                                                                     |
| --- | ------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Authentication      | JWT bearer signed with the key secret (`securitySchemes.ApiKey`)                | Done by the official SDK                                             | unchanged, correct                                                                                                                      |
| 2   | Balances            | `Account.available_balance{value,currency}`, `hold`, `retail_portfolio_id`      | read correctly, but summed accounts of **every** portfolio           | only the key's own portfolio is counted                                                                                                 |
| 3   | Portfolio isolation | `key_permissions.portfolio_uuid`, `Account.retail_portfolio_id`                 | key's `portfolio_uuid` only                                          | **new** `assert_portfolio_isolation()`: every account must belong to the key's portfolio; part of `verify_access()`                     |
| 4   | Buy / sell          | `NewOrderResponse{success, success_response.order_id, error_response}`          | matched                                                              | unchanged, correct                                                                                                                      |
| 5   | Order preview       | `OrderPreviewResponse{errs, slippage, commission_total, best_bid, best_ask, …}` | read only `errs`; slippage approximated from a separate bid/ask call | **new** `preview_metrics()`; `run_cycle` uses Coinbase's own `slippage` and `commission_total`, falls back to bid/ask only when missing |
| 6   | Order status        | `Order{status, filled_size, total_fees, total_value_after_fees, …}`             | matched                                                              | unchanged, correct                                                                                                                      |
| 7   | Fill reconciliation | `Fill{size, size_in_quote, price, commission}`, `cursor`                        | first page only, no cross-check                                      | paginated, portfolio-scoped; **new** `reconcile_fills()` compares order vs. sum of fills                                                |
| 8   | Fees                | `FeeTier{taker_fee_rate, maker_fee_rate}`, `Fill.commission`                    | matched                                                              | fees cross-checked per fill                                                                                                             |
| 9   | Error handling      | `{error, code, message, details}`                                               | exception text only                                                  | **new** `error_detail()` extracts the spec fields                                                                                       |
| 10  | API permissions     | `can_view, can_trade, can_transfer, portfolio_uuid, portfolio_type`             | matched; transfer key refused                                        | unchanged, correct                                                                                                                      |

Order queries (`list_orders`, `get_fills`) are now scoped with the spec's
`retail_portfolio_id` filter and follow `cursor`/`has_next` pagination. The
client-order-id lookup after a restart no longer stops at the first 100 orders.

## Real bug found with real data

Checked against the actual fills of the two orders from 2026-11-13 (read-only):
the BUY was quote-sized, and Coinbase reports its fill as
`size: 10.979621466, size_in_quote: true` — **USDC, not BTC**. A naive sum would
have reported a mismatch on a correct order. `reconcile_fills()` now converts
quote-sized fills with the fill price. Both real orders reconcile exactly:

| Order            | Fills           | Size                   | Fees                    |
| ---------------- | --------------- | ---------------------- | ----------------------- |
| BUY `66b81bf7…`  | 1 (quote-sized) | 0.00016017 BTC = order | 0.010979621466 = order  |
| SELL `fcda9f60…` | 3               | 0.00016017 BTC = order | 0.0109782341312 = order |

## Tests

**154 pass** (139 before, 15 new): spec field shapes for permissions,
balances, preview, fees and errors; foreign-portfolio accounts are detected and
never counted as spendable; preview slippage is preferred, a preview slippage of
3.5 % blocks the order, and a missing preview value falls back to bid/ask; order
and fill queries carry `retail_portfolio_id`; pagination finds an order on page
2; reconciliation passes on both real orders and flags a mismatch.

## Not changed by this phase

Readiness stays **NOT READY 11/14**: the bot's own connector still has no API
key in this environment. The new checks make criteria 3 and 14 stronger once
the key runs on the laptop (`windows\readiness.ps1`).
