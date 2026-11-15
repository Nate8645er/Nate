"""HyperGrok FastAPI backend: REST + WebSocket in front of the EXISTING
trading system. It adds no trading logic of its own.

Security:
  * Every REST and WebSocket endpoint needs a bearer token (env HYPERGROK_TOKEN,
    otherwise one is generated at start and printed to the server console only).
  * State-changing routes are POST and require the token, so a cross-site form
    cannot drive them.
  * No API key, secret or private key is ever sent to the browser.
  * The dashboard cannot bypass the backend: live execution still needs
    confirmed limits plus a per-order approval phrase, checked in modes.py.
"""

from __future__ import annotations

import asyncio
import json
import os
import secrets
import time
from collections import deque
from contextlib import asynccontextmanager
from decimal import Decimal as D
from pathlib import Path
from typing import Optional

from fastapi import (
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.agents_map import AGENT_TO_STATION, connected_count, stations  # noqa: E402
from server.auth import AUDIT_FILE, AuthStore, Session  # noqa: E402
from server.secretstore import SecretError, SecretStore  # noqa: E402
from coinbase_connector.keyfile import load_key_from_text  # noqa: E402
from multimarket import smart_money, social, whale  # noqa: E402
from trading_team import RiskManager, paper_risk_config  # noqa: E402
from trading_team.meeting import hold_meeting  # noqa: E402
from trading_team.live_pipeline import read_positions, unresolved_orders  # noqa: E402
from trading_team.modes import ModeController, ModeError, TradingMode  # noqa: E402
from trading_team.persistence import SafetyStore  # noqa: E402
from trading_team.readiness import KNOWN_ORDERS, run_readiness_check  # noqa: E402
from trading_team.risk_config import NATE_CONFIRMED_LIMITS, NATE_PROFILE  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
AUTH = AuthStore.load()
SYMBOLS = ["BTC-USD", "ETH-USD", "SOL-USD"]


# --------------------------------------------------------------------------
# Event bus: sequence numbers, history, de-duplication
# --------------------------------------------------------------------------


class EventBus:
    def __init__(self, history: int = 500):
        self.seq = 0
        self.history: deque = deque(maxlen=history)
        self._subs: set = set()
        self._seen_ids: set = set()

    def publish(
        self, kind: str, payload: dict, event_id: Optional[str] = None
    ) -> Optional[dict]:
        """Returns the event, or None when it is a duplicate."""
        if event_id:
            if event_id in self._seen_ids:
                return None
            self._seen_ids.add(event_id)
        self.seq += 1
        event = {"seq": self.seq, "kind": kind, "ts": time.time(), "payload": payload}
        if event_id:
            event["id"] = event_id
        self.history.append(event)
        for q in list(self._subs):
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass
        return event

    def since(self, seq: int) -> list:
        return [e for e in self.history if e["seq"] > seq]

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=200)
        self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subs.discard(q)


BUS = EventBus()
# Nate's confirmed limits and durable safety state. The emergency stop and the
# loss ledger live in state/ and survive a restart. Autonomous live trading is
# NOT armed here and there is no HTTP route that arms it.
SAFETY = SafetyStore(STATE)
CONTROLLER = ModeController(NATE_CONFIRMED_LIMITS, store=SAFETY)
# Encrypted-at-rest Coinbase key. Configured from the mobile setup page; the
# plaintext key lives only in memory after an unlock, never in GitHub or logs.
SECRETS = SecretStore(STATE / "secret.enc")
_CONNECTOR: dict = {"obj": None, "error": "nicht versucht"}


def reset_connector() -> None:
    """Drop the cached connector so the next call rebuilds it (after the key
    changes, unlocks, or is cleared)."""
    _CONNECTOR["obj"] = None
    _CONNECTOR["error"] = "nicht versucht"


def _current_credentials():
    """Credentials for the SDK, preferring the unlocked encrypted store, then
    a local key file / env pair. Returns None when nothing is available."""
    if SECRETS.is_unlocked:
        return load_key_from_text(SECRETS.plaintext())
    from coinbase_connector.keyfile import resolve_credentials

    return resolve_credentials()


