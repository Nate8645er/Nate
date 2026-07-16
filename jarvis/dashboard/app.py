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
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from jarvis.core.identity import materialize, validate_address
from jarvis.core.orchestrator import Orchestrator

DATA_DIR = Path(os.environ.get("JARVIS_DATA", Path.home() / ".jarvis"))
STATIC = Path(__file__).resolve().parent / "static"

orchestrator = Orchestrator(DATA_DIR)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Startet Belegschaft/Autopilot/Sicherheit und fährt beim Stop sauber herunter."""
    await _startup_tasks()
    yield
    await orchestrator.stop()


app = FastAPI(title="JARVIS HyperScale", version="1.1.0", lifespan=_lifespan)


def _host_from_header(raw: str) -> str:
    """Extrahiert den reinen Host aus dem Host-Header — inkl. IPv6 ('[::1]:8787')."""
    raw = raw.strip()
    if raw.startswith("["):                 # IPv6-Literal: [::1]:8787
        end = raw.find("]")
        return raw[1:end].lower() if end != -1 else raw.lower()
    return raw.rsplit(":", 1)[0].lower() if ":" in raw else raw.lower()


@app.middleware("http")
async def _host_guard(request, call_next):
    """Schutz vor DNS-Rebinding: nur Loopback-Hostnamen (oder ausdrücklich erlaubte)."""
    host = _host_from_header(request.headers.get("host") or "")
    allowed = {"127.0.0.1", "localhost", "::1", ""}
    extra = os.environ.get("JARVIS_ALLOWED_HOSTS", "")
    if extra:
        allowed |= {h.strip().lower() for h in extra.split(",") if h.strip()}
    if host not in allowed:
        return Response("Host nicht erlaubt (Schutz vor DNS-Rebinding). "
                        "Für LAN-Zugriff JARVIS_ALLOWED_HOSTS setzen.", status_code=403)
    return await call_next(request)


class KeyIn(BaseModel):
    schluessel: str


class TaskIn(BaseModel):
    beschreibung: str
    adresse: str | None = None


def _load_persisted_key() -> None:
    """Lädt über die Dashboard-Buttons gespeicherte API-Keys (lokale Datei)."""
    import json
    cfg = DATA_DIR / "config.json"
    if not cfg.exists():
        return
    try:
        data = json.loads(cfg.read_text())
    except Exception:
        return
    if data.get("anthropic_api_key") and not os.environ.get("ANTHROPIC_API_KEY"):
        os.environ["ANTHROPIC_API_KEY"] = data["anthropic_api_key"]
    if data.get("openrouter_api_key") and not os.environ.get("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = data["openrouter_api_key"]
    if data.get("elevenlabs_api_key") and not os.environ.get("ELEVENLABS_API_KEY"):
        os.environ["ELEVENLABS_API_KEY"] = data["elevenlabs_api_key"]
    if data.get("voice_id") and not os.environ.get("JARVIS_VOICE_ID"):
        os.environ["JARVIS_VOICE_ID"] = data["voice_id"]
    if data.get("brain_mode") and not os.environ.get("JARVIS_BRAIN"):
        os.environ["JARVIS_BRAIN"] = data["brain_mode"]
    if data.get("shortcut_token") and not os.environ.get("JARVIS_SHORTCUT_TOKEN"):
        os.environ["JARVIS_SHORTCUT_TOKEN"] = data["shortcut_token"]


def _persist_key(field: str, value: str) -> None:
    """Schreibt/aktualisiert einen Key in config.json mit 0600-Rechten."""
    import json
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg = DATA_DIR / "config.json"
    data = {}
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
        except Exception:
            data = {}
    data[field] = value
    fd = os.open(cfg, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    try:
        os.chmod(cfg, 0o600)
    except OSError:
        pass


async def _startup_tasks() -> None:
    _load_persisted_key()
    # Persönlicher Einzelplatz-Betrieb: alle Werkzeuge automatisch aktiv, damit
    # nichts manuell freigeschaltet werden muss (PC-Steuerung, Shell/Code).
    # JARVIS läuft nur auf 127.0.0.1 (Host-Guard). Wer den Schutz behalten will,
    # setzt JARVIS_LOCKDOWN=1 — dann bleiben gefährliche Werkzeuge gesperrt.
    if os.environ.get("JARVIS_LOCKDOWN") != "1":
        os.environ.setdefault("JARVIS_ALLOW_PC", "1")
        os.environ.setdefault("JARVIS_ALLOW_DANGEROUS", "1")
        orchestrator.log("info", "Alle Werkzeuge automatisch aktiviert "
                                 "(PC-Steuerung + Code). Schutz zurück mit JARVIS_LOCKDOWN=1.")
    # Autopilot standardmäßig an (kann mit JARVIS_AUTOPILOT=0 abgeschaltet werden).
    _autopilot_default = os.environ.get("JARVIS_AUTOPILOT", "1") != "0"
    await orchestrator.start()
    # Belegschaft-Betrieb standardmäßig an (Roll-Call der gesamten Organisation,
    # kein bezahltes Modell). Mit JARVIS_WORKFORCE=0 abschaltbar.
    if os.environ.get("JARVIS_WORKFORCE", "1") != "0":
        orchestrator.workforce.start()
        orchestrator.log("info", "Belegschaft-Betrieb gestartet: gesamte Organisation im Roll-Call")
    if _autopilot_default:
        orchestrator.autopilot.start()
        orchestrator.log("info", "24/7-Autopilot automatisch gestartet (Standard; aus mit JARVIS_AUTOPILOT=0)")
    # Sicherheits-Monitor standardmäßig an (alle 30 Min); mit JARVIS_SECURITY=0 abschaltbar.
    if os.environ.get("JARVIS_SECURITY", "1") != "0":
        orchestrator.security.start()
        orchestrator.bodyguards.start()
        orchestrator.log("info", "Sicherheits-Monitor + 24/7-Bodyguards gestartet")
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


@app.get("/favicon.ico")
async def favicon() -> Response:
    # Kleines SVG-Favicon (Krabbe/Kern), vermeidet 404 im Browser.
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
           '<circle cx="16" cy="16" r="13" fill="#040703" stroke="#2bff66" stroke-width="2"/>'
           '<circle cx="16" cy="16" r="5" fill="#7dffa8"/></svg>')
    return Response(content=svg, media_type="image/svg+xml")


@app.get("/")
async def start_page() -> FileResponse:
    return FileResponse(STATIC / "start.html")


# --- PWA: als App aufs Handy installierbar --------------------------------
@app.get("/manifest.webmanifest")
async def manifest() -> FileResponse:
    return FileResponse(STATIC / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
async def service_worker() -> FileResponse:
    # Service Worker MUSS von der Wurzel kommen (Scope '/'), nicht aus /static.
    return FileResponse(STATIC / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@app.get("/handy")
async def handy_page() -> FileResponse:
    return FileResponse(STATIC / "handy.html")


@app.get("/api/handy")
async def handy_info(request: Request) -> JSONResponse:
    """Info für den Handy-Zugang: LAN-Adresse (aus dem Host-Header) + QR-Ziel."""
    from jarvis.core.netinfo import lan_ip
    host = request.headers.get("host") or ""
    port = 8787
    if ":" in host and not host.endswith("]"):
        try:
            port = int(host.rsplit(":", 1)[1])
        except ValueError:
            pass
    ip = lan_ip()
    url = f"http://{ip}:{port}/" if ip else ""
    lan_offen = bool(os.environ.get("JARVIS_ALLOWED_HOSTS"))
    return JSONResponse({"lan_ip": ip, "port": port, "url": url,
                         "lan_modus_aktiv": lan_offen})


@app.get("/api/handy/qr.svg")
async def handy_qr(request: Request) -> Response:
    """QR-Code (SVG) zur LAN-Adresse — Handy scannt ihn und ist verbunden.
    Nutzt 'segno' (pure Python). Fehlt es, kommt 404 und die Seite zeigt nur die URL."""
    from jarvis.core.netinfo import lan_ip
    host = request.headers.get("host") or ""
    port = 8787
    if ":" in host and not host.endswith("]"):
        try:
            port = int(host.rsplit(":", 1)[1])
        except ValueError:
            pass
    ip = lan_ip()
    if not ip:
        return Response("keine LAN-IP", status_code=404)
    try:
        import io

        import segno
        buf = io.BytesIO()
        segno.make(f"http://{ip}:{port}/", error="m").save(
            buf, kind="svg", scale=6, dark="#2bff66", light="#040703", border=2)
        return Response(buf.getvalue().decode("utf-8"), media_type="image/svg+xml",
                        headers={"Cache-Control": "no-cache"})
    except Exception:
        return Response("segno nicht installiert", status_code=404)


# --- Apple Kurzbefehle / Siri: JARVIS per Sprache vom iPhone steuern ---------
@app.get("/kurzbefehle")
async def kurzbefehle_page() -> FileResponse:
    return FileResponse(STATIC / "kurzbefehle.html")


def _shortcut_authorized(request: Request) -> bool:
    """Token-Schutz: ist ein Token gesetzt, muss der Kurzbefehl es mitschicken."""
    token = os.environ.get("JARVIS_SHORTCUT_TOKEN", "")
    if not token:
        return True     # kein Token gesetzt -> offen (nur für lokalen Gebrauch sinnvoll)
    given = (request.headers.get("x-jarvis-token")
             or request.query_params.get("token", ""))
    return given == token


@app.api_route("/api/shortcut", methods=["GET", "POST"])
async def shortcut(request: Request) -> Response:
    """Kurzbefehl-/Siri-Endpunkt: nimmt einen Text-Befehl, führt ihn aus und
    gibt die Antwort als KLARTEXT zurück (damit Siri sie direkt vorlesen kann)."""
    if not _shortcut_authorized(request):
        return Response("Nicht autorisiert (Token fehlt oder falsch).",
                        status_code=401, media_type="text/plain; charset=utf-8")
    text = request.query_params.get("text", "") or request.query_params.get("q", "")
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                text = body.get("text") or body.get("q") or text
        except Exception:
            raw = (await request.body()).decode("utf-8", "ignore").strip()
            text = text or raw
    text = (text or "").strip()
    if not text:
        return Response("Sag JARVIS, was zu tun ist (Parameter 'text').",
                        media_type="text/plain; charset=utf-8")
    import asyncio
    antwort = await asyncio.to_thread(orchestrator.answer_now, text)
    orchestrator.log("info", f"Kurzbefehl (Siri): {text[:60]}")
    return Response(str(antwort), media_type="text/plain; charset=utf-8")


class TokenIn(BaseModel):
    token: str | None = None


@app.get("/api/shortcut/token")
async def shortcut_token_status() -> JSONResponse:
    tok = os.environ.get("JARVIS_SHORTCUT_TOKEN", "")
    return JSONResponse({"gesetzt": bool(tok),
                         "token_maskiert": (tok[:4] + "…" + tok[-4:]) if len(tok) > 10 else ("•" * len(tok)),
                         "token": tok})   # lokal (nur auf DIESEM Gerät sichtbar) zum Einrichten


@app.post("/api/shortcut/token")
async def shortcut_token_set(t: TokenIn) -> JSONResponse:
    """Setzt ein Token (oder erzeugt eines, wenn leer) und speichert es lokal."""
    import secrets
    tok = (t.token or "").strip() or secrets.token_urlsafe(18)
    os.environ["JARVIS_SHORTCUT_TOKEN"] = tok
    _persist_key("shortcut_token", tok)
    orchestrator.log("info", "Kurzbefehl-Token gesetzt/erneuert")
    return JSONResponse({"gesetzt": True, "token": tok})


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


@app.get("/sicherheit")
async def sicherheit_page() -> FileResponse:
    return FileResponse(STATIC / "sicherheit.html")


@app.get("/schluessel")
async def schluessel_page() -> FileResponse:
    return FileResponse(STATIC / "schluessel.html")


@app.get("/zugaenge")
async def zugaenge_page() -> FileResponse:
    return FileResponse(STATIC / "zugaenge.html")


# --- Zugänge-Vault: Plattform-Logins (lokal, verschlüsselt) ------------------
def _vault():
    from jarvis.core.zugaenge import Vault
    return Vault(DATA_DIR)


class ZugangIn(BaseModel):
    plattform: str
    benutzer: str
    passwort: str
    login_url: str = ""
    url: str = ""
    user_sel: str = ""
    pass_sel: str = ""
    submit_sel: str = ""


@app.get("/api/zugaenge")
async def zugaenge_list() -> JSONResponse:
    from jarvis.core.zugaenge import PRESETS
    v = _vault()
    return JSONResponse({
        "zugaenge": v.list(),
        "verschluesselt": v.verschluesselt,
        "master_passwort": bool(os.environ.get("JARVIS_VAULT_PW")),
        "presets": sorted(PRESETS.keys()),
    })


@app.post("/api/zugaenge")
async def zugaenge_set(z: ZugangIn) -> JSONResponse:
    try:
        res = _vault().set(z.plattform, z.benutzer, z.passwort, z.login_url,
                           z.url, z.user_sel, z.pass_sel, z.submit_sel)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    orchestrator.log("info", f"Zugang gespeichert: {res['plattform']} "
                             f"(verschlüsselt: {res['verschluesselt']})")
    return JSONResponse(res)


@app.delete("/api/zugaenge/{plattform}")
async def zugaenge_delete(plattform: str) -> JSONResponse:
    ok = _vault().delete(plattform)
    if ok:
        orchestrator.log("info", f"Zugang gelöscht: {plattform.lower()}")
    return JSONResponse({"geloescht": ok})


@app.post("/api/zugaenge/{plattform}/login")
async def zugaenge_login(plattform: str) -> JSONResponse:
    """Loggt sich JETZT bei einer Plattform ein (oder 'alle')."""
    plug = orchestrator.plugins.plugins.get("browser_auto")
    if plug is None:
        raise HTTPException(500, "Browser-Automatisierung nicht verfügbar")
    res = await asyncio.to_thread(orchestrator.plugins.run, "Führung",
                                  "browser_auto", "login", plattform=plattform)
    orchestrator.log("info", f"Auto-Login ausgelöst: {plattform}")
    return JSONResponse({"ergebnis": res})


class BrainModeIn(BaseModel):
    nur_openrouter: bool


@app.get("/api/brainmode")
async def brainmode_status() -> JSONResponse:
    from jarvis.core import brain
    return JSONResponse({"nur_openrouter": brain._only_openrouter()})


@app.post("/api/brainmode")
async def brainmode_set(m: BrainModeIn) -> JSONResponse:
    """'Nur OpenRouter' an/aus — Fable 5 überspringen (kein Anthropic nötig)."""
    from jarvis.core import brain
    os.environ["JARVIS_BRAIN"] = "openrouter" if m.nur_openrouter else "auto"
    _persist_key("brain_mode", os.environ["JARVIS_BRAIN"])
    brain._skip_anthropic = False   # Zustand neu bewerten lassen
    orchestrator.log("info", f"Modell-Modus: {'nur OpenRouter' if m.nur_openrouter else 'Fable 5 + OpenRouter'}")
    return JSONResponse({"nur_openrouter": brain._only_openrouter()})


@app.post("/api/security/check")
async def security_check() -> JSONResponse:
    import asyncio
    report = await asyncio.to_thread(orchestrator.plugins.plugins["security"].check)
    orchestrator.security.last = report
    orchestrator.security.reports.appendleft(report)
    return JSONResponse(report)


@app.post("/api/security/scan")
async def security_scan() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "scan")
    return JSONResponse({"ergebnis": str(r)})


@app.post("/api/security/signatures")
async def security_signatures() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "signatures")
    return JSONResponse({"ergebnis": str(r)})


@app.post("/api/security/update")
async def security_update() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "update")
    return JSONResponse({"ergebnis": str(r)})


@app.post("/api/security/threats")
async def security_threats() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "threats")
    return JSONResponse({"ergebnis": str(r)})


@app.post("/api/security/remove")
async def security_remove() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "remove")
    return JSONResponse({"ergebnis": str(r)})


@app.post("/api/security/fullscan")
async def security_fullscan() -> JSONResponse:
    import asyncio
    r = await asyncio.to_thread(orchestrator.plugins.plugins["security"].run, "fullscan")
    return JSONResponse({"ergebnis": str(r)})


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
    fort = orchestrator.progression.get(e.address)
    eff = orchestrator.progression.effective_level(e.level, e.address)
    return JSONResponse({
        "adresse": e.address, "name": e.name, "team": e.team, "rolle": e.role,
        "spezialisierung": e.specialization, "skills": list(e.skills),
        "ziele": list(e.goals), "prioritaet": e.priority,
        "eigenes_unternehmen": e.company, "ebene": e.depth,
        "adressierbare_mitarbeiter_im_eigenen_unternehmen": e.sub_employees,
        "plugins_autorisiert": orchestrator.plugins.for_team(e.team),
        # Level & Meisterschaft (prozedurale Basis + echt verdiente Erfahrung)
        "level_basis": e.level, "level": eff, "meisterschaft": e.mastery,
        "werkzeuge_beherrscht": list(e.tools),
        "erfahrung_basis": e.xp, "erledigte_aufgaben": fort["erledigt"],
        "bonus_level": fort["bonus_level"], "verdiente_xp": fort["xp"],
        "ist_teamleiter": e.is_team_boss, "chef_adresse": e.boss_address,
        "chef_name": materialize(e.boss_address).name if not e.is_team_boss else None,
    })


@app.get("/api/teammode")
async def teammode_status() -> JSONResponse:
    return JSONResponse({"an": orchestrator.team_mode})


@app.post("/api/teammode")
async def teammode_set(k: KeyIn) -> JSONResponse:
    """Team-Modus an/aus (schluessel = '1'/'an' -> an, sonst aus)."""
    orchestrator.team_mode = k.schluessel.strip().lower() in ("1", "an", "true", "on")
    orchestrator.log("info", f"Team-Modus {'AN' if orchestrator.team_mode else 'AUS'}")
    return JSONResponse({"an": orchestrator.team_mode})


@app.get("/api/teams")
async def teams(company: str = "") -> JSONResponse:
    """Die 25 Teams eines Unternehmens mit ihrem jeweiligen Teamleiter (Chef)."""
    from jarvis.core.identity import team_bosses
    try:
        bosses = team_bosses(company)
    except ValueError as err:
        raise HTTPException(400, str(err)) from err
    return JSONResponse({
        "unternehmen": company or "Wurzelorganisation",
        "teams": [{"team": b.team, "chef": b.name, "chef_adresse": b.address,
                   "rolle": b.role, "meisterschaft": b.mastery, "level": b.level}
                  for b in bosses],
        "anzahl_teams": len(bosses),
    })


@app.get("/api/fortschritt/top")
async def fortschritt_top(limit: int = 10) -> JSONResponse:
    """Bestenliste: Mitarbeiter mit den meisten verdienten Erfahrungspunkten."""
    limit = max(1, min(limit, 50))
    out = []
    for row in orchestrator.progression.top(limit):
        try:
            e = materialize(row["adresse"])
            eff = min(99, e.level + row["bonus_level"])
            out.append({"adresse": row["adresse"], "name": e.name, "team": e.team,
                        "meisterschaft": e.mastery, "level": eff,
                        "erledigt": row["erledigt"], "xp": row["xp"]})
        except ValueError:
            continue
    return JSONResponse({"bestenliste": out, "summe": orchestrator.progression.totals()})


@app.post("/api/training/build")
async def training_build() -> JSONResponse:
    """Baut den Trainingsdatensatz aus JARVIS' echten Daten (Klick statt CLI)."""
    import asyncio

    from jarvis.training import build_dataset as bd
    from jarvis.training import tokenize_stats as ts
    examples = await asyncio.to_thread(bd.build, DATA_DIR)
    out_path = DATA_DIR / "dataset.jsonl"
    n = bd.write_jsonl(examples, out_path)
    stats = ts.stats(out_path) if n else {"beispiele": 0}
    orchestrator.log("info", f"Trainingsdatensatz gebaut: {n} Beispiele")
    return JSONResponse({
        "beispiele": n, "datei": str(out_path), "statistik": stats,
        "hinweis": ("Bereit für Fine-Tuning (Chat-JSONL)." if n else
                    "Noch keine brauchbaren Daten — JARVIS muss erst mit echtem "
                    "API-Key Aufgaben/Ideen erzeugen."),
    })


