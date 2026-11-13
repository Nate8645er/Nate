# Phase 12 — Pixel Art AI Trading Headquarters

The office from the reference image, built as a working React view on top of the
Phase 11 backend. Same app, same security rules, no second trading engine.

## 1. What matches the reference

- Dark futuristic trading room, pixel-art style (`shape-rendering: crispEdges`),
  neon green / cyan / violet lighting, scanline overlay.
- Headline **"15 AI AGENTS — ONE TRADING EMPIRE"** in a pixel typeface, with the
  subtitle **HYPERGROK AI TRADING EMPIRE · COINBASE · SOLANA · PUMP.FUN**.
- **15 individual workstations** in three rows of five, each with its own
  coloured pixel robot, monitor, numbered badge (01–15) and name plate.
- Large central trading monitor with live BTC / ETH / SOL prices and bars.
- Side screens: **SOLANA · SCAN** (left) and **RISK · DECISION** (right).
- Meeting table below the desks with a big screen showing the coin and verdict.
- Bottom agent navigation bar with all 15 colour chips (CEO, CMA, PFS, MH, WT,
  SMA, TA, SS, OCI, RSD, ATS, RM, TE, PM, L&O), plus a page navigation row.

Not reproduced: decorative plants, the cat, and the laurel/banner ornaments from
the reference. They carry no data, and the room already reads as the same scene.

## 2. The 15 workstations and what really drives them

| #   | Workstation              | Backend                             | Status            |
| --- | ------------------------ | ----------------------------------- | ----------------- |
| 01  | CEO / Orchestrator       | `meeting.hold_meeting` (Supervisor) | CONNECTED         |
| 02  | Crypto Market Analyst    | `core.MarketAnalyst`                | CONNECTED         |
| 03  | Pump.fun Scanner         | `multimarket.discovery`             | CONNECTED         |
| 04  | Memecoin Hunter          | `discovery.TokenScanner`            | CONNECTED         |
| 05  | Whale Tracker            | —                                   | **NOT CONNECTED** |
| 06  | Smart Money Analyst      | —                                   | **NOT CONNECTED** |
| 07  | Technical Analysis       | `trading_team.indicators`           | CONNECTED         |
| 08  | Social / Sentiment       | —                                   | **NOT CONNECTED** |
| 09  | On-Chain Intelligence    | `solana_rpc.fetch_onchain`          | CONNECTED         |
| 10  | Rug Pull & Scam Detector | `assess_memecoin_risk`              | CONNECTED         |
| 11  | AI Strategy              | `collaboration.DebateRoom`          | CONNECTED         |
| 12  | Risk Manager             | `core.RiskManager` (veto)           | CONNECTED         |
| 13  | Trading Execution        | connector + `modes` gate            | CONNECTED         |
| 14  | Portfolio Manager        | `multimarket.core.Portfolio`        | CONNECTED         |
| 15  | Learning & Optimization  | `trading_team.backtest`             | CONNECTED         |

**12 of 15 are real. 3 say NOT CONNECTED** and their robot is greyed out. No
fifteen independent AI processes are simulated.

## 3. Animations, driven only by real events

Robot states come from WebSocket events, never from a timer or random data:
`IDLE`, `ANALYZING`/`SCANNING` (typing), `MEETING` (walks to the table),
`RISK_CHECK`, `BUY_PREP` (green), `SELL_PREP` (red), `NO_TRADE` (amber),
`ERROR`, `OFFLINE`. Movement uses GSAP along per-agent SVG paths with
`getPointAtLength`, exactly the requested pattern, with the tangent angle
applied while walking.

## 4. Interactive workstations

Every station is clickable and tappable (a transparent hit rect covers the whole
desk, which also fixed a real tap-target bug found in testing). The terminal
overlay shows name, status, the backing function, last action and the activity
history for that station, and states plainly when no agent runs there.

## 5. Live data

Central monitor: real Coinbase prices, `DATA STALE` when a fetch fails.
Scanner page: the real token snapshot with MC/FDV, liquidity, volume, risk,
veto and category filters (<100k, <500k, <1M, >1M); missing values show
`UNKNOWN`. Offensive token names from on-chain data are masked in display only.

## 6. Mobile

iPhone 14 (390 px, touch): the same office scales down, all 15 robots stay
visible, the scene is not replaced by plain cards, and there is **no horizontal
scroll**. Verified with a real mobile browser context.

## 7. Test results

- TypeScript clean, production build succeeds.
- Desktop and iPhone renders captured from the running app.
- A real meeting moved the robots and filled the feed with 7 real statements;
  verdict **NO TRADE** (no consensus) — no order prepared.
- No console or page errors in either viewport.
- Backend rejects unauthenticated requests (401).

## 8. Remaining problems

- 3 workstations have no backend (by design, marked).
- Not deployed: backend is localhost-only, so the iPhone test was local.
- Single shared token; no accounts, roles or rate limiting.
- Bundle not code-split (781 kB).
- The reference's decorative elements (plants, cat, banners) are not drawn.
