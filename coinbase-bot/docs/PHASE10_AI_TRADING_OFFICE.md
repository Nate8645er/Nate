# Phase 10 — AI Trading Office + Live Control Center

Built on the existing stand (PR #50). No second trading engine: the meeting
orchestrates the six agents that were already there. Live trading stays off.

## 1. Implemented components

| Component | File | What it does |
|---|---|---|
| Trading modes | `trading_team/modes.py` | `PAPER` / `LIVE MANUAL` / `LIVE AUTONOMOUS`. Autonomous is hard-locked; live manual needs confirmed, complete limits **and** a per-order approval phrase. |
| Absolute limits | `trading_team/modes.py` | Total capital, max daily loss, max total loss, max slippage, max open exposure. `tightened()` clamps every attempt to raise a ceiling back down; `confirmed` cannot be set by code. |
| Team meeting | `trading_team/meeting.py` | The eight steps, each a recorded `Statement(step, agent, decision, rationale)`. Decisions are BUY / SELL / HOLD / NO TRADE / VETO. |
| Office run | `run_office.py` | Holds real meetings on live candles with the real balance and writes `state/office_snapshot.json`. |
| AI office view | `dashboard/office.html` | Animated SVG office; GSAP moves agents along SVG paths to the meeting table, driven only by recorded statements. |
| Control centre | `dashboard/index.html` (Phase 9) | Connector status, portfolios, scanner, risk centre. |

### The eight steps

1. **MarketAnalyst** reads trend, momentum, volatility from real candles.
2. **Strategist** turns the debate consensus into a plan with stop-loss / take-profit.
3. **Debate**: every voice states a stance on the *same* report and may contradict.
4. **RiskManager** evaluates. A VETO ends the meeting — binding, no override path.
5. **Supervisor** checks the consensus; no consensus means NO TRADE.
6. **ExecutionAgent** sizes the order against the **real** balance and the ceiling.
7. **TradeReviewer** re-checks size, fee and limits.
8. **Gate** reports whether execution would be allowed. *The meeting never sends
   an order itself* — it only prepares one and names the approval phrase.

There is never an obligation to trade: steps 2, 4, 5, 6 and 7 can all end in
NO TRADE or VETO.

## 2. Agents actually running

All six are wired and appear in every recorded meeting: MarketAnalyst,
Strategist, RiskManager, ExecutionAgent, TradeReviewer, Supervisor, plus the
four debate voices (Trend, Momentum, MeanReversion, VolSkeptiker).

## 3. Coinbase connection

- Real balance read before the meeting through the authorised connector:
  **17.1068518096028 USDC** (portfolio "Default").
- Real market data: public daily candles for BTC-USD, ETH-USD, SOL-USD.
- Live execution was already proven in Phase 3 (one real buy + one real sell,
  reconciled to the cent). Nothing was executed in Phase 10.
- No transfer or withdrawal rights are used anywhere.

## 4. Real meeting results (this run)

| Symbol | Consensus | Unanimous | Final | Order prepared | Gate |
|---|---|---|---|---|---|
| BTC-USD | BUY | no | **NO TRADE** | no | not reached |
| ETH-USD | BUY | no | **NO TRADE** | no | not reached |
| SOL-USD | SELL | no | **NO TRADE** | no | not reached |

All three stopped at step 5: the Supervisor refused to proceed without a
carried consensus. No order was prepared, so the execution gate was never
reached. This is the honest outcome, not a configuration failure.

## 5. Dashboard functions

AI office scene with six desks and a meeting room; play / reset / emergency
stop; per-symbol tabs; live activity feed of the real statements; live profit
monitor (real balance, capital ceiling, open position, realised P&L, open
orders, mode, limits-confirmed); risk centre; connector status. Dark futuristic
palette (black, deep blue, violet, neon cyan, green up / red down). Works at
phone width with no horizontal scroll.

**Animations are visualisation only.** The frontend holds no keys, makes no
trading decision and cannot trigger an order. The backend decides.

## 6. Real-time data

This build uses a **snapshot**, not a WebSocket stream: the page states its
snapshot time and the source of every figure. A push channel (WebSocket/SSE)
with reconnect and de-duplication is designed for but **not implemented** —
see section 8.

## 7. Test results

`python -m pytest tests` gives **85 passing**, including Phase 10:

- default mode is PAPER; LIVE AUTONOMOUS refuses to be selected at all
- LIVE MANUAL refuses without confirmed, complete limits
- limits can only be tightened; raising a ceiling is clamped; `confirmed` is not settable by code
- live execution needs the exact approval phrase (wrong size or `None` is refused)
- PAPER never allows live execution even with a valid phrase
- emergency stop forces PAPER, blocks execution and blocks mode changes
- position size capped by capital ceiling, real balance and open exposure
- meetings record every agent with a rationale (traceable)
- a risk veto blocks the order and ends the meeting
- order size never exceeds the real balance; below minimum means NO TRADE
- the meeting serialises for the dashboard

Browser checks (Playwright, real renders): animation advances through the real
statements, **no console errors**, **no horizontal scroll at 390 px**,
screenshots captured for desktop and phone.

## 8. Remaining risks and what is NOT built

- **No React/Vite/TypeScript app.** The office is a self-contained animated
  page (GSAP from CDN), not the component library in the brief
  (StatsCard, AgentCard, ...). Those components do not exist.
- **No WebSocket/SSE backend, no reconnect logic, no de-duplication** — the
  page renders a snapshot.
- **No authentication and no deployment.** This container is ephemeral and must
  not host a reachable trading backend. The office is published as a *private*
  Claude artifact, which is how it can be opened on the iPhone today.
- **Limits are unset** (daily loss, total loss, open exposure are 0), so
  LIVE MANUAL is refused and LIVE AUTONOMOUS is locked.
- The strategy evidence is still thin (Phase 7: only `macd_trend` on BTC passed,
  in a mostly rising sample). That is not a mandate to trade.

## 9. Approvals still required

Before any autonomous live step, the user must separately and explicitly
confirm the **final** risk configuration:

1. total trading capital, 2. max daily loss, 3. max total loss,
4. max open exposure, 5. max slippage.

Only then can LIVE MANUAL be selected — and even then every single order needs
its own approval phrase. LIVE AUTONOMOUS additionally needs a separate decision
after that.

## 10. Security

No real order, no transfer, no withdrawal, no leverage, no API key in the
frontend, no secret printed, no auto-merge, main untouched. All earlier
safeguards (connector approval phrases, cloid idempotency, kill switch,
memecoin veto) remain in place and tested.
