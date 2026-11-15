# Phase 22 — Google Cloud deployment (e2-micro, iPhone-only)

Adapted the Phase 21 deployment for **Google Compute Engine** and your project
**hypergrok-ai-empire**. I cannot deploy it for you — that needs your Google
login in your project, and I create no billable resources — so this gives you
the artifacts plus exact iPhone steps. Status: **NOT DEPLOYED yet.**

## Free tier reality (verify on Google's page before you start)

- **e2-micro** is Always Free: **1 GB RAM**, 0.25 vCPU bursting to 2, **30 GB**
  standard persistent disk — **only** in `us-west1`, `us-central1`, or
  `us-east1`. One such VM per month, no external-IP charge on the free tier.
- **1 GB RAM is the real constraint.** A Node frontend build can run out of
  memory, so the startup script adds **2 GB swap** first and caps Node's heap.
  The backend service is memory-limited to 450 MB — enough for FastAPI +
  uvicorn; the 15 agents are functions in one process, not 15 processes.
- Egress free allowance is ~1 GB/month; a Cloudflare Tunnel uses very little.
- Does it suffice? **Yes** for this backend (paper + monitoring + dashboard).
  It is not sized for heavy load, but you are one user.

## What was built this phase

- `deploy/gcp/startup-script.sh` — a GCE **startup script** (idempotent, runs on
  every boot): creates swap, installs Python/Node/git, clones **PR #50** branch,
  installs deps, builds the frontend, writes the systemd service and enables it.
  Auto-start on boot, auto-restart on crash, `MemoryMax=450M`. Syntax-checked.
- Reuses everything from Phase 20/21: `/setup`, encrypted SecretStore, scheduler,
  monitor, emergency stop, audit, auth, dashboard. **No second engine.**
- **172 tests pass** (unchanged; nothing in the app logic changed this phase).

The backend binds to **127.0.0.1 only** — no GCP firewall port is opened. HTTPS
comes from **Cloudflare Tunnel**, so the trading API is never public.

## iPhone steps — Google Cloud Console in Safari

**1. Create the VM (free).**

- Safari -> `console.cloud.google.com` -> project **hypergrok-ai-empire**.
- Compute Engine -> VM instances -> **Create instance**.
- Name `hypergrok`, Region **us-central1** (or us-west1/us-east1), Series **E2**,
  Machine type **e2-micro**. Boot disk: Ubuntu 22.04 LTS, 30 GB **Standard**.
- Expand **Advanced -> Management -> Automation -> Startup script** and paste the
  full contents of `coinbase-bot/deploy/gcp/startup-script.sh`.
- (Private repo only) **Advanced -> Metadata**: add key `GITHUB_TOKEN` with a
  GitHub fine-grained **read-only** token. Never put the token in the script.
- Leave firewall HTTP/HTTPS **unchecked** (we stay private). Create.

**2. Wait ~3-5 min**, then open the VM's **SSH in browser** button and check:

```
systemctl status hypergrok      # active (running)
curl -s localhost:8787/api/health
```

**3. Cloudflare Tunnel + Access (your login).** In the SSH window:

```
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
sudo install cloudflared /usr/local/bin/ && cloudflared tunnel login
cloudflared tunnel create hypergrok
# route your hostname to http://127.0.0.1:8787 (see deploy/cloudflared-config.example.yml)
```

In Cloudflare **Zero Trust -> Access**: add an application for that hostname,
policy = **only your e-mail**. Then run the tunnel (`cloudflared tunnel run hypergrok`,
or install it as a service).

**4. Unlock passphrase (so the key survives reboots).** In SSH:

```
sudo systemctl edit hypergrok
# add:  [Service]
#       Environment=HYPERGROK_SECRET_PASSPHRASE=<deine-passphrase>
sudo systemctl restart hypergrok
```

**5. Import the Coinbase key — pure Safari.** Open
`https://<dein-hostname>/setup`, log in, paste the **new** CDP key from the Files
app, enter the same passphrase, tap save. It verifies read-only (view+trade,
**no transfer**, portfolio, USDC/BTC, orders, reconciliation) before storing it
encrypted.

## After deployment — tests I run for you

Once it is reachable, tell me and I will (read-only, no order): hit
`/api/readiness` for the 14 checks, `/api/key/status`, `/api/live` for the real
balance/positions/P&L, and confirm the dashboard shows real data with STALE/
UNAVAILABLE where appropriate.

## Blockers (need you)

- Create the VM + paste the startup script (your Google login).
- Cloudflare Tunnel + Access (your Cloudflare login).
- **Rotate the Coinbase key** first: View + Trade, **no transfer**, in the
  portfolio holding your 17.10 USDC. The old key is refused (transfer + empty
  portfolio) and was exposed in chat.

## Cost & safety

Cost **0** on the free tier if you stay on e2-micro in an eligible region and do
not add a paid upgrade. No real order, no withdrawal, no leverage, LIVE
AUTONOMOUS stays locked, no secret in GitHub/chat/logs, no merge.
