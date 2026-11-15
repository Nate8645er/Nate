# Phase 14 — Autonomous Live Trading Readiness

**Verdict: NOT READY — 11 of 14 criteria pass.**
`LIVE_AUTONOMOUS_ENABLED = False`. No real order was sent in this phase. Nothing
was armed. Main is untouched; everything is in PR #50.

The three failing criteria all have the same cause: the bot's own connector has
never run with an API key. They cannot be passed from this cloud session — they
have to be passed on the machine that will hold the key (section 10).

## 1. Actual Coinbase status (read 2026-11-13/14, read-only)

| Item | Value |
| --- | --- |
| Portfolios on the account | 1 — "Default" (`26329da5-…b846`) |
| Available | 17.1068518096028 USDC, nothing on hold |
| Open orders | 0 |
| Positions | none (USDC only) |
| Fee tier | Intro — taker 0.10 %, maker 0.09 % |
| Test order BUY `66b81bf7-…ab8c` | FILLED, 0.00016017 BTC @ 68549.8, fee 0.01098, cost 10.9906 USDC |
| Test order SELL `fcda9f60-…6271` | FILLED, 0.00016017 BTC @ 68541.14 (3 fills), fee 0.01098, proceeds 10.9673 USDC |
| Round-trip result | **−0.0233 USDC**, fees included |

Both earlier orders are still served by the API and match the audit document.

**Important distinction.** These reads, like the two test orders, went through
the Coinbase connector of the Claude session. The repository's own connector
(`coinbase_connector/connector.py`, official SDK) is what an autonomous bot
would use, and it has only ever run against mocks: there is no API key in this
environment. Two methods added in this phase (`get_open_orders`,
`find_order_by_client_id`) are therefore untested against the real API.

## 2. Confirmed risk values (`trading_team/risk_config.py`)

| Setting | Value |
| --- | --- |
| Platform / type | Coinbase Advanced Trade, SPOT only |
| MAX_ALLOCATED_CAPITAL | 17.10 USDC |
| MAX_POSITION_FRACTION | 1.0 (allowed, never required) |
| MAX_DAILY_LOSS | 17.10 USDC |
| MAX_TOTAL_LOSS | 17.10 USDC |
| MAX_SLIPPAGE | 2.0 % |
| Leverage, margin, withdrawals, transfers | disabled |
| Allowed products | BTC-USDC, ETH-USDC, SOL-USDC |

Two things about these values, stated once:

- **They permit the total loss of the 17.10 USDC.** Both loss limits equal the
  whole allocation, so the loss gate only trips when everything is gone. If you
  want a gate that acts earlier, lower one of them; the RiskManager can tighten
  at any time but nothing can raise them.
- 2.0 % slippage is looser than the 1.0 % placeholder used before. It is set by
  your instruction as part of the confirmed baseline.

The 17.10 ceiling is fixed in code. A deposit does not raise it. The account
currently holds 17.1069 USDC; the 0.0069 above the ceiling is not used.

## 3. What was implemented

| File | Purpose |
| --- | --- |
| `trading_team/risk_config.py` | The confirmed values, one source of truth |
| `trading_team/persistence.py` | Durable emergency stop, loss ledger, order ledger (atomic writes) |
| `trading_team/modes.py` | Persistent stop, loss gates, slippage gate, product allow-list, `arm_autonomous` |
| `trading_team/execution_guard.py` | Pre-trade gate, fill classification, read-back after timeout |
| `trading_team/live_pipeline.py` | The 12-step cycle, meeting ticket check, positions, exits |
| `trading_team/readiness.py` | LIVE_READINESS_CHECK, 14 criteria |
| `server/app.py` | `/api/readiness`, `/api/live`, `/api/emergency_stop/clear`, durable state |
| `web/src/components/LivePanels.tsx` | Readiness panel, real-money P&L, order history |
| `scripts/readiness_check.py`, `windows/*.ps1`, `.env.example` | Laptop setup |

How the lock works. `LIVE AUTONOMOUS` can be selected only after
`ModeController.arm_autonomous()` succeeded, and that needs all of: no
emergency stop, durable state, confirmed limits, no loss limit reached, a
passing readiness report, a named person, and the exact phrase
`AUTONOMES LIVE TRADING AKTIVIEREN 17.10 USDC`. No code in the repository calls
it and no HTTP route exposes it. Arming is held in memory only, so every
restart comes back in PAPER and unarmed.

## 4. Meeting flow before every order

1–6 are the existing `hold_meeting` (MarketAnalyst, Strategist, the four debate
voices, RiskManager with binding veto, Supervisor, ExecutionAgent,
TradeReviewer). The meeting never sends. Afterwards:

7. Order preview and current bid/ask from Coinbase.
8. Final check: the order is **rebuilt from the meeting record** and compared
   with what the RiskManager approved, the capital ceiling and the approval
   text; then stop, mode, product, loss limits, market-data age, fee, balance,
   minimum size, open orders, exposure, slippage, price impact.
9. Client order id is written to disk, then the order is sent.
10. The fill is read back from Coinbase.
11. Review: requested vs. actually spent.
12. Position and, on exit, realised P&L (fees included) go to the ledger.

Every cycle is appended to `state/live_meetings.jsonl` with time, coin, market
data, each agent's statement, objections, consensus, veto, decision and size.

## 5. Order safety checks

