# Phase 21 — Mobile-first 24/7 Cloud Deployment

**No persistent server exists yet, so the system is NOT DEPLOYED.** Everything
that can be built without your cloud login is built, tested, and ready to run on
a host you create. I created no cloud resources and authorized no payment.

## Status legend (as you asked)

| State       | Meaning here                                                       |
| ----------- | ------------------------------------------------------------------ |
| IMPLEMENTED | code exists in PR #50                                              |
| TESTED      | covered by the automated suite / a live local check                |
| DEPLOYED    | running on a permanent server — **nothing is, yet**                |
| CONNECTED   | talking to real Coinbase with your key — **blocked, key rejected** |
| BLOCKED     | needs your personal login/decision                                 |

## Phase 1 — Existing system (audited, not invented)

| Component                                         | State               | Evidence                                            |
| ------------------------------------------------- | ------------------- | --------------------------------------------------- |
| FastAPI backend, 23 API routes                    | IMPLEMENTED, TESTED | imports clean, routes enumerated                    |
| React dashboard (pixel office, 15 agents, mobile) | IMPLEMENTED, TESTED | tsc + build pass, iPhone-width render (Phase 12/13) |
| WebSocket (reconnect, heartbeat, resume, dedup)   | IMPLEMENTED, TESTED | browser test Phase 11/13                            |
| 15 agent workstations                             | IMPLEMENTED, TESTED | 15/15 mapped to real functions                      |
| Team meeting (8 steps, binding veto)              | IMPLEMENTED, TESTED | meeting + championship tests                        |
| Coinbase connector (official SDK)                 | IMPLEMENTED, TESTED | spec-conformance tests (Phase 17)                   |
| SecretStore (encrypted at rest)                   | IMPLEMENTED, TESTED | Fernet+PBKDF2 240k, no-plaintext test               |
| Scheduler + position monitor                      | IMPLEMENTED, TESTED | engine tests; off by default                        |
| RiskManager, persistent emergency stop            | IMPLEMENTED, TESTED | survives restart (live-checked)                     |
| Audit log                                         | IMPLEMENTED, TESTED | `state/audit.jsonl`, append-only                    |
| Auth (PBKDF2 240k, roles, lockout, CSRF)          | IMPLEMENTED, TESTED | auth tests                                          |
| Test suite                                        | TESTED              | **172 Python tests pass**                           |

No second trading engine was created; nothing working was replaced.

## Phase 2 — Free hosting (researched, not provisioned)

**Oracle Cloud "Always Free"** is still the best free always-on option, but the
free ARM (Ampere A1) allowance was **cut on 15 June 2026** from 4 OCPU / 24 GB to
**2 OCPU / 12 GB**, with **200 GB block storage**. That is still far more than
this backend needs (it is capped at 700 MB RAM in the service file). Caveats to
know before you rely on it:

