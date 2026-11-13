# Phase 13 — Live Mobile Trading Headquarters

Continues PR #50. Nothing was overwritten, no second trading engine. The pixel
office, the 8-step meeting, the risk manager and the trading modes are intact.

## 1. Implemented functions

| Area               | File                            | What it does                                                                                                               |
| ------------------ | ------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Whale Tracker      | `multimarket/whale.py`          | Real supply + measured on-chain activity rate from the free Solana RPC                                                     |
| Smart Money        | `multimarket/smart_money.py`    | Mint/freeze authority structure + activity; a real structural risk grade                                                   |
| Social / Attention | `multimarket/social.py`         | CoinGecko public trending (attention), DexScreener profile presence                                                        |
| Authentication     | `server/auth.py`                | User accounts, PBKDF2-SHA256 (240k iterations, per-user salt), sessions with expiry, roles, brute-force lockout, audit log |
| API hardening      | `server/app.py`                 | Session auth on every route, `require_admin` + CSRF header on all state-changing routes, WebSocket session auth            |
| Frontend login     | `web/src/lib/api.ts`, `App.tsx` | Username/password form, session + CSRF stored client-side, CSRF header on POST                                             |
| Performance        | `web/vite.config.ts`            | Manual chunks — main bundle went from 781 kB to **49 kB**                                                                  |
| RPC robustness     | `multimarket/solana_rpc.py`     | Retry with backoff on HTTP 429/503 (the public node throttles)                                                             |

## 2. The three previously missing agents — what is real

**05 Whale Tracker — CONNECTED (partial).**
Real: token supply, signature count, the time window those signatures cover and
the resulting transactions-per-hour rate, graded QUIET / NORMAL / BURST.
Measured live on a real memecoin mint: 100 signatures over 0.02 h =
**about 4737 tx/h -> BURST**.
**Not available:** top-holder distribution. `getTokenLargestAccounts` is
refused by the public node with _"Too many requests for a specific RPC call"_ —
verified for both USDC and small memecoins, and it still failed after 24 s of
backoff. It is reported as `UNAVAILABLE_FREE_RPC`, never estimated. A dedicated
RPC key would unlock it.

**06 Smart Money Analyst — CONNECTED (partial).**
Real: mint authority and freeze authority state, Token-2022 use, measured
activity, combined into a structural risk grade. Measured live: both
authorities revoked -> **LOW**.
**Not available:** early-buyer detection and per-wallet profit history need a
paid indexer -> `UNAVAILABLE_PAID_INDEXER`. Holder concentration -> see above.

**08 Social / Attention — CONNECTED (partial), renamed from "Sentiment".**
Real: CoinGecko's public `search/trending` endpoint (10 assets returned live),
plus whether a token publishes any links on DexScreener.
**Not available:** an actual sentiment score. CryptoPanic answers **403**
without a paid key from here, and no other free source was reachable. The field
is `UNAVAILABLE_NO_FREE_SOURCE`. Attention is labelled as attention, not as
sentiment. No scraping, no bypassing of any access restriction.

All 15 workstations now report `CONNECTED` (15/15 via `/api/health`), but three
of them carry explicit unavailability markers for the parts that free data
cannot deliver.

## 3. Available data sources

| Source                    | Status            | Note                                                               |
| ------------------------- | ----------------- | ------------------------------------------------------------------ |
| Coinbase (public candles) | CONNECTED         | BTC/ETH/SOL, 30 s poll, `DATA STALE` on failure                    |
| Solana RPC                | CONNECTED         | supply, authorities, signatures; `getTokenLargestAccounts` refused |
| GeckoTerminal             | CONNECTED         | new pools                                                          |
| DexScreener               | CONNECTED         | token profiles                                                     |
| Jupiter (lite-api)        | CONNECTED         | quotes, price impact                                               |
| CoinGecko trending        | CONNECTED         | attention only                                                     |
| CryptoPanic / news        | **NOT CONNECTED** | 403 without a paid key                                             |
| Birdeye, GMGN             | **NOT CONNECTED** | need keys / authorisation                                          |

## 4. Dashboard status

Unchanged in design: 15 pixel robots, 15 workstations, neon office, big
monitors, meeting room, live profit area, 12 pages, bottom agent bar. Agents
still move with GSAP only on real backend events.

