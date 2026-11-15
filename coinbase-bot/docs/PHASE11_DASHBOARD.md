# Phase 11 — React Dashboard + WebSocket Backend

A real, running application: React + TypeScript + Vite + Tailwind + Framer
Motion + GSAP + Recharts + Lucide in front of a FastAPI/WebSocket backend that
wraps the **existing** trading system. No second trading engine.

## 1. Implemented functions

| Area                 | Where                  | What it does                                                                                                                       |
| -------------------- | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| REST + WebSocket API | `server/app.py`        | `/api/health`, `/api/state`, `/api/scanner`, `/api/meeting/run`, `/api/mode`, `/api/emergency_stop`, `/api/balance/refresh`, `/ws` |
| Event bus            | `server/app.py`        | Sequence numbers, 500-event history, duplicate suppression by event id, resume via `?since=`                                       |
| Market poller        | `server/app.py`        | Real public Coinbase candles every 30 s; marks `DATA STALE` instead of inventing prices                                            |
| Workstation map      | `server/agents_map.py` | 15 visible stations mapped to real backend functions; 3 are honestly `NOT CONNECTED`                                               |
| Frontend             | `web/src`              | 12 pages, pixel office, agent terminals, live feed, charts                                                                         |
| WS client            | `web/src/lib/ws.ts`    | Auto-reconnect with backoff, 40 s heartbeat watchdog, sequence dedup, resume                                                       |

## 2. Components

`StatsCard` (Framer Motion + Lucide, exactly the requested shape), `PixelRobot`,
`PixelOffice`, `AgentTerminal`, `LiveActivityFeed`, `ProfitChart` (Recharts),
`Panel`, `Row`, `RiskCenter`, `ConnectorStatus`, `MarketScanner`, `ModeBadge`.

Pages: AI Office, Command Center, Live Market, Team Meeting, Coinbase Trading,
Memecoin Scanner, Portfolios, Live Profit, Trade History, Risk Center,
Connectors, Settings.

## 3. Agents actually running

The six backend agents plus four debate voices. They are driven by the existing
`hold_meeting()`; the dashboard only renders what they emit. Of the 15 visible
workstations, **12 are backed by real code** and **3 report NOT CONNECTED**
(Whale Tracker, Smart Money Analyst, Social Sentiment) because no such function
exists in this repository.

## 4. WebSocket status

Verified in a real browser: the client reaches `open`, receives the agent
statements of a real meeting, and the office animates from those events. The
server sends a heartbeat every 15 s; the client forces a reconnect after 40 s of
silence and resumes from its last sequence number, so no event is applied twice.

## 5. Coinbase data

Live prices from public candles (BTC/ETH/SOL) refresh every 30 s and show
`DATA STALE` when a fetch fails. The real balance is handed in through
`/api/balance/refresh` by the operator after reading it with the authorised
connector — **the server stores no API key** and the browser never sees one.

## 6. Browser test results

- `tsc --noEmit`: clean.
- `vite build`: success (781 kB JS, 238 kB gzip).
- Backend: `/api/health` ok, `/api/state` returns **401 without a token**.
- Desktop 1440 px: login, office, real meeting (robots moved, 7 statements in
  the feed), agent terminal opens. **No console errors, no page errors.**
- iPhone 14 (390 px, touch, Safari UA): all 15 workstations present,
  **no horizontal scroll**, meeting runs from a tap.

## 7. Screenshots

`p12_desktop.png`, `p12_scene.png`, `p12_mobile.png` (captured from the running
app, not mockups).

## 8. Security status

Bearer token on every REST route and on the WebSocket; 401/4401 without it.
State changes are POST-only. No API key, secret or private key reaches the
browser. CORS is limited to the local dev origin. The dashboard cannot bypass
the backend: live execution still requires confirmed limits plus a per-order
approval phrase inside `modes.py`. Emergency stop forces PAPER.

## 9. Open problems

- **No deployment.** The backend binds to `127.0.0.1` only. Exposing it needs a
  reverse proxy, TLS and a stronger auth story than a shared bearer token.
  Nothing is reachable from the internet, so the iPhone test ran locally.
- Single shared token, no user accounts, no roles, no rate limiting, no
  persistent audit log yet.
- JS bundle is one 781 kB chunk (no code splitting).
- Recharts P&L chart has no data points because no trade was executed; it says
  so instead of drawing a fake curve.

## 10. Start instructions

```bash
# terminal 1 — backend (prints the dashboard token once)
cd coinbase-bot && ./start_backend.sh

# terminal 2 — frontend dev server with proxy
cd coinbase-bot && ./start_frontend.sh      # http://localhost:5173

# or production: build once, backend serves it on http://127.0.0.1:8787
cd coinbase-bot/web && npm run build
```

Paste the printed token into the login screen. It is stored only in the
browser's local storage and never committed.
