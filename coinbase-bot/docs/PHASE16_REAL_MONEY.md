# Phase 16 — Real-Money AI Trading System

**Verdict: NOT READY — 11 of 14 readiness criteria pass.** No real order was
sent. Autonomous live is locked (`LIVE_AUTONOMOUS_ENABLED = False`). Main
untouched; all in PR #50. This is a real Coinbase-spot trading system built on
the existing architecture — not a paper competition presented as finished — but
it is not yet cleared for real money, and it is honest about why.

## 1. Coinbase connection

The official Advanced Trade connector is used (no second engine). It requires
**View + Trade** and refuses any **transfer**-capable key at construction.
`verify_access()` does the read-only section-3 check (permissions, portfolio,
balance, products, open orders, history, fees) and passes only when the key can
view and trade, cannot transfer, and is the expected portfolio. In this
environment there is **no API key for the bot's own connector**, so the live
connection criteria (2, 3, 14) are FAIL until the key is on the laptop. The
session's read-only connector shows: 1 portfolio, 17.1069 USDC available,
0 open orders, taker fee 0.10 %.

## 2. Portfolio isolation

The key's portfolio is checked against the expected id, and the transfer
permission must be off. Independently, the capital ceiling of **17.10 USDC is
fixed in code**: it is not derived from the balance, so a deposit never raises
it, and no other portfolio is reachable. Confirmed by a readiness self-test.

## 3. Agent team (15 workstations)

The 15 visible workstations map to real backend functions; 12 are backed by
code, 3 carry honest unavailability markers for data free sources cannot
deliver (holder concentration, paid-indexer wallet history, a real sentiment
score). No independent "AI agent processes" are simulated. The six core agents
(MarketAnalyst, Strategist, RiskManager, ExecutionAgent, TradeReviewer,
Supervisor) plus four debate voices drive every decision.

## 4. Meeting flow

Every entry runs the full meeting; the meeting never sends an order itself.
Steps 1–6 are the existing `hold_meeting` (analysis → strategy → debate →
RiskManager veto → Supervisor → ExecutionAgent sizing). Then: order preview,
the final safety check (the order is rebuilt from the meeting record and
re-verified against what the RiskManager approved), execution only if the gate
is open, Coinbase fill reconciliation, review, portfolio update. A RiskManager
veto is binding. Every cycle is appended to `state/live_meetings.jsonl`.

## 5. Trading strategies — the championship

Seven strategies (MACD trend, momentum-with-volume-filter, breakout-volume,
mean-reversion, EMA+ATR stop, RSI trend, multi-signal) run on the **same** real
candles and compete. The winner is the side with the most votes above a quorum,
beating the opposite side, else HOLD. The championship only **selects** a
candidate; the meeting and RiskManager remain authoritative. Entries are
long-only (spot, no shorting). Crucially there is **one shared execution step
per tick**, so competing strategies can never each spend the budget — no double
orders. On today's real market all three coins voted SELL → NO TRADE.

## 6. Risk gates

Before any order: confirmed limits, product allow-list (BTC/ETH/SOL-USDC),
daily and total loss ceilings (persistent, fee-inclusive), slippage ≤ 2 %,
price impact, position size ≤ allocation, available balance, exchange minimum,
open orders, market-data freshness (≤ 90 s), known fee rate. Any unknown value
blocks the order ("Bei unklaren Zuständen: BLOCK NEW ORDERS"). The RiskManager
may tighten these at any time and can never raise them.

## 7. Order execution

Market buy and sell through the connector, with order preview, unique client
order ids written to disk **before** sending (idempotent), status read-back,
fill reconciliation and partial-fill handling (only the filled amount is
booked). Limit sell and cancel are available for controlled exits. On a timeout
or unknown status the system **never re-buys**: it trips the persistent
emergency stop and reconciles by client order id first.

## 8. Stop-loss system

`monitor_positions` continuously checks each open position and exits on
stop-loss, take-profit or a time cap. Exits run even under the emergency stop
(risk reduction). **Honest limitation:** Coinbase supports stop-limit and
trigger-bracket orders, but no order type guarantees a fill price or a maximum
loss — a fast move can fill worse, and a stop-limit may not fill at all. A
position with an unknown or stale price is never acted on (no invented price);
it is flagged and kept under watch. Stops only work while the laptop runs and
is online.

## 9. Dashboard

The pixel office and 15 workstations are unchanged. The Risk Center shows the
confirmed limits, current daily/total loss and the persistent stop; a Live
Readiness panel runs the 14-criteria check on demand; Live Profit shows real
balance, allocated capital, positions, realised / unrealised / daily / total
P&L and fees from Coinbase, with a LIVE/PAPER badge and `UNBEKANNT` for missing
values. All P&L is zero because the system has sent no order. Paper forward-test
results are kept in a separate paper book and never shown as real money.

## 10. Test results

**139 Python tests pass** (125 + 14 new this phase). Verified: championship
ranking and long-only entries; paper runner simulates a fill with the real fee
and sends nothing real; one shared execution (no double orders); emergency stop
blocks buys but allows the risk-reducing exit; stop-loss / take-profit / time
exits; stale or missing price never triggers an exit; read-only `verify_access`
passes and rejects a wrong portfolio or a transfer-capable key. Plus the Phase
14 scenarios (timeout no re-buy, duplicate refused, restart safety, partial
fill, manipulated decision refused, veto binding). Forward paper ran live on
real Coinbase candles: NO TRADE on all three coins (SELL majority).

## 11. Readiness status

NOT READY, 11/14. PASS: risk config, emergency stop, persistent loss,
de-duplication, restart safety, API error handling, meeting required, veto,
authentication, audit logging, market data. FAIL: Coinbase connection,
portfolio isolation, order reconciliation — all three only because the bot's
connector has no API key in this environment.

## 12. Remaining risks

- **No key here** → three criteria cannot pass until the laptop run. Create a
  View+Trade key, put it and the portfolio id in `coinbase-bot\.env`, run
  `windows\readiness.ps1`.
- **No validated edge.** No strategy passed out-of-sample validation and the
  live tape is not signalling entries; the system may trade rarely, and there is
  no evidence it beats fees. The 2.0 % slippage and the loss limits equal to the
  full capital mean the configuration permits losing all 17.10 USDC.
- **No production scheduler.** The runner and monitor are built and tested but
  nothing runs them on a timer in production yet; that, and switching the mode,
  are deliberately left for your decision.
- Stops are not guaranteed fills and only work while the laptop is on.

## Activation

Nate's risk values are confirmed, but this phase is not a release. When the
laptop run shows 14/14 and the risks above are addressed, a separate final
**LIVE-ACTIVATION** confirmation will be requested, naming the checked
configuration and using the exact phrase
`AUTONOMES LIVE TRADING AKTIVIEREN 17.10 USDC`. Until then: no real order, no
autonomous switch.