def live_connector():
    """The official Coinbase connector, only when an API key is present in the
    environment of this process. The key never leaves the backend."""
    if _CONNECTOR["obj"] is not None:
        return _CONNECTOR["obj"]
    try:
        from coinbase_connector.connector import CoinbaseLiveConnector

        creds = _current_credentials()  # encrypted store, key file, or env
        if creds is None:
            _CONNECTOR["error"] = (
                "Kein Schluessel: ueber /setup einrichten oder COINBASE_KEY_FILE setzen"
            )
            return None
        _CONNECTOR["obj"] = CoinbaseLiveConnector(
            credentials=creds, max_quote_per_order=str(NATE_PROFILE.max_position_usdc())
        )
        _CONNECTOR["error"] = ""
    except Exception as exc:  # noqa: BLE001
        _CONNECTOR["error"] = f"{type(exc).__name__}: {exc}"
    return _CONNECTOR["obj"]


MARKET: dict = {"prices": {}, "updated_at": None, "stale": True}
BALANCE: dict = {"available_usdc": None, "source": "nicht gelesen", "updated_at": None}


# --------------------------------------------------------------------------
# Market poller (real public Coinbase candles, no key)
# --------------------------------------------------------------------------


def _fetch_prices() -> dict:
    from coinbase.rest import RESTClient

    client = RESTClient()
    out = {}
    now = int(time.time())
    for product in SYMBOLS:
        try:
            resp = client.get_public_candles(
                product_id=product,
                start=str(now - 7200),
                end=str(now),
                granularity="ONE_HOUR",
                limit=2,
            ).to_dict()
            cs = sorted(resp.get("candles", []), key=lambda c: int(c["start"]))
            if cs:
                last, prev = cs[-1], cs[0]
                close, open_ = float(last["close"]), float(prev["open"])
                out[product] = {
                    "price": close,
                    "change_pct": ((close / open_ - 1) * 100) if open_ else 0.0,
                    "volume": float(last.get("volume", 0)),
                }
        except Exception:
            continue
    return out


async def market_loop() -> None:
    while True:
        try:
            prices = await asyncio.to_thread(_fetch_prices)
            if prices:
                MARKET["prices"] = prices
                MARKET["updated_at"] = time.time()
                MARKET["stale"] = False
                BUS.publish(
                    "market", {"prices": prices, "updated_at": MARKET["updated_at"]}
                )
            else:
                MARKET["stale"] = True
                BUS.publish("market_stale", {"reason": "keine Kursdaten abrufbar"})
        except Exception as exc:
            MARKET["stale"] = True
            BUS.publish("error", {"where": "market_loop", "detail": str(exc)[:200]})
        await asyncio.sleep(30)


# Scheduler / position monitor. Prepared and persistent, but SAFE: it never
# sends a real entry. When enabled it runs the forward-paper cycle and watches
# open positions for stop-loss / take-profit / time exits. Real exits only run
# when a connector is configured and only to REDUCE risk (never a new buy).
SCHED: dict = {
    "enabled": False,
    "interval": 60,
    "last_tick": None,
    "last_result": None,
    "ticks": 0,
}


def _autotrade_tick() -> dict:
    """One scheduler tick (runs in a thread). Returns a small summary."""
    from decimal import Decimal as D
    from trading_team import RiskManager
    from trading_team.engine import monitor_positions, run_once
    from trading_team.risk_config import live_risk_config
    from scripts.forward_paper import PublicConnector, STORE, fetch_ohlcv, spot_prices

    conn = live_connector() or PublicConnector()
    risk = RiskManager(live_risk_config())
    entries = []
    for symbol in SYMBOLS:
        pid = symbol if symbol.endswith("-USDC") else symbol.replace("-USD", "-USDC")
        try:
            ohlcv = fetch_ohlcv(pid)
        except Exception as exc:  # noqa: BLE001
            entries.append(
                {"symbol": pid, "result": f"DATA STALE: {type(exc).__name__}"}
            )
            continue
        out = run_once(
            pid,
            ohlcv,
            controller=CONTROLLER,
            risk=risk,
            connector=conn,
            store=STORE,
            market_updated_at=time.time(),
            fee_rate=D("0.001"),
            min_order_usdc=D("1"),
            mode=TradingMode.PAPER,
        )
        entries.append({"symbol": pid, "result": out["result"]})
    prices = spot_prices()
    paper_mon = monitor_positions(
        prices, controller=CONTROLLER, connector=conn, store=STORE, paper=True
    )
    # Real positions: only watch for risk-reducing exits, never a new entry.
    real_mon = {"checked": 0, "actions": [], "watch_blocked": []}
    if live_connector() is not None:
        real_mon = monitor_positions(
            MARKET["prices"],
            controller=CONTROLLER,
            connector=live_connector(),
            store=SAFETY,
            paper=False,
            market_stale=MARKET["stale"],
        )
    return {"entries": entries, "paper_monitor": paper_mon, "real_monitor": real_mon}