@app.get("/api/org/{address:path}")
async def org(address: str, count: int = 10) -> JSONResponse:
    """Zeigt die ersten Mitarbeiter des virtuellen Unternehmens einer Adresse."""
    try:
        segments = validate_address(address)
        address = "/".join(str(s) for s in segments)   # kanonisieren (Trailing-Slash '5/' -> '5')
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



@app.get("/api/brain")
async def brain_status() -> JSONResponse:
    from jarvis.core import brain
    return JSONResponse({"modus": brain.mode(), "modell": brain.active_model()})


@app.post("/api/brain/verify")
async def brain_verify() -> JSONResponse:
    """Echter Test-Aufruf: prüft, ob Key + Modell wirklich antworten."""
    import asyncio
    from jarvis.core import brain
    result = await asyncio.to_thread(brain.verify)
    if result.get("ok"):
        orchestrator.log("info", f"Fable 5 verifiziert: Modell {result['modell']} antwortet")
    return JSONResponse(result)


@app.get("/api/skills")
async def skills() -> JSONResponse:
    return JSONResponse({"skills": [
        {"name": s.name, "description": s.description} for s in orchestrator.skills.all()]})


@app.get("/api/tools")
async def tools() -> JSONResponse:
    st = orchestrator.plugins.status()
    return JSONResponse({
        "tools": st,
        "lauffaehig": sum(1 for t in st if t.get("ok")),
        "gesamt": len(st),
        "ladefehler": getattr(orchestrator.plugins, "load_errors", []),
    })


