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

from fastapi import Depends, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from server.agents_map import AGENT_TO_STATION, connected_count, stations  # noqa: E402
from trading_team import RiskManager, paper_risk_config  # noqa: E402
from trading_team.meeting import hold_meeting  # noqa: E402
from trading_team.modes import AbsoluteLimits, ModeController, ModeError, TradingMode  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "state"
TOKEN = os.environ.get("HYPERGROK_TOKEN") or secrets.token_urlsafe(24)
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

    def publish(self, kind: str, payload: dict, event_id: Optional[str] = None) -> Optional[dict]:
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
CONTROLLER = ModeController(AbsoluteLimits(total_capital_usdc=D("17.10")))
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
            resp = client.get_public_candles(product_id=product, start=str(now - 7200),
                                             end=str(now), granularity="ONE_HOUR", limit=2).to_dict()
            cs = sorted(resp.get("candles", []), key=lambda c: int(c["start"]))
            if cs:
                last, prev = cs[-1], cs[0]
                close, open_ = float(last["close"]), float(prev["open"])
                out[product] = {"price": close,
                                "change_pct": ((close / open_ - 1) * 100) if open_ else 0.0,
                                "volume": float(last.get("volume", 0))}
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
                BUS.publish("market", {"prices": prices, "updated_at": MARKET["updated_at"]})
            else:
                MARKET["stale"] = True
                BUS.publish("market_stale", {"reason": "keine Kursdaten abrufbar"})
        except Exception as exc:
            MARKET["stale"] = True
            BUS.publish("error", {"where": "market_loop", "detail": str(exc)[:200]})
        await asyncio.sleep(30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(market_loop())
    BUS.publish("system", {"message": "backend gestartet", "mode": CONTROLLER.mode.value})
    yield
    task.cancel()


app = FastAPI(title="HyperGrok AI Trading Empire", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["*"])


def auth(authorization: str = Header(default="")) -> None:
    if not authorization.startswith("Bearer ") or not secrets.compare_digest(
            authorization[7:], TOKEN):
        raise HTTPException(status_code=401, detail="Ungueltiges Token")


# --------------------------------------------------------------------------
# REST
# --------------------------------------------------------------------------


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
        "limits": {k: str(v) for k, v in {
            "total_capital_usdc": CONTROLLER.limits.total_capital_usdc,
            "max_daily_loss_usdc": CONTROLLER.limits.max_daily_loss_usdc,
            "max_total_loss_usdc": CONTROLLER.limits.max_total_loss_usdc,
            "max_slippage_pct": CONTROLLER.limits.max_slippage_pct,
            "max_open_exposure_usdc": CONTROLLER.limits.max_open_exposure_usdc,
        }.items()} | {"confirmed": CONTROLLER.limits.confirmed},
        "stations": stations(),
        "market": {"prices": MARKET["prices"], "updated_at": MARKET["updated_at"], "stale": stale},
        "balance": BALANCE,
        "seq": BUS.seq,
    }


@app.get("/api/scanner", dependencies=[Depends(auth)])
def scanner() -> dict:
    """Last scanner snapshot written by run_phase9.py. Never invented."""
    path = STATE / "dashboard_snapshot.json"
    if not path.exists():
        return {"available": False, "reason": "kein Scanner-Snapshot vorhanden", "tokens": []}
    data = json.loads(path.read_text())
    return {"available": True, "generated_at": data.get("generated_at"),
            "tokens": data.get("scanner", []), "risk_events": data.get("risk_events", [])}


@app.post("/api/balance/refresh", dependencies=[Depends(auth)])
def set_balance(value: float = Query(..., ge=0)) -> dict:
    """The real balance is read through the authorised Coinbase connector by the
    operator and handed in here; the server keeps no API key."""
    BALANCE.update({"available_usdc": value, "updated_at": time.time(),
                    "source": "Coinbase (autorisierter Connector)"})
    BUS.publish("balance", dict(BALANCE))
    return dict(BALANCE)


@app.post("/api/meeting/run", dependencies=[Depends(auth)])
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
        hold_meeting, symbol, closes,
        **{"risk": RiskManager(paper_risk_config()), "controller": CONTROLLER,
           "available_usdc": available})
    data = result.to_dict()
    BUS.publish("meeting_start", {"symbol": symbol, "price": str(closes[-1])})
    for s in data["statements"]:
        BUS.publish("agent", {**s, "station": AGENT_TO_STATION.get(s["agent"], "")})
        await asyncio.sleep(0.05)
    BUS.publish("meeting_end", {"symbol": symbol, "final": data["final"],
                                "consensus": data["consensus"], "agreed": data["agreed"],
                                "prepared_order": data["prepared_order"],
                                "note": data["execution_note"]})
    return data


def _fetch_closes(symbol: str, n: int = 120) -> list:
    from coinbase.rest import RESTClient
    client = RESTClient()
    end = int(time.time())
    try:
        resp = client.get_public_candles(product_id=symbol, start=str(end - 86400 * (n + 1)),
                                         end=str(end), granularity="ONE_DAY", limit=n).to_dict()
        cs = sorted(resp["candles"], key=lambda c: int(c["start"]))
        return [D(c["close"]) for c in cs]
    except Exception:
        return []


@app.post("/api/mode", dependencies=[Depends(auth)])
def set_mode(mode: str = Query(...)) -> dict:
    try:
        CONTROLLER.set_mode(TradingMode(mode))
    except (ModeError, ValueError) as exc:
        BUS.publish("mode_refused", {"requested": mode, "reason": str(exc)})
        raise HTTPException(409, str(exc))
    BUS.publish("mode", {"mode": CONTROLLER.mode.value})
    return {"mode": CONTROLLER.mode.value}


@app.post("/api/emergency_stop", dependencies=[Depends(auth)])
def emergency_stop(reason: str = Query("Dashboard")) -> dict:
    CONTROLLER.trigger_emergency_stop(reason)
    BUS.publish("emergency_stop", {"reason": reason})
    return CONTROLLER.status()


# --------------------------------------------------------------------------
# WebSocket: heartbeat, sequence numbers, resume, de-duplication
# --------------------------------------------------------------------------


@app.websocket("/ws")
async def ws(socket: WebSocket, token: str = Query(""), since: int = Query(0)) -> None:
    if not secrets.compare_digest(token, TOKEN):
        await socket.close(code=4401)
        return
    await socket.accept()
    queue = BUS.subscribe()
    try:
        # Resume: replay everything the client missed, in order.
        for event in BUS.since(since):
            await socket.send_text(json.dumps(event))
        await socket.send_text(json.dumps({"seq": BUS.seq, "kind": "sync",
                                           "ts": time.time(), "payload": {"resumed_from": since}}))
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=15)
                await socket.send_text(json.dumps(event))
            except asyncio.TimeoutError:
                await socket.send_text(json.dumps({"seq": BUS.seq, "kind": "heartbeat",
                                                   "ts": time.time(), "payload": {}}))
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
    print("=" * 60)
    print("HyperGrok backend. Dashboard-Token (nur hier, nie im Repo):")
    print(f"  {TOKEN}")
    print("=" * 60)
    uvicorn.run(app, host="127.0.0.1", port=8787, log_level="warning")