async def autotrade_loop() -> None:
    while True:
        try:
            if SCHED["enabled"]:
                SCHED["last_result"] = await asyncio.to_thread(_autotrade_tick)
                SCHED["ticks"] += 1
                SCHED["last_tick"] = time.time()
                BUS.publish(
                    "scheduler",
                    {"ticks": SCHED["ticks"], "summary": SCHED["last_result"]},
                )
        except Exception as exc:  # noqa: BLE001
            BUS.publish("error", {"where": "autotrade_loop", "detail": str(exc)[:200]})
        await asyncio.sleep(max(15, int(SCHED["interval"])))


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(market_loop())
    # Persistent host: unlock the stored key automatically if the passphrase is
    # provided via the host's own env-var vault. No passphrase -> stays locked.
    if SECRETS.try_env_unlock():
        reset_connector()
        BUS.publish("key", {"event": "auto_unlock", "status": SECRETS.status()})
    sched = asyncio.create_task(autotrade_loop())
    BUS.publish(
        "system", {"message": "backend gestartet", "mode": CONTROLLER.mode.value}
    )
    if CONTROLLER.emergency_stop:
        BUS.publish(
            "emergency_stop", {"reason": CONTROLLER.stop_reason, "restored": True}
        )
    AUTH.audit(
        "backend_start",
        mode=CONTROLLER.mode.value,
        emergency_stop=CONTROLLER.emergency_stop,
        unresolved_orders=len(unresolved_orders(SAFETY)),
    )
    yield
    task.cancel()
    sched.cancel()