@app.post("/api/brain/key")
async def brain_key(k: KeyIn) -> JSONResponse:
    """Fable-5-Button: API-Key lokal setzen und persistieren (nur auf diesem PC)."""
    import json
    key = k.schluessel.strip()
    if len(key) < 12:
        raise HTTPException(400, "Key sieht ungültig aus (zu kurz)")
    os.environ["ANTHROPIC_API_KEY"] = key
    _persist_key("anthropic_api_key", key)   # 0600, nicht weltlesbar
    import asyncio

    from jarvis.core import brain
    result = await asyncio.to_thread(brain.verify)
    if result.get("ok"):
        orchestrator.log("info", f"Fable 5 aktiviert & verifiziert: {result['modell']}")
    else:
        orchestrator.log("warn", f"Key gesetzt, aber Verify fehlgeschlagen: {result.get('grund')}")
    return JSONResponse({"modus": brain.mode(), "modell": brain.active_model(), "verify": result})


@app.get("/api/modelle/key")
async def modelle_key_status() -> JSONResponse:
    """Ist ein OpenRouter-Key aktiv? (verrät den Key selbst nicht)"""
    from jarvis.core import openrouter
    return JSONResponse({"aktiv": openrouter.available()})


@app.post("/api/modelle/key")
async def modelle_key(k: KeyIn) -> JSONResponse:
    """OpenRouter-Key lokal setzen und persistieren (nur auf diesem PC)."""
    key = k.schluessel.strip()
    if len(key) < 12:
        raise HTTPException(400, "Key sieht ungültig aus (zu kurz)")
    os.environ["OPENROUTER_API_KEY"] = key
    _persist_key("openrouter_api_key", key)   # 0600, nicht weltlesbar
    from jarvis.core import openrouter
    orchestrator.log("info", "OpenRouter-Key gesetzt — Multi-Modell-Zugang aktiv")
    return JSONResponse({"aktiv": openrouter.available()})


