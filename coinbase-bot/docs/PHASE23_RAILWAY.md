# Phase 23 — Railway deployment prep (and a repo mix-up to fix)

## 1. Which repository has the latest complete code

**`Nate8645er/Nate`** (note the `er`), branch
**`claude/coinbase-ai-trading-bot-f6i4h3`**, PR #50. All of Phase 1-22 is there.

## 2. Is it in your `Nate8645/Nate`?

**Almost certainly no — that is a different GitHub account** (`Nate8645`, without
`er`). Every commit I made went to `Nate8645er/Nate`. This session only has
access to `Nate8645er/Nate`, so **I cannot read or push to `Nate8645/Nate`** and
cannot move the code there myself. You have to connect the two (step 3).

## 3. Secure transfer — two clean options (your action)

**Option A (simplest): point Railway at `Nate8645er/Nate`.**
If that account is also yours, give Railway access to it and deploy the branch
`claude/coinbase-ai-trading-bot-f6i4h3` (or the new `railway-deploy` branch).
No copying, nothing can go stale. Recommended.

**Option B: mirror into `Nate8645/Nate` yourself.**
On GitHub (Safari): open `Nate8645/Nate` -> you can **Import** or push a mirror.
From any git client:

```
git clone --bare https://github.com/Nate8645er/Nate.git
cd Nate.git && git push --mirror https://github.com/Nate8645/Nate.git
```

This is **your** push (your credentials). I cannot do it — the second repo is
outside this session's access. No secrets are in the repo, so a mirror is safe.

Either way: **existing files and changes are preserved** (a branch push adds,
it does not delete), and **nothing is merged into `main`.**

## 4. Deployment branch

Created **`railway-deploy`** in `Nate8645er/Nate` from the Phase-22 head, with the
Railway config added. Point Railway at this branch (or at the main working
branch). `main` is untouched.

## 5. Railway deployment folder & files

The app lives in **`coinbase-bot/`** — in Railway, set **Root Directory =
`coinbase-bot`**. New files:

- `coinbase-bot/railway.json` — Nixpacks build, restart-on-failure.
- `coinbase-bot/nixpacks.toml` — install Python deps + `npm ci`, build frontend.
- `coinbase-bot/deploy/railway-start.sh` — starts uvicorn on `0.0.0.0:$PORT`.

**Railway environment variables (set in Railway, never in git):**
`HYPERGROK_SECRET_PASSPHRASE` (unlocks the encrypted key after a restart),
optional `HYPERGROK_PORTFOLIO_ID`.

**Attach a Railway Volume at `coinbase-bot/state`** — otherwise the encrypted
key, the loss ledger and the emergency stop reset on every redeploy.

## 6. Two honest warnings

**Cost — Railway is not really free for 24/7.** Railway removed its free tier in 2023. New accounts get a one-time trial credit, then it bills by usage; a bot
running around the clock will use up the credit and then **charge you**. You
said no paid services — so I **activated nothing** and created no Railway
resources. If you want genuinely free 24/7, the **GCP e2-micro** setup from
Phase 22 (or Oracle Always Free) is the better fit. Your call.

**Public exposure.** Railway publishes the app at a public HTTPS URL, so unlike
the Cloudflare-Tunnel setup there is **no e-mail gate** in front. The dashboard
is then protected only by its login (PBKDF2, lockout), CSRF, and the hard
trading locks (LIVE AUTONOMOUS locked, per-order approval, no key connected).
That is acceptable while live trading is locked, but weaker than Cloudflare
Access. If you stay on Railway, consider putting **Cloudflare Access** in front
of the Railway domain too, and keep live locked until you are satisfied.

## 7. Security / secrets

- No API key, private key or secret is in GitHub (scanned: only a fake test
  PEM). `state/` (encrypted key, ledgers, users, audit) is gitignored.
- The Coinbase key is never committed; it is entered via `/setup` over HTTPS and
  stored encrypted at rest, unlocked by the Railway env passphrase.

## 8. Test status

**172 Python tests pass.** No real order, no trading-permission change, no
auto-merge.

## Summary for you

- **Right repository:** `Nate8645er/Nate`
- **Right branch:** `claude/coinbase-ai-trading-bot-f6i4h3` (or `railway-deploy`)
- **Railway folder:** `coinbase-bot/` (Root Directory), config in
  `railway.json` + `nixpacks.toml` + `deploy/railway-start.sh`
- **Tests:** 172 pass
- **Blocked / your action:** connect Railway to `Nate8645er/Nate` **or** mirror
  to `Nate8645/Nate`; set the env vars + a volume; decide on the cost.