## 5. Mobile access — **NOT DEPLOYED**

The dashboard renders correctly at iPhone 14 width (390 px, touch) and was
tested in a mobile browser context: 15 workstations present, no horizontal
scroll, login and meeting work by tap.

**It is not reachable from your iPhone.** No tunnel is running. The backend
binds to `127.0.0.1` only, and this container is ephemeral — a tunnel started
here would die with it. Setting up Cloudflare Tunnel + Access requires logging
into _your_ Cloudflare account, which only you can do. See section 10.

## 6. Security status

- Shared token **removed**. Real accounts with PBKDF2-SHA256, per-user salt,
  240 000 iterations. No password is stored in plain text (unit-tested).
- Sessions expire after 12 h and die on backend restart.
- Roles: `admin` may change state, `viewer` may only read.
- Every state-changing route requires the admin role **and** a matching CSRF
  token in `X-CSRF-Token`, which a cross-site form cannot supply.
- Brute force: 5 failed attempts per user and per IP trigger a 5-minute lockout
  (unit-tested, including that the correct password is then refused too).
- WebSocket authenticates with the session token; invalid closes with 4401.
- Audit log in `state/audit.jsonl`: logins, failures, lockouts, CSRF rejections,
  forbidden role attempts, WS connections.
- `state/` (users, audit, snapshots) is gitignored. The built frontend bundle
  was grepped for key/secret patterns: **clean**.
- Live trading unchanged: LIVE AUTONOMOUS locked, LIVE MANUAL needs confirmed
  limits plus a per-order approval phrase, emergency stop forces PAPER.

## 7. Test results

**104 Python tests pass.** New in this phase (19): password hashing without
plaintext, unique salts, broken-record handling, login/session/logout, expiry,
roles, brute-force lockout, audit logging, whale UNKNOWN on RPC failure, whale
activity-rate computation, no invented holder concentration, smart-money
HIGH on active mint authority, UNKNOWN without data, social never inventing a
sentiment score, trending parsing, missing-token handling.

Live checks against the running backend:

| Check                       | Result                                                   |
| --------------------------- | -------------------------------------------------------- |
| `/api/state` without login  | **401**                                                  |
| Login with wrong password   | **401**                                                  |
| Login with correct password | 200, role `admin`                                        |
| `/api/state` with session   | 200                                                      |
| POST without CSRF header    | **403**                                                  |
| `/api/intel/whale`          | 200, real data                                           |
| `/api/intel/social`         | 200, 10 trending, sentiment `UNAVAILABLE_NO_FREE_SOURCE` |
| Workstations connected      | 15 / 15                                                  |

Browser (real renders): wrong password rejected in the UI, WebSocket `open`,
15 workstations, meeting filled the feed, iPhone 390 px without horizontal
scroll. `tsc` clean, production build succeeds.

## 8. Screenshots

`p13_desktop.png`, `p13_mobile.png` — captured from the running application.

## 9. Open problems

- **No iPhone deployment** (section 5). This is the main gap.
- Sessions are in memory only; a restart logs everyone out.
- No per-route rate limiting yet — only login is throttled.
- `getTokenLargestAccounts` blocked on the free node, so holder concentration
  stays unavailable across whale, smart money and the memecoin risk gate.
- No real sentiment source without a paid key.
- Charts chunk is still 542 kB (Recharts), loaded eagerly.

## 10. Next steps — your part for iPhone access

I stopped here deliberately: it needs your account.

1. Install `cloudflared` on a machine that stays on (not this container).
2. `cloudflared tunnel login` — opens your Cloudflare account in a browser.
3. `cloudflared tunnel create hypergrok`, then route a hostname to
   `http://127.0.0.1:8787`.
4. In Cloudflare Zero Trust, put an **Access** policy on that hostname limited
   to your email. The free tier covers a single user.
5. Start the backend, then the tunnel. Open the hostname on the iPhone, sign in
   through Cloudflare Access, then with your dashboard account.

Both layers matter: Access keeps strangers off the hostname, the dashboard
login keeps the trading controls behind a real account. Do not expose
`127.0.0.1:8787` directly to the internet.
