# Phase 15 — Coinbase Connector & Execution Safety

**Verdict: NOT READY — 11 of 14 readiness criteria pass.** No real order was
sent. Autonomous live stays locked. Main untouched; everything is in PR #50.

The three failing criteria are unchanged from Phase 14 and cannot be fixed from
this environment: they need the bot's own connector to run with a real API key,
and there is none here. Everything that does _not_ need a key was built and
tested.

## 1. Connector review and read-only verification

The official Coinbase Advanced Trade connector
(`coinbase_connector/connector.py`) was reviewed and extended:

- It already refuses any key that carries **transfer** permission, and requires
  View + Trade.
- New `verify_access(expected_portfolio_id)` — a single **read-only** check of
  everything section 3 asks for: permissions, portfolio id, available balance,
  tradable products, open orders, order history, fees. It sends nothing and
  returns `ok` only when the key can view and trade, **cannot** transfer, and
  belongs to the expected portfolio. Unit-tested with a read-only fake and with
  a transfer-capable fake (which is rejected at construction).
- New `supported_order_types()` documents what Coinbase really offers and, more
  importantly, that **no order type guarantees a fill price or a maximum loss**.
- New `get_open_orders()` and `find_order_by_client_id()` for reconciliation
  after a restart or timeout.

On your laptop, the read-only verification is one command (no order is sent):

```bash
python -c "from coinbase_connector.connector import CoinbaseLiveConnector as C; \
import json; print(json.dumps(C().verify_access('<PORTFOLIO_ID>'), indent=2, default=str))"
```

## 2. Emergency stop — repaired

Before, the emergency stop blocked **every** order, exits included, so a stop
could strand an open position. Now:

- New buys and any risk increase stay blocked.
- A **risk-reducing exit is allowed even while the stop is active** — the one
  action a stop must not prevent. The gate is `ModeController.may_reduce_risk`:
  there must be a real position, limits must be confirmed, and either a live
  mode or an active stop (controlled liquidation). Naked sells are impossible.
- Still persistent: a restart keeps the stop; an unreadable stop file counts as
  STOP; clearing needs an admin plus a written reason and is audited.

Unit-tested: under an active stop a buy is refused and the held position is
still flattened and booked.

## 3. Read-only Coinbase status (today)

| Item                | Value                                                                            |
| ------------------- | -------------------------------------------------------------------------------- |
| Portfolio           | one — "Default" `26329da5-…b846`                                                 |
| Available           | 17.1068518096028 USDC, nothing on hold                                           |
| Open orders         | 0                                                                                |
| Fees                | Intro tier: taker 0.10 %, maker 0.09 %                                           |
| Earlier test orders | BUY `66b81bf7…` and SELL `fcda9f60…`, both still FILLED, round trip −0.0233 USDC |

These reads go through the Coinbase connector of the Claude session. The bot's
own connector has still never run with a key (criteria 2/3/14).

## 4. The runner — PAPER and LIVE MANUAL

New `trading_team/engine.py` adds a runner that drives the **existing** meeting
and execution path on a schedule — it is not a second engine:

- It runs the strategy championship, and only a BUY winner reaches the full
  eight-step meeting with its binding RiskManager veto.
- There is **one** shared execution step per tick, so competing strategies can
  never each spend the budget.
- PAPER simulates a fill at the real ask with the real taker fee, into a
  **separate** paper book (`state/paper/…`). LIVE_MANUAL / LIVE_AUTONOMOUS go
  through the unchanged real `run_cycle`, which needs the per-order approval or
  the armed autonomous mode.
- Resolves unresolved orders first and blocks on any that are pending.

## 5. Continuous position monitoring and stop-loss

`monitor_positions` checks every open position once per call and acts on:

- **Stop-loss** (price ≤ stop), **take-profit** (price ≥ take) from the meeting,
- a **time exit** (a hard cap on holding duration).

A position whose price is unknown or stale is **not** acted on — no invented
price — it is reported as `watch_blocked` and kept under watch. Real exits fire
even under the emergency stop (risk reduction). Honest limit from section 8:
Coinbase supports stop-limit and trigger-bracket orders, but a stop is a trigger
to _send_ an order, not a guaranteed fill; a fast move can fill worse or, for a
stop-limit, not at all. This is documented, not hidden.

## 6. Tests (all green)

**139 Python tests pass** (125 before + 14 new). New coverage: the championship
ranks all seven strategies and is long-only for entries; the paper runner
simulates a fill with the real fee and sends no real order; a held position
blocks a second order; the stop blocks entries but allows the exit; stop-loss,
take-profit and time exits fire; stale/missing price never triggers an exit; the
read-only `verify_access` passes and rejects a wrong portfolio or transfer
permission.

Scenario checks from Phase 14 (timeout never re-buys, duplicate order refused,
restart safety, partial fill, veto binding) still pass.

## 7. Forward paper trading on real Coinbase data

`scripts/forward_paper.py` pulls **real** public candles (no key), runs the full
pipeline per coin, and books paper fills in the separate paper book. Run live in
this session on 2026-11-14:

```
BTC-USDC  NO TRADE: Championship 1 BUY / 6 SELL von 7 Strategien; Sieger SELL
ETH-USDC  NO TRADE: Championship 1 BUY / 6 SELL von 7 Strategien; Sieger SELL
SOL-USDC  NO TRADE: Championship 1 BUY / 6 SELL von 7 Strategien; Sieger SELL
```

The real market gave a SELL majority on all three, so the system opened nothing.
That is the point: it does not force a trade. `windows\forward_paper.ps1` runs
it on the laptop, one pass or as a loop.

## 8. Readiness — re-run

| #   | Criterion                   | Result                                                |
| --- | --------------------------- | ----------------------------------------------------- |
| 1   | Risk configuration          | PASS                                                  |
| 2   | Coinbase connection         | **FAIL** — no API key in the bot's process            |
| 3   | Portfolio isolation         | **FAIL** — needs the key's portfolio id               |
| 4   | Emergency stop              | PASS                                                  |
| 5   | Persistent loss calculation | PASS                                                  |
| 6   | Order de-duplication        | PASS                                                  |
| 7   | Restart safety              | PASS                                                  |
| 8   | API error handling          | PASS                                                  |
| 9   | Meeting required            | PASS                                                  |
| 10  | RiskManager veto            | PASS                                                  |
| 11  | Authentication              | PASS                                                  |
| 12  | Audit logging               | PASS                                                  |
| 13  | Current market data         | PASS                                                  |
| 14  | Order reconciliation        | **FAIL** — logic passes; live read-back needs the key |

## 9. Remaining blockers (why NOT READY)

1. **No API key in the bot's process.** Put a View+Trade key and the portfolio
   id in `coinbase-bot\.env` on the laptop (template `.env.example`), then run
   `windows\readiness.ps1`. That is the first time the SDK connector talks to
   Coinbase; expect a small fix.
2. **No strategy has passed validation and the live tape is not giving BUY
   signals.** Forward paper above opened nothing. There is still no evidence the
   bot would earn more than it pays in fees.
3. The runner and monitor exist and are tested, but nothing schedules them in
   production yet — that scheduling, and the final activation, are deliberately
   left for your decision.

READY will be reported only when the laptop run shows 14/14 and these risks are
addressed.