# --- Echte Stimme (ElevenLabs, optional) -----------------------------------

class VoiceKeyIn(BaseModel):
    schluessel: str
    stimm_id: str | None = None


@app.get("/api/voice/status")
async def voice_status() -> JSONResponse:
    from jarvis.core import voice
    return JSONResponse({"aktiv": voice.available(), "stimm_id": voice.voice_id()})


@app.post("/api/voice/key")
async def voice_key(k: VoiceKeyIn) -> JSONResponse:
    """ElevenLabs-Key (+ optional Stimm-ID) lokal setzen und persistieren."""
    from jarvis.core import voice
    key = k.schluessel.strip()
    if len(key) < 12:
        raise HTTPException(400, "Key sieht ungültig aus (zu kurz)")
    os.environ["ELEVENLABS_API_KEY"] = key
    _persist_key("elevenlabs_api_key", key)
    if k.stimm_id and k.stimm_id.strip():
        os.environ["JARVIS_VOICE_ID"] = k.stimm_id.strip()
        _persist_key("voice_id", k.stimm_id.strip())
    orchestrator.log("info", f"Echte Stimme aktiviert (ElevenLabs, Stimme {voice.voice_id()})")
    return JSONResponse({"aktiv": voice.available(), "stimm_id": voice.voice_id()})