- **Capacity:** A1 instances are sometimes unavailable in a region ("out of
  host capacity"); you may need to retry or pick another availability domain.
- **Deletion risk:** if A1 usage exceeds the free allowance, Oracle can disable
  and delete the instance after 30 days unless you upgrade to paid. Stay within
  2 OCPU / 12 GB and it remains free.
- **Region:** pick a home region close to you at signup; it cannot be changed.
- Verify the current numbers on Oracle's own page before signup — public sources
  disagree and some are stale.

**Alternatives if Oracle has no capacity:** a small computer you own (Raspberry
Pi / old PC) + Cloudflare Tunnel (free), or Fly.io's free allowance (may idle).
Render/Railway free tiers **sleep** and are unsuitable for the 24/7 scheduler.

**No paid instance, no card charge, no auto-upgrade was created or authorized.**

## Phase 3 — Deployment artifacts (IMPLEMENTED, syntax-checked)

New in `coinbase-bot/deploy/`:

- `install.sh` — idempotent Ubuntu installer (venv, deps, frontend build, dirs).
- `hypergrok.service` — systemd unit: **auto-start on boot, auto-restart on
  crash**, `MemoryMax=700M`, hardening. The backend starts in PAPER and a set
  emergency stop survives a restart, so **a restart never trades on its own**.
- `backup.sh` + `hypergrok-backup.{service,timer}` — daily backup of `state/`
  (the key stays **encrypted** in the backup), keeps the last 14.
- `healthcheck.sh` — `/api/health` probe.
- `cloudflared-config.example.yml` — tunnel ingress template.

Persistent data lives in `state/` (encrypted key, loss ledger, positions,
users, audit) — all gitignored. DEPLOYED only once this runs on your server.

## Phase 4 — Cloudflare (BLOCKED on your login)

Config template is provided. The tunnel + Access setup needs your Cloudflare
account, so I stop here. On your iPhone (Safari): create a tunnel, route the
hostname to `http://127.0.0.1:8787`, and add a **Cloudflare Access** policy that
allows only your e-mail — Access sits in front of the dashboard. HTTPS and
WebSocket work through the tunnel; the backend never faces the public internet.

## Phase 5 — Mobile Coinbase setup (IMPLEMENTED, TESTED; CONNECTED is BLOCKED)

`/setup` (Phase 20) is live: authenticated HTTPS, key pasted once, encrypted at
rest, read-only verification before storing. **Your uploaded key is rejected**
(it has transfer permission and sits in an empty portfolio), so Coinbase is
**not CONNECTED**. Because that key was in a chat, **rotate it**: create a new
CDP key — View + Trade only, no transfer, in the portfolio holding your
17.10 USDC — and enter it only in `/setup` over HTTPS.

## Phase 6-8 — Agents, scheduler, dashboard

IMPLEMENTED + TESTED (above). The scheduler and monitor are prepared for 24/7
and are **off by default**; even automatic sells are real orders and stay
blocked until your separate activation. The dashboard shows real backend data
and marks missing data STALE/UNAVAILABLE — no fake profit.

## Phase 9 — Security audit

| #   | Check                   | Result                                                      |
| --- | ----------------------- | ----------------------------------------------------------- |
| 1   | Secret encryption       | PASS — Fernet+PBKDF2 240k, ciphertext-only on disk (test)   |
| 2   | Password security       | PASS — PBKDF2-HMAC-SHA256, 240k, per-user salt              |
| 3   | Session security        | PASS — 12 h TTL, die on restart                             |
| 4   | HTTPS                   | via Cloudflare Tunnel (BLOCKED on your setup)               |
| 5   | CSRF                    | PASS — double-submit token on state-changing routes         |
| 6   | Rate limits             | PARTIAL — login lockout (5/5 min); no per-route limiter yet |
| 7   | API-key permissions     | PASS — transfer key refused at construction                 |
| 8   | Portfolio isolation     | PASS — per-account `retail_portfolio_id` check              |
| 9   | Audit logs              | PASS — append-only `state/audit.jsonl`                      |
| 10  | Backup & recovery       | IMPLEMENTED — `deploy/backup.sh` + timer                    |
| 11  | Emergency stop          | PASS — persistent, survives restart, fail-closed            |
| 12  | Position reconciliation | PASS — `reconcile_fills`, unresolved-order block            |
| 13  | Scheduler safety        | PASS — no real buy; off by default                          |
| 14  | Network access          | PASS — backend binds 127.0.0.1 only                         |
| 15  | Server restart          | PASS — systemd auto-restart, PAPER on boot                  |

One honest gap: **no per-route rate limiting** beyond login throttling. Cloudflare
Access in front mitigates it; a limiter can be added if you want.

## Phase 10 — Final status

- **Files created this phase:** `deploy/{install.sh, hypergrok.service,
backup.sh, hypergrok-backup.service, hypergrok-backup.timer, healthcheck.sh,
cloudflared-config.example.yml}`, this report.
- **Tests:** 172 pass.
- **Hosting:** NOT DEPLOYED (no permanent server exists).
- **Cloudflare:** BLOCKED on your login.
- **Coinbase:** NOT CONNECTED (key rejected — rotate it).
- **Dashboard URL:** none yet; it will be your Cloudflare hostname after setup.
- **Cost:** 0. No paid service, no card, no upgrade.
- **Security:** strong; one non-blocking gap (per-route rate limiting).

### Your next steps (iPhone only)

1. **Rotate the Coinbase key** (View + Trade, no transfer, correct portfolio).
2. **Create a free Oracle Always Free VM** (or use a computer you own). Confirm
   the free config first; do not upgrade to paid.
3. Tell me the VM is ready — I will give you the exact copy-paste commands
   (they are already in `deploy/`) and the Cloudflare steps.
4. Set up **Cloudflare Tunnel + Access** (only your e-mail).
5. Open `https://<dein-hostname>/setup`, paste the new key, done.

Absolute rules kept: no real order, no withdrawal, no leverage, no auto
activation, no secrets in GitHub, no paid service, no merge, all safety limits
intact.