| Situation | Behaviour |
| --- | --- |
| Balance, fee, minimum, slippage or data age unknown | order blocked |
| Market data older than 90 s | blocked |
| Same client order id again, also after a restart | refused before sending |
| Timeout while sending | **no retry**; emergency stop; order stays "unresolved" and blocks everything until Coinbase was asked |
| Status unreadable after sending | emergency stop, blocked |
| Partial fill | only the filled amount is booked; no automatic top-up |
| Loss limit reached | persistent emergency stop |
| Emergency stop | survives restart; unreadable stop file counts as STOP; clearing needs an admin and a written reason, and returns to PAPER |
| RiskManager veto, missing consensus, incomplete or altered meeting record | no order |

A stop-loss is a decision rule, not a guarantee: a market order fills at the
price available, which can be worse than the stop level.

## 6. Test results

- **125 Python tests pass** (104 existing + 21 new).
- All ten required scenarios pass: total capital loss, daily limit, total limit
  across days and restarts, slippage above 2 %, Coinbase timeout, partial fill,
  duplicate buy, restart during an order, manipulated agent decision,
  RiskManager veto. Each asserts on the number of orders the fake connector
  actually received.
- Backend, live: `/api/readiness` 401 without login; `LIVE AUTONOMOUS` refused;
  emergency stop set, backend killed and restarted, **stop still active**;
  clearing refused without reason (422) and without CSRF (403).
- `tsc` clean, production build succeeds.
- Browser, desktop 1440 px and iPhone 14: login, Risk Center, readiness run
  shows `NOT READY · 11/14`, Live Profit shows the PAPER badge, WebSocket open,
  no horizontal scroll, no console errors.

Readiness result in this environment:

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Risk configuration | PASS |
| 2 | Coinbase connection | **FAIL** — no API key in the bot's process |
| 3 | Portfolio isolation | **FAIL** — needs the key's portfolio id |
| 4 | Emergency stop | PASS |
| 5 | Persistent loss calculation | PASS |
| 6 | Order de-duplication | PASS |
| 7 | Restart safety | PASS |
| 8 | API error handling | PASS |
| 9 | Meeting required | PASS |
| 10 | RiskManager veto | PASS |
| 11 | Authentication | PASS |
| 12 | Audit logging | PASS |
| 13 | Current market data | PASS |
| 14 | Order reconciliation | **FAIL** — logic passes, live read-back needs the connector |

## 7. Dashboard status

The pixel office, 15 workstations and event-driven movement are unchanged.
New: Risk Center shows the confirmed limits, current daily/total loss and the
persistent stop; a Live Readiness panel runs the check on demand; Live Profit
shows real balance, allocated capital, positions, realised / unrealised / daily
/ total P&L, fees and order history, with a LIVE or PAPER badge. Unknown values
show `UNBEKANNT`. All P&L figures are zero because this system has sent no
order. Unrealised P&L would be marked with the USD price feed, not USDC.

## 8. Windows 11 start

Not tested on Windows — written here, run there. Requirements: Python 3.11+
and, for the one-time dashboard build, Node.js 20 LTS.

```powershell
git clone https://github.com/Nate8645er/Nate ; cd Nate\coinbase-bot
git checkout claude/coinbase-ai-trading-bot-f6i4h3
powershell -ExecutionPolicy Bypass -File windows\build_frontend.ps1   # once
powershell -ExecutionPolicy Bypass -File windows\start_backend.ps1
```

The first start prints the admin password once. Open `http://127.0.0.1:8787`.
`windows\diagnose.ps1` shows RAM, disk, port, health and the stop file.
`start_backend.ps1` installs only into `.venv` inside the folder, rotates
`logs\backend.log` at 5 MB and restarts the backend after a crash (always in
PAPER). Idle footprint is one Python process; no local AI model is started.
After the build `web\node_modules` can be deleted.

## 9. iPhone access — not set up, needs your Cloudflare login

1. Install `cloudflared` on the laptop, run `cloudflared tunnel login`.
2. `cloudflared tunnel create hypergrok`, route a hostname to
   `http://127.0.0.1:8787` (WebSockets work through the tunnel).
3. In Cloudflare Zero Trust add an Access application for that hostname,
   policy: your e-mail only.
4. Start the backend, then `cloudflared tunnel run hypergrok`.

Access protects the hostname, the dashboard login protects the controls. The
backend stays on 127.0.0.1; do not open port 8787 in the firewall. Requires a
domain in your Cloudflare account. Sessions end when the backend restarts.

## 10. Remaining blockers

To reach 14/14:

1. Create a Coinbase API key with **View + Trade only**, put it in
   `coinbase-bot\.env` on the laptop (see `.env.example`) together with
   `HYPERGROK_PORTFOLIO_ID`. Do not send it to me or commit it.
2. Run `windows\readiness.ps1`. This is the first time the SDK connector
   talks to Coinbase; expect that something small needs fixing.

Beyond the 14 criteria — these do not show up in the check but matter:

- **No strategy has passed validation.** Phases 6 and 7 ended in NO TRADE, and
  the real debate room returned NO TRADE on every series tried here. Expect the
  bot to trade rarely, and there is no evidence it would earn more than it pays
  in fees.
- **No runner exists.** Nothing calls `run_cycle` on a schedule. That loop and
  the stop-loss / take-profit monitor that calls `close_position` are the last
  pieces and were deliberately not built before activation is decided.
- The meeting only produces buys; exits go through `close_position`.
- An emergency stop also blocks exits: an open position then stays open until
  you act.
- Stops are not resting orders on the exchange; they only work while the
  laptop runs and is online.
- The loss-limit day is the UTC day.
- Memecoin sources stay analysis and paper only; no Solana swap is enabled.

## Final activation

Not requested now, because the verdict is NOT READY. When the check shows
14/14 on your laptop, the activation confirmation must name the configuration
above and use the exact phrase from section 3.