@app.post("/api/voice/say")
async def voice_say(k: KeyIn) -> Response:
    """Text -> Audio (MP3) mit der echten Stimme. 204, wenn kein Key/Fehler
    (dann nutzt die Weboberfläche automatisch die Browser-Stimme)."""
    import asyncio

    from jarvis.core import voice
    text = k.schluessel.strip()   # 'schluessel' trägt hier den Text
    if not text:
        raise HTTPException(400, "kein Text")
    audio = await asyncio.to_thread(voice.synthesize, text)
    if not audio:
        return Response(status_code=204)
    return Response(content=audio, media_type="audio/mpeg")


@app.get("/autopilot")
async def autopilot_page() -> FileResponse:
    return FileResponse(STATIC / "autopilot.html")


@app.post("/api/autopilot/start")
async def autopilot_start() -> JSONResponse:
    orchestrator.autopilot.start()
    orchestrator.log("info", "24/7-Autopilot GESTARTET — Mitarbeiter erfinden Ideen")
    return JSONResponse(orchestrator.autopilot.stats())


@app.post("/api/autopilot/stop")
async def autopilot_stop() -> JSONResponse:
    orchestrator.autopilot.stop()
    orchestrator.log("info", "24/7-Autopilot gestoppt")
    return JSONResponse(orchestrator.autopilot.stats())


