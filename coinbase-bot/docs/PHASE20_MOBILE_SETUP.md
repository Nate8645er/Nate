# Phase 20 — Mobile-only setup (iPhone / Safari)

Everything to run and control HyperGrok from your iPhone is built. One thing I
cannot provide from here, and it is the central blocker:

## The blocker — honest and specific

**This cloud session is not a permanent server.** Its container is wiped after
inactivity, and I cannot keep a secret or a web page alive beyond the session.
So the authenticated setup page and the encrypted key store I built **must run
on a host that stays on**. Pick one of the free options below; then the whole
key setup and all control happen in Safari, no laptop.

## What is built (works the moment it runs on a persistent host)

- **`/setup`** — a self-contained, mobile HTML page (no build step). You log in
  with your dashboard admin account over HTTPS, paste the CDP key file content,
  choose an encryption passphrase, and submit. The key is sent once and is
  never stored in the browser.
- **Encrypted secret store** (`server/secretstore.py`) — the key is encrypted at
  rest with a Fernet key derived from your passphrase (PBKDF2-HMAC-SHA256,
  240 000 iterations, random salt) and written to `state/secret.enc`. The
  passphrase is never stored; the plaintext key lives only in memory after an
  unlock. Nothing is ever written to GitHub, logs or the chat.
- **Read-only verification on setup** — before storing, the server checks the
  key live: view+trade, **transfer must be off** (a transfer key is refused),
  the portfolio, and the USDC/BTC balance. Only a valid key is stored.
- **Key endpoints** (admin + CSRF): `/api/key/setup`, `/api/key/unlock`,
  `/api/key/lock`, `/api/key/clear`, `/api/key/status`.
- **Scheduler + position monitor** (`/api/scheduler`) — a persistent background
  loop that runs the forward-paper cycle and watches open positions for
  stop-loss / take-profit / time exits. It **never sends a real buy**; real
  exits only reduce risk. Off by default; you toggle it from the dashboard.
- **Dashboard** — the existing React app is already mobile-responsive (tested at
  iPhone width) and shows real Coinbase data via `/api/live`: balance,
  positions, realised/unrealised/daily/total P&L, fees, agent decisions, team
  meetings, risk status, mode control and the emergency stop.
- **172 tests pass** (10 new for the secret store and key endpoints).

## Hosting — free options (pick one)

| Option                                                                  | Always on?          | Cost      | iPhone-only setup                  | Notes                                          |
| ----------------------------------------------------------------------- | ------------------- | --------- | ---------------------------------- | ---------------------------------------------- |
| **Oracle Cloud "Always Free" VM** + Cloudflare Tunnel                   | **Yes**             | Free      | Hard but possible in Safari        | Best free always-on box (ARM VM). Recommended. |
| A computer you own (Mac mini, Raspberry Pi, old PC) + Cloudflare Tunnel | Yes (if left on)    | Free      | Host setup needs the computer once | Simplest if you have the hardware.             |
| **Fly.io** free allowance + a volume for `state/`                       | Mostly              | Free tier | Possible via Safari + their web UI | May idle; fine for monitoring.                 |
| Render / Railway free                                                   | Sleeps after 15 min | Free tier | Safari                             | **Not** good for the scheduler (sleeps).       |

**No paid service was used or signed up for.** If you ever want a paid always-on
box (simplest, ~5 EUR/month), tell me first — I will not do that without your yes.

## iPhone-only setup, step by step (Safari)

You need the backend running on one of the hosts above, reached over HTTPS
through a **Cloudflare Tunnel** with a **Cloudflare Access** policy locked to
your e-mail. The host setup (VM + tunnel) is the one involved part; after that,
everything is Safari taps.

**A. One-time host + tunnel (in Safari, on the host's web consoles)**

1. Create a free Oracle Cloud account and an **Always Free** VM (Ubuntu). Use
   the browser Cloud Shell to run the setup — no laptop needed.
2. On the VM: clone the repo, `pip install -r coinbase-bot/requirements.txt`,
   build the frontend once (`cd web && npm ci && npm run build`).
3. Install `cloudflared`, run `cloudflared tunnel login` (opens a Cloudflare
   login you complete in Safari), create a tunnel, and route a hostname to
   `http://127.0.0.1:8787`.
4. In Cloudflare **Zero Trust -> Access**, add an application for that hostname
   with a policy that allows **only your e-mail**.
5. Set the host env var `HYPERGROK_SECRET_PASSPHRASE` to the passphrase you will
   use (this is the host's own secret vault, so the key auto-unlocks after a
   restart). Start the backend, then the tunnel.

**B. Daily use — pure Safari on the iPhone**

6. Open `https://<dein-hostname>/`. Cloudflare Access asks for your e-mail code,
   then the dashboard login appears. Sign in with your admin account.
7. **Set up the Coinbase key:** open `https://<dein-hostname>/setup`. Paste the
   content of your new CDP key file (from the iPhone Files app — open it, copy
   all, paste), enter your passphrase, tap **Pruefen & verschluesselt speichern**.
   The page shows the read-only verification; the key is stored encrypted.
8. From the dashboard you then monitor the team, watch meetings, see the
   balance, positions and P&L, switch the trading mode, toggle the scheduler,
   and hit the **Not-Aus** — all by tap.

## Important: your key still has to be fixed first

The key you uploaded has **transfer permission** and is bound to a **portfolio
without funds** (see `PHASE18_19_KEY_INTEGRATION.md`). The `/setup` page will
**refuse** it, correctly. Create a new CDP key: **View + Trade only, no
transfer**, inside the portfolio that holds your 17.10 USDC, then use it in
step 7. And do not paste a key into the chat again — only into `/setup` over
HTTPS.

## Readiness

Unchanged: **NOT READY**, because no valid key is connected yet. With a correct
key via `/setup`, the connector-dependent criteria (2 connection, 3 isolation,
14 reconciliation) pass and the dashboard fills with real data. Live autonomous
stays locked; activation remains a separate, explicit decision.

## Safety recap

No real order, no withdrawal, no leverage, no auto-activation, no paid service,
no merge. The key never touches GitHub, logs or chat; at rest it is encrypted,
in memory only after your unlock.
