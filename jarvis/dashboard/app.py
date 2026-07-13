"""Live-Dashboard: FastAPI-Server mit Live-Ticker-Oberfläche.

Endpunkte:
  GET  /               Dashboard (HTML, Live-Ticker via Polling)
  GET  /api/state      kompletter Systemzustand (Agenten, Aufgaben, CPU/RAM, Logs)
  GET  /api/employee/{address}   Identität eines beliebigen der 100 Mrd. Mitarbeiter
  GET  /api/org/{address}        Auszug aus dessen virtuellem Unternehmen
  GET  /api/business   Business-Kennzahlen — NUR echte Daten, keine Simulation als real
  POST /api/task       Aufgabe einreihen: {"beschreibung": "...", "adresse": optional}
"""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis.core.identity import materialize, validate_address
from jarvis.core.orchestrator import Orchestrator

DATA_DIR = Path(os.environ.get("JARVIS_DATA", Path.home() / ".jarvis"))
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="JARVIS HyperScale", version="0.1.0")
orchestrator = Orchestrator(DATA_DIR)


class TaskIn(BaseModel):
    beschreibung: str
    adresse: str | None = None


def _load_persisted_key() -> None:
    """Lädt einen über den Fable-5-Button gespeicherten API-Key (lokale Datei)."""
    import json
    cfg = DATA_DIR / "config.json"
    if cfg.exists() and not os.environ.get("ANTHROPIC_API_KEY"):
        try:
            key = json.loads(cfg.read_text()).get("anthropic_api_key", "")
            if key:
                os.environ["ANTHROPIC_API_KEY"] = key
        except Exception:
            pass


@app.on_event("startup")
async def _startup() -> None:
    _load_persisted_key()
    await orchestrator.start()
    if os.environ.get("JARVIS_DEMO") == "1":
        import asyncio
        asyncio.create_task(_demo_loop())


async def _demo_loop() -> None:
    """Erzeugt fortlaufend klar markierte Demo-Aufgaben, damit der Ticker lebt."""
    import asyncio
    import random
    samples = [
        "!plugin system info",
        "!plugin clock now",
        "!plugin calc eval expression=(17*3)+8",
        "!plugin files write path=notiz.txt content=JARVIS-Demo",
        "!plugin files list",
        "!plugin aufgaben list",
        "!plugin finanzen summe",
        "Erstelle eine Kurzzusammenfassung des Projektstatus",
        "Prüfe die Aufgabenliste des Qualitätsmanagement-Teams",
        "Recherche: aktuelle Best Practices für Plugin-Architekturen",
    ]
    orchestrator.log("info", "Demo-Modus aktiv: markierte Beispiel-Aufgaben laufen")
    while True:
        orchestrator.submit(random.choice(samples), is_demo=True)
        await asyncio.sleep(2.5)


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
async def start_page() -> FileResponse:
    return FileResponse(STATIC / "start.html")


@app.get("/uebersicht")
async def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


@app.get("/gehirn")
async def gehirn_page() -> FileResponse:
    return FileResponse(STATIC / "gehirn.html")


@app.get("/mitarbeiter")
async def mitarbeiter_page() -> FileResponse:
    return FileResponse(STATIC / "mitarbeiter.html")


@app.get("/werkzeuge")
async def werkzeuge_page() -> FileResponse:
    return FileResponse(STATIC / "werkzeuge.html")


@app.get("/api/memory")
async def memory(limit: int = 25) -> JSONResponse:
    import time as _t
    rows = orchestrator.memory.recent(max(1, min(limit, 100)))
    return JSONResponse({"eintraege": [
        {"adresse": a, "zeit": _t.strftime("%H:%M:%S", _t.localtime(ts)),
         "aufgabe": task, "ergebnis": result}
        for a, ts, task, result in rows]})


@app.get("/api/state")
async def state() -> JSONResponse:
    return JSONResponse(orchestrator.state())


@app.get("/api/employee/{address:path}")
async def employee(address: str) -> JSONResponse:
    try:
        e = materialize(address)
    except ValueError as err:
        raise HTTPException(400, str(err)) from err
    return JSONResponse({
        "adresse": e.address, "name": e.name, "team": e.team, "rolle": e.role,
        "spezialisierung": e.specialization, "skills": list(e.skills),
        "ziele": list(e.goals), "prioritaet": e.priority,
        "eigenes_unternehmen": e.company, "ebene": e.depth,
        "adressierbare_mitarbeiter_im_eigenen_unternehmen": e.sub_employees,
        "plugins_autorisiert": orchestrator.plugins.for_team(e.team),
    })