@app.get("/api/autopilot/briefing")
async def autopilot_briefing() -> JSONResponse:
    """Tages-Briefing: was die Mitarbeiter heute erarbeitet haben (echte Daten)."""
    ideen = orchestrator.autopilot.today()
    fin = orchestrator.finanzen()
    return JSONResponse({
        "datum": __import__("time").strftime("%Y-%m-%d"),
        "ideen_heute": len(ideen),
        "ideen": [{"zeit": e["zeit"], "von": e["von"], "team": e.get("team", ""),
                   "text": e["text"]} for e in ideen[-50:]],
        "erledigte_aufgaben_gesamt": orchestrator.completed,
        "profit_heute_chf_real": fin["einnahmen_chf"],
        "hinweis": ("Ideen sind echte Vorarbeit, kein Geld. Profit zeigt nur real "
                    "über das finanzen-Plugin erfasste Einnahmen — 0.00, bis du echte "
                    "Verkäufe einträgst."),
    })


@app.post("/api/workforce/start")
async def workforce_start() -> JSONResponse:
    """Belegschaft-Betrieb starten: gesamte Organisation kontinuierlich aktivieren."""
    orchestrator.workforce.start()
    orchestrator.log("info", "Belegschaft-Betrieb GESTARTET — gesamte Organisation läuft")
    return JSONResponse(orchestrator.workforce.stats())


@app.post("/api/workforce/stop")
async def workforce_stop() -> JSONResponse:
    orchestrator.workforce.stop()
    orchestrator.log("info", "Belegschaft-Betrieb gestoppt")
    return JSONResponse(orchestrator.workforce.stats())


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
    adresse = (task.adresse or "").strip() or None
    if adresse is not None:
        try:
            validate_address(adresse)
        except ValueError as err:
            raise HTTPException(400, f"Ungültige Adresse: {err}") from err
    t = orchestrator.submit(task.beschreibung.strip(), adresse)
    return JSONResponse({"id": t.id, "adresse": t.address, "status": t.status})