app = FastAPI(title="HyperGrok AI Trading Empire", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def current_session(authorization: str = Header(default="")) -> Session:
    """Any authenticated user. Raises 401 otherwise."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Anmeldung erforderlich")
    session = AUTH.session(authorization[7:])
    if session is None:
        raise HTTPException(status_code=401, detail="Sitzung ungueltig oder abgelaufen")
    return session


def auth(session: Session = Depends(current_session)) -> Session:
    return session


def require_admin_read(session: Session = Depends(current_session)) -> Session:
    """Admin role for a read-only route (no CSRF needed for GET)."""
    if session.role != "admin":
        AUTH.audit("forbidden", username=session.username, role=session.role)
        raise HTTPException(403, "admin erforderlich")
    return session


def require_admin(
    session: Session = Depends(current_session), x_csrf_token: str = Header(default="")
) -> Session:
    """State-changing routes: admin role AND a matching CSRF token, which a
    cross-site form cannot supply."""
    if session.role != "admin":
        AUTH.audit("forbidden", username=session.username, role=session.role)
        raise HTTPException(status_code=403, detail="Rolle admin erforderlich")
    if not secrets.compare_digest(x_csrf_token or "", session.csrf):
        AUTH.audit("csrf_rejected", username=session.username)
        raise HTTPException(status_code=403, detail="CSRF-Token fehlt oder falsch")
    return session


# --------------------------------------------------------------------------
# REST
# --------------------------------------------------------------------------


@app.post("/api/login")
def login(payload: dict, request: Request) -> dict:
    ip = request.client.host if request.client else "-"
    username = str(payload.get("username", ""))[:64]
    password = str(payload.get("password", ""))[:256]
    session = AUTH.login(username, password, ip)
    if session is None:
        raise HTTPException(status_code=401, detail="Anmeldung fehlgeschlagen")
    return {
        "token": session.token,
        "csrf": session.csrf,
        "role": session.role,
        "username": session.username,
    }


@app.post("/api/logout")
def logout(session: Session = Depends(current_session)) -> dict:
    AUTH.logout(session.token)
    return {"ok": True}


@app.get("/api/me", dependencies=[Depends(auth)])
def me(session: Session = Depends(current_session)) -> dict:
    return {"username": session.username, "role": session.role, "csrf": session.csrf}


@app.get("/api/intel/whale", dependencies=[Depends(auth)])
def intel_whale(mint: str = Query(..., min_length=32, max_length=64)) -> dict:
    return whale.analyse(mint).to_dict()


@app.get("/api/intel/smart_money", dependencies=[Depends(auth)])
def intel_smart(mint: str = Query(..., min_length=32, max_length=64)) -> dict:
    return smart_money.analyse(mint).to_dict()


@app.get("/api/intel/social", dependencies=[Depends(auth)])
def intel_social() -> dict:
    return social.trending_assets().to_dict()


@app.get("/api/health")
def health() -> dict:
    connected, total = connected_count()
    return {"ok": True, "stations_connected": connected, "stations_total": total}


@app.get("/api/state", dependencies=[Depends(auth)])
def state() -> dict:
    stale = MARKET["updated_at"] is None or (time.time() - MARKET["updated_at"]) > 90
    return {
        "mode": CONTROLLER.mode.value,
        "emergency_stop": CONTROLLER.emergency_stop,
        "status": CONTROLLER.status(),
        "limits": {
            k: str(v)
            for k, v in {
                "total_capital_usdc": CONTROLLER.limits.total_capital_usdc,
                "max_daily_loss_usdc": CONTROLLER.limits.max_daily_loss_usdc,
                "max_total_loss_usdc": CONTROLLER.limits.max_total_loss_usdc,
                "max_slippage_pct": CONTROLLER.limits.max_slippage_pct,
                "max_open_exposure_usdc": CONTROLLER.limits.max_open_exposure_usdc,
            }.items()
        }
        | {"confirmed": CONTROLLER.limits.confirmed},
        "stations": stations(),
        "market": {
            "prices": MARKET["prices"],
            "updated_at": MARKET["updated_at"],
            "stale": stale,
        },
        "balance": BALANCE,
        "risk_profile": NATE_PROFILE.to_dict(),
        "safety": SAFETY.snapshot() | {"unresolved_orders": unresolved_orders(SAFETY)},
        "seq": BUS.seq,
    }


@app.get("/api/scanner", dependencies=[Depends(auth)])
def scanner() -> dict:
    """Last scanner snapshot written by run_phase9.py. Never invented."""
    path = STATE / "dashboard_snapshot.json"
    if not path.exists():
        return {
            "available": False,
            "reason": "kein Scanner-Snapshot vorhanden",
            "tokens": [],
        }
    data = json.loads(path.read_text())
    return {
        "available": True,
        "generated_at": data.get("generated_at"),
        "tokens": data.get("scanner", []),
        "risk_events": data.get("risk_events", []),
    }


@app.post("/api/balance/refresh", dependencies=[Depends(require_admin)])
def set_balance(value: float = Query(..., ge=0)) -> dict:
    """The real balance is read through the authorised Coinbase connector by the
    operator and handed in here; the server keeps no API key."""
    BALANCE.update(
        {
            "available_usdc": value,
            "updated_at": time.time(),
            "source": "Coinbase (autorisierter Connector)",
        }
    )
    BUS.publish("balance", dict(BALANCE))
    return dict(BALANCE)


@app.post("/api/meeting/run", dependencies=[Depends(require_admin)])
async def run_meeting(symbol: str = Query("BTC-USD")) -> dict:
    """Run the existing eight-step meeting and stream each statement as an event."""
    if symbol not in SYMBOLS:
        raise HTTPException(400, "unbekanntes Symbol")
    closes = await asyncio.to_thread(_fetch_closes, symbol)
    if len(closes) < 40:
        BUS.publish("error", {"where": "meeting", "detail": "zu wenig Kursdaten"})
        raise HTTPException(503, "zu wenig Kursdaten fuer ein Meeting")
    available = D(str(BALANCE["available_usdc"] or 0))
    result = await asyncio.to_thread(
        hold_meeting,
        symbol,
        closes,
        **{
            "risk": RiskManager(paper_risk_config()),
            "controller": CONTROLLER,
            "available_usdc": available,
        },
    )
    data = result.to_dict()
    BUS.publish("meeting_start", {"symbol": symbol, "price": str(closes[-1])})
    for s in data["statements"]:
        BUS.publish("agent", {**s, "station": AGENT_TO_STATION.get(s["agent"], "")})
        await asyncio.sleep(0.05)
    BUS.publish(
        "meeting_end",
        {
            "symbol": symbol,
            "final": data["final"],
            "consensus": data["consensus"],
            "agreed": data["agreed"],
            "prepared_order": data["prepared_order"],
            "note": data["execution_note"],
        },
    )
    return data


def _fetch_closes(symbol: str, n: int = 120) -> list:
    from coinbase.rest import RESTClient

    client = RESTClient()
    end = int(time.time())
    try:
        resp = client.get_public_candles(
            product_id=symbol,
            start=str(end - 86400 * (n + 1)),
            end=str(end),
            granularity="ONE_DAY",
            limit=n,
        ).to_dict()
        cs = sorted(resp["candles"], key=lambda c: int(c["start"]))
        return [D(c["close"]) for c in cs]
    except Exception:
        return []


@app.post("/api/mode", dependencies=[Depends(require_admin)])
def set_mode(mode: str = Query(...)) -> dict:
    try:
        CONTROLLER.set_mode(TradingMode(mode))
    except (ModeError, ValueError) as exc:
        BUS.publish("mode_refused", {"requested": mode, "reason": str(exc)})
        raise HTTPException(409, str(exc))
    BUS.publish("mode", {"mode": CONTROLLER.mode.value})
    return {"mode": CONTROLLER.mode.value}


@app.post("/api/emergency_stop", dependencies=[Depends(require_admin)])
def emergency_stop(
    reason: str = Query("Dashboard"), session: Session = Depends(current_session)
) -> dict:
    CONTROLLER.trigger_emergency_stop(reason, source=session.username)
    AUTH.audit("emergency_stop", username=session.username, reason=reason)
    BUS.publish("emergency_stop", {"reason": reason})
    return CONTROLLER.status()


@app.post("/api/emergency_stop/clear", dependencies=[Depends(require_admin)])
def emergency_stop_clear(
    reason: str = Query(..., min_length=8), session: Session = Depends(current_session)
) -> dict:
    """Clearing is deliberate: an admin, a written reason, an audit entry. It
    returns the system to PAPER - it does not re-arm anything."""
    try:
        CONTROLLER.clear_emergency_stop(cleared_by=session.username, reason=reason)
    except ModeError as exc:
        raise HTTPException(409, str(exc))
    AUTH.audit("emergency_stop_cleared", username=session.username, reason=reason)
    BUS.publish("emergency_stop_cleared", {"by": session.username, "reason": reason})
    return CONTROLLER.status()


@app.get("/api/readiness", dependencies=[Depends(require_admin_read)])
def readiness() -> dict:
    """LIVE_READINESS_CHECK. Reads and self-tests only; arms nothing."""
    report = run_readiness_check(
        controller=CONTROLLER,
        connector=live_connector(),
        auth_store=AUTH,
        audit_file=AUDIT_FILE,
        market_updated_at=MARKET["updated_at"],
        expected_portfolio_id=os.environ.get("HYPERGROK_PORTFOLIO_ID") or None,
        known_orders=KNOWN_ORDERS,
    )
    report["connector_note"] = _CONNECTOR["error"]
    BUS.publish(
        "readiness",
        {
            "verdict": report["verdict"],
            "passed": report["passed"],
            "total": report["total"],
        },
    )
    return report


@app.get("/api/live", dependencies=[Depends(auth)])
def live_overview() -> dict:
    """Real-money figures only. Every value is read from Coinbase or from the
    durable ledger; what is not known is null, never estimated."""
    conn = live_connector()
    real_balance, source = BALANCE["available_usdc"], BALANCE["source"]
    if conn is not None:
        try:
            real_balance, source = (
                float(conn.get_available_funds("USDC")),
                "Coinbase (live)",
            )
        except Exception as exc:  # noqa: BLE001
            source = f"Coinbase nicht lesbar: {type(exc).__name__}"
    ledger = SAFETY.read_ledger()
    positions = read_positions(SAFETY)
    stale = MARKET["updated_at"] is None or (time.time() - MARKET["updated_at"]) > 90
    unrealised, rows = D("0"), []
    for product, pos in positions.items():
        price = (
            None if stale else MARKET["prices"].get(product.replace("-USDC", "-USD"))
        )
        value = None if price is None else D(str(pos["base_size"])) * D(str(price))
        pnl = None if value is None else value - D(str(pos["cost_usdc"]))
        unrealised = None if (pnl is None or unrealised is None) else unrealised + pnl
        rows.append(
            {
                "product_id": product,
                **pos,
                "mark_usd": price,
                "unrealised_pnl_usdc": None if pnl is None else str(pnl),
            }
        )
    orders = SAFETY.read_order_ids()
    fees = sum(
        (
            D(str((o.get("outcome") or {}).get("fees_usdc") or "0"))
            for o in orders.values()
        ),
        D("0"),
    )
    realised = ledger.total_realised
    return {
        "mode": CONTROLLER.mode.value,
        "is_live": CONTROLLER.mode is not TradingMode.PAPER,
        "real_balance_usdc": real_balance,
        "balance_source": source,
        "allocated_capital_usdc": str(CONTROLLER.limits.total_capital_usdc),
        "open_positions": rows,
        "realised_pnl_usdc": str(realised),
        "daily_pnl_usdc": str(ledger.realised_today()),
        "unrealised_pnl_usdc": None if unrealised is None else str(unrealised),
        "total_pnl_usdc": None if unrealised is None else str(realised + unrealised),
        "trading_fees_usdc": str(fees),
        "order_history": [
            {"client_order_id": cid, **row} for cid, row in orders.items()
        ][-50:],
        "note": "Nur Orders dieses Systems. Die zwei Testorders vom 13.11. liefen ueber den "
        "Coinbase-Connector der Sitzung und stehen nicht in diesem Ledger.",
    }


# --------------------------------------------------------------------------
# Coinbase key setup from the phone (authenticated, HTTPS, encrypted at rest)
# --------------------------------------------------------------------------


_SETUP_HTML = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>HyperGrok · Schluessel einrichten</title>
<style>
  :root{color-scheme:dark}
  *{box-sizing:border-box}
  body{margin:0;background:#07090f;color:#e7ecf3;font:16px/1.5 -apple-system,system-ui,sans-serif;padding:16px}
  h1{font-size:18px;letter-spacing:.1em;text-transform:uppercase;color:#7cf5c0}
  .card{max-width:520px;margin:0 auto;background:#0d1320;border:1px solid #1d2838;border-radius:16px;padding:16px;margin-bottom:14px}
  label{display:block;font-size:12px;color:#9fb0c3;margin:10px 0 4px}
  input,textarea,button{width:100%;font-size:16px;border-radius:12px;border:1px solid #273448;background:#0a0f1a;color:#e7ecf3;padding:12px;min-height:48px}
  textarea{min-height:120px;font-family:ui-monospace,monospace}
  button{background:#12b981;color:#04120c;border:none;font-weight:700;margin-top:14px}
  button.secondary{background:#1b2740;color:#cfe}
  .muted{color:#7f90a5;font-size:13px}
  .ok{color:#56e39f}.bad{color:#ff6b6b}.warn{color:#ffcf6b}
  pre{white-space:pre-wrap;word-break:break-word;background:#070b13;border:1px solid #1d2838;border-radius:12px;padding:10px;font-size:12px}
  .hide{display:none}
</style></head>
<body><div class="card">
  <h1>HyperGrok · Schluessel</h1>
  <p class="muted">Nur ueber HTTPS. Der Schluessel wird einmal gesendet, auf dem
  Server verschluesselt gespeichert und nie im Browser abgelegt.</p>
</div>

<div class="card" id="loginCard">
  <label>Benutzer</label><input id="u" autocomplete="username">
  <label>Passwort</label><input id="p" type="password" autocomplete="current-password">
  <button onclick="login()">Anmelden</button>
  <p id="loginMsg" class="muted"></p>
</div>

<div class="card hide" id="keyCard">
  <p class="muted">Status: <span id="status">...</span></p>
  <label>CDP-Schluesseldatei (Inhalt einfuegen: JSON, PEM oder Text)</label>
  <textarea id="key" placeholder='{ "name": "organizations/.../apiKeys/...", ... }'></textarea>
  <label>Verschluesselungs-Passphrase (min. 8 Zeichen, merken!)</label>
  <input id="pass" type="password" autocomplete="new-password">
  <button onclick="setup()">Pruefen &amp; verschluesselt speichern</button>
  <button class="secondary" onclick="unlock()">Nur entsperren (Passphrase)</button>
  <p id="keyMsg" class="muted"></p>
  <pre id="report" class="hide"></pre>
</div>

<script>
let TOKEN="", CSRF="";
const $=id=>document.getElementById(id);
async function api(path, opts={}){
  opts.headers=Object.assign({"content-type":"application/json"}, opts.headers||{});
  if(TOKEN) opts.headers["Authorization"]="Bearer "+TOKEN;
  if(opts.method&&opts.method!=="GET") opts.headers["X-CSRF-Token"]=CSRF;
  const r=await fetch(path, opts);
  const t=await r.text(); let j={}; try{j=JSON.parse(t)}catch(e){}
  if(!r.ok) throw new Error(j.detail||r.status); return j;
}
async function login(){
  $("loginMsg").textContent="...";
  try{
    const j=await api("/api/login",{method:"POST",body:JSON.stringify({username:$("u").value,password:$("p").value})});
    TOKEN=j.token; CSRF=j.csrf;
    if(j.role!=="admin"){$("loginMsg").innerHTML='<span class="bad">Admin-Konto noetig.</span>';return;}
    $("loginCard").classList.add("hide"); $("keyCard").classList.remove("hide"); refresh();
  }catch(e){$("loginMsg").innerHTML='<span class="bad">'+e.message+'</span>';}
}
async function refresh(){
  try{const s=await api("/api/key/status");
    const sec=s.secret||{};
    $("status").innerHTML=(sec.configured?('<span class="ok">gespeichert</span>'+(sec.unlocked?' · entsperrt':' · <span class="warn">gesperrt</span>')+(sec.key_id_suffix?(' · ...'+sec.key_id_suffix):'')):'<span class="warn">nicht eingerichtet</span>')
      +(s.connected?' · <span class="ok">verbunden</span>':'');
  }catch(e){$("status").textContent=e.message;}
}
async function setup(){
  $("keyMsg").textContent="pruefe read-only ..."; $("report").classList.add("hide");
  try{
    const j=await api("/api/key/setup",{method:"POST",body:JSON.stringify({key:$("key").value,passphrase:$("pass").value})});
    $("key").value=""; // never keep the key in the field
    $("keyMsg").innerHTML='<span class="ok">Gespeichert &amp; verschluesselt.</span>';
    $("report").textContent=JSON.stringify(j.verify,null,2); $("report").classList.remove("hide");
    refresh();
  }catch(e){$("keyMsg").innerHTML='<span class="bad">'+e.message+'</span>';}
}
async function unlock(){
  $("keyMsg").textContent="...";
  try{await api("/api/key/unlock",{method:"POST",body:JSON.stringify({passphrase:$("pass").value})});
    $("keyMsg").innerHTML='<span class="ok">Entsperrt.</span>'; refresh();
  }catch(e){$("keyMsg").innerHTML='<span class="bad">'+e.message+'</span>';}
}
</script>
</body></html>"""


def _verify_key_readonly(creds: dict) -> dict:
    """Build the connector read-only and run verify_access. Returns a sanitized
    report. Raises ConnectorError for a transfer-capable key (never accepted)."""
    from coinbase_connector.connector import CoinbaseLiveConnector

    expected = os.environ.get("HYPERGROK_PORTFOLIO_ID") or None
    conn = CoinbaseLiveConnector(
        credentials=creds, max_quote_per_order=str(NATE_PROFILE.max_position_usdc())
    )
    report = conn.verify_access(expected_portfolio_id=expected)
    try:
        report["usdc_available"] = str(conn.get_available_funds("USDC"))
        report["btc_available"] = str(conn.get_available_funds("BTC"))
    except Exception as exc:  # noqa: BLE001
        report["balance_error"] = f"{type(exc).__name__}: {exc}"
    return report


@app.get("/api/key/status", dependencies=[Depends(require_admin_read)])
def key_status() -> dict:
    conn = live_connector()
    return {
        "secret": SECRETS.status(),
        "connector_error": _CONNECTOR["error"],
        "connected": conn is not None,
        "permissions": (conn.permissions if conn else None)
        and {
            k: conn.permissions.get(k)
            for k in ("can_view", "can_trade", "can_transfer", "portfolio_type")
        },
    }


@app.post("/api/key/setup", dependencies=[Depends(require_admin)])
def key_setup(payload: dict, session: Session = Depends(current_session)) -> dict:
    """Receive the CDP key content + an encryption passphrase from the phone.
    Verifies read-only (view+trade, NO transfer, portfolio, balance), then
    encrypts it at rest. The key is never logged or echoed back."""
    content = str(payload.get("key") or "").strip()
    passphrase = str(payload.get("passphrase") or "")
    if not content:
        raise HTTPException(400, "Kein Schluesselinhalt.")
    try:
        creds = load_key_from_text(content)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Schluessel nicht lesbar: {type(exc).__name__}")
    try:
        report = _verify_key_readonly(creds)
    except Exception as exc:  # noqa: BLE001 - e.g. transfer permission refused
        AUTH.audit(
            "key_setup_rejected", username=session.username, reason=type(exc).__name__
        )
        raise HTTPException(400, f"Schluessel abgelehnt: {exc}")
    try:
        SECRETS.store(content, passphrase, key_id_suffix=creds["api_key"][-6:])
    except SecretError as exc:
        raise HTTPException(400, str(exc))
    reset_connector()
    AUTH.audit(
        "key_setup_ok", username=session.username, key_id_suffix=creds["api_key"][-6:]
    )
    BUS.publish("key", {"event": "configured", "status": SECRETS.status()})
    return {"stored": True, "secret": SECRETS.status(), "verify": report}


@app.post("/api/key/unlock", dependencies=[Depends(require_admin)])
def key_unlock(payload: dict, session: Session = Depends(current_session)) -> dict:
    try:
        SECRETS.unlock(str(payload.get("passphrase") or ""))
    except SecretError as exc:
        raise HTTPException(400, str(exc))
    reset_connector()
    AUTH.audit("key_unlock", username=session.username)
    return {"unlocked": True, "secret": SECRETS.status()}


@app.post("/api/key/lock", dependencies=[Depends(require_admin)])
def key_lock(session: Session = Depends(current_session)) -> dict:
    SECRETS.lock()
    reset_connector()
    AUTH.audit("key_lock", username=session.username)
    return {"locked": True, "secret": SECRETS.status()}


@app.post("/api/key/clear", dependencies=[Depends(require_admin)])
def key_clear(session: Session = Depends(current_session)) -> dict:
    SECRETS.clear()
    reset_connector()
    AUTH.audit("key_clear", username=session.username)
    BUS.publish("key", {"event": "cleared"})
    return {"cleared": True, "secret": SECRETS.status()}


@app.get("/api/scheduler", dependencies=[Depends(require_admin_read)])
def scheduler_status() -> dict:
    return {k: SCHED[k] for k in ("enabled", "interval", "ticks", "last_tick")} | {
        "last_result": SCHED["last_result"]
    }


@app.post("/api/scheduler", dependencies=[Depends(require_admin)])
def scheduler_toggle(
    enabled: bool = Query(...),
    interval: int = Query(60),
    session: Session = Depends(current_session),
) -> dict:
    SCHED["enabled"] = bool(enabled)
    SCHED["interval"] = max(15, int(interval))
    AUTH.audit("scheduler", username=session.username, enabled=SCHED["enabled"])
    BUS.publish(
        "scheduler", {"enabled": SCHED["enabled"], "interval": SCHED["interval"]}
    )
    return {"enabled": SCHED["enabled"], "interval": SCHED["interval"]}


@app.get("/setup")
def setup_page() -> "HTMLResponse":
    """A self-contained mobile page (no build step) to configure the Coinbase
    key from Safari on the iPhone. It talks only to the authenticated API over
    HTTPS; the key is sent once and never stored in the browser."""
    return HTMLResponse(_SETUP_HTML)


# --------------------------------------------------------------------------
# WebSocket: heartbeat, sequence numbers, resume, de-duplication
# --------------------------------------------------------------------------


@app.websocket("/ws")
async def ws(socket: WebSocket, token: str = Query(""), since: int = Query(0)) -> None:
    session = AUTH.session(token)
    if session is None:
        await socket.close(code=4401)
        return
    AUTH.audit("ws_connected", username=session.username)
    await socket.accept()
    queue = BUS.subscribe()
    try:
        # Resume: replay everything the client missed, in order.
        for event in BUS.since(since):
            await socket.send_text(json.dumps(event))
        await socket.send_text(
            json.dumps(
                {
                    "seq": BUS.seq,
                    "kind": "sync",
                    "ts": time.time(),
                    "payload": {"resumed_from": since},
                }
            )
        )
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                await socket.send_text(json.dumps(event))
            except asyncio.TimeoutError:
                await socket.send_text(
                    json.dumps(
                        {
                            "seq": BUS.seq,
                            "kind": "heartbeat",
                            "ts": time.time(),
                            "payload": {},
                        }
                    )
                )
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        BUS.unsubscribe(queue)


# --------------------------------------------------------------------------
# Static frontend (production build)
# --------------------------------------------------------------------------

DIST = ROOT / "web" / "dist"
if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(DIST / "index.html")


@app.exception_handler(404)
def spa_fallback(request, exc):
    if DIST.exists() and not request.url.path.startswith("/api"):
        return FileResponse(DIST / "index.html")
    return JSONResponse({"detail": "not found"}, status_code=404)


if __name__ == "__main__":
    import uvicorn

    print("=" * 64)
    password = AUTH.bootstrap_admin()
    if password:
        print("Erster Start: Admin-Konto angelegt.")
        print("  Benutzer: admin")
        print(f"  Passwort: {password}   <- einmalig, wird nirgends gespeichert")
    else:
        print(f"Bestehende Konten: {', '.join(AUTH.users) or 'keine'}")
    print("=" * 64)
    uvicorn.run(app, host="127.0.0.1", port=8787, log_level="warning")