@app.get("/api/org/{address:path}")
async def org(address: str, count: int = 10) -> JSONResponse:
    """Zeigt die ersten Mitarbeiter des virtuellen Unternehmens einer Adresse."""
    try:
        validate_address(address)
    except ValueError as err:
        raise HTTPException(400, str(err)) from err
    count = max(1, min(count, 50))
    boss = materialize(address)
    team = [materialize(f"{address}/{i}") for i in range(count)]
    return JSONResponse({
        "unternehmen": boss.company, "leitung": boss.display,
        "adressierbar": boss.sub_employees,
        "mitarbeiter_auszug": [
            {"adresse": e.address, "name": e.name, "rolle": e.role, "team": e.team}
            for e in team],
    })


@app.get("/api/business")
async def business() -> JSONResponse:
    """Business-Panel. Ehrlichkeits-Doktrin: keine erfundenen Umsätze.

    Dieses System kann kein Geld generieren. Angezeigt werden ausschließlich
    real gemessene Betriebsdaten; Finanzfelder bleiben 0, bis echte,
    belegbare Datenquellen (z. B. Buchhaltungs-Export) angebunden sind.
    """
    fin = orchestrator.finanzen()
    return JSONResponse({
        "hinweis": ("Keine simulierten Umsätze. Angezeigt wird nur, was real über das "
                    "finanzen-Plugin erfasst wurde. Kein System generiert Geld auf Knopfdruck."),
        "ziel_chf": fin["ziel_chf"],
        "umsatz_chf_real": fin["einnahmen_chf"],
        "kosten_chf_real": fin["ausgaben_chf"],
        "saldo_chf_real": fin["saldo_chf"],
        "fortschritt_zum_ziel_prozent": fin["fortschritt_prozent"],
        "datenquelle": f"finanzen-Plugin ({fin['eintraege']} manuell erfasste Einträge)",
        "betriebsdaten_real": {
            "erledigte_aufgaben": orchestrator.completed,
            "fehlgeschlagene_aufgaben": orchestrator.failed,
            "aktivierte_agenten": orchestrator.activated_agents,
        },
    })


class KeyIn(BaseModel):
    schluessel: str


@app.get("/api/brain")
async def brain_status() -> JSONResponse:
    from jarvis.core import brain
    return JSONResponse({"modus": brain.mode(), "modell": brain.DEFAULT_MODEL})


@app.get("/api/skills")
async def skills() -> JSONResponse:
    return JSONResponse({"skills": [
        {"name": s.name, "description": s.description} for s in orchestrator.skills.all()]})


@app.get("/api/tools")
async def tools() -> JSONResponse:
    return JSONResponse({"tools": orchestrator.plugins.status()})


@app.post("/api/brain/key")
async def brain_key(k: KeyIn) -> JSONResponse:
    """Fable-5-Button: API-Key lokal setzen und persistieren (nur auf diesem PC)."""
    import json
    key = k.schluessel.strip()
    if len(key) < 12:
        raise HTTPException(400, "Key sieht ungültig aus (zu kurz)")
    os.environ["ANTHROPIC_API_KEY"] = key
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "config.json").write_text(json.dumps({"anthropic_api_key": key}))
    from jarvis.core import brain
    orchestrator.log("info", "Fable-5-Button: API-Key gesetzt — Gehirn im API-Modus")
    return JSONResponse({"modus": brain.mode(), "modell": brain.DEFAULT_MODEL})


@app.get("/api/task/{task_id}")
async def get_task(task_id: int) -> JSONResponse:
    t = orchestrator.find_task(task_id)
    if t is None:
        raise HTTPException(404, "Aufgabe nicht (mehr) vorhanden")
    return JSONResponse(t.as_dict())


@app.post("/api/task")
async def create_task(task: TaskIn) -> JSONResponse:
    if not task.beschreibung.strip():
        raise HTTPException(400, "Beschreibung fehlt")
    t = orchestrator.submit(task.beschreibung.strip(), task.adresse)
    return JSONResponse({"id": t.id, "adresse": t.address, "status": t.status})
