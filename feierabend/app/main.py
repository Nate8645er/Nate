# Feierabend - Webdienst.
#
# Ablauf einer Erfassung:
#   1. Browser erkennt Sprache (Web Speech API) - Audio bleibt auf dem Geraet
#   2. Text kommt hier an
#   3. Kundennamen werden lokal durch Token ersetzt
#   4. Sicherheitsnetz prueft, ob wirklich kein Klarname mehr drinsteht
#   5. Erst dann geht der Text an das Sprachmodell
#   6. Handwerker bestaetigt den Entwurf, danach wird gespeichert
#
# Nichts wird ohne Bestaetigung gespeichert. Ein still falsch abgelegter
# Rapport ist schlimmer als gar keiner - er wird verrechnet.

import os
import sys
import time
from collections import defaultdict
from datetime import date

from fastapi import FastAPI, Header, Request
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                               RedirectResponse)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HIER, "..", "core"))
sys.path.insert(0, HIER)

import bexio  # noqa: E402
import db  # noqa: E402
import llm  # noqa: E402
from pseudonym import Kunde, Pseudonymisierer  # noqa: E402

STATIC = os.path.join(HIER, "static")
BASIS_URL = os.environ.get("FEIERABEND_URL", "http://localhost:8000")

app = FastAPI(title="Feierabend")

# Ratenbegrenzung je Zugangscode. Ohne sie kann ein geleakter Code das
# Modellbudget abbrennen.
_anfragen = defaultdict(list)
RATE_FENSTER = 60
RATE_MAX = 30


def _rate_ok(schluessel):
    jetzt = time.monotonic()
    letzte = [t for t in _anfragen[schluessel] if t > jetzt - RATE_FENSTER]
    if len(letzte) >= RATE_MAX:
        _anfragen[schluessel] = letzte
        return False
    letzte.append(jetzt)
    _anfragen[schluessel] = letzte
    return True


def _anmelden(code):
    """Zugangscode aufloesen. Der einzige Weg in einen Mandanten."""
    if not code:
        return None, JSONResponse({"fehler": "Zugangscode fehlt"},
                                  status_code=401)
    if not _rate_ok(code):
        return None, JSONResponse({"fehler": "Zu viele Anfragen"},
                                  status_code=429)
    nutzer = db.mitarbeiter_per_code(code)
    if not nutzer:
        return None, JSONResponse({"fehler": "Zugangscode unbekannt"},
                                  status_code=401)
    return nutzer, None


def _pseudonymisierer(betrieb_id):
    kunden = [Kunde(id=k["id"], name=k["name"])
              for k in db.kunden_lesen(betrieb_id)]
    return Pseudonymisierer(kunden)


@app.on_event("startup")
def start():
    db.anlegen()


# ---------------------------------------------------------------- Modelle

class Anmeldung(BaseModel):
    code: str


class Entwurf(BaseModel):
    text: str


class RapportDaten(BaseModel):
    datum: str
    kunde: str
    stunden: float
    taetigkeiten: str = ""
    material: list = []
    folgetermin: str = ""


# ----------------------------------------------------------------- Routen

@app.get("/api/status")
def status():
    return {"bereit": True,
            "modell": llm.verfuegbar(),
            "bexio": bexio.konfiguriert()}


@app.post("/api/anmelden")
def anmelden(daten: Anmeldung):
    nutzer, fehler = _anmelden(daten.code)
    if fehler:
        return fehler
    return {"name": nutzer["name"], "betrieb": nutzer["betrieb_name"]}


@app.get("/api/kunden")
def kunden(x_code: str = Header(default="")):
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    return {"kunden": db.kunden_lesen(nutzer["betrieb_id"])}


@app.post("/api/entwurf")
def entwurf(daten: Entwurf, x_code: str = Header(default="")):
    """Gesprochenen Text in einen Rapport-Entwurf verwandeln.

    Speichert nichts. Der Handwerker sieht den Entwurf und bestaetigt ihn
    erst - oder korrigiert ihn.
    """
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    text = (daten.text or "").strip()
    if not text:
        return JSONResponse({"fehler": "Kein Text erkannt"}, status_code=400)

    pseudo = _pseudonymisierer(nutzer["betrieb_id"])
    zuordnung = pseudo.pseudonymisieren(text)

    # Sicherheitsnetz: Steht noch ein Klarname drin, geht nichts raus.
    if pseudo.enthaelt_klarnamen(zuordnung.text):
        return JSONResponse(
            {"fehler": "Interner Pruefabbruch - bitte erneut aufnehmen"},
            status_code=500)

    historie = db.rapporte_lesen(nutzer["betrieb_id"])
    try:
        roh = llm.rapport_aus_text(
            zuordnung.text,
            bekannte_token=sorted(zuordnung.treffer),
            uebliche_materialien=llm.materialien_aus_rapporten(historie))
    except llm.ModellNichtVerfuegbar as e:
        return JSONResponse({"fehler": str(e)}, status_code=503)
    except Exception:
        return JSONResponse(
            {"fehler": "Konnte den Rapport nicht lesen - nochmals bitte"},
            status_code=422)

    kunde_name = ""
    if roh["kunde_token"]:
        eintrag = pseudo.kunde_zu_token(roh["kunde_token"])
        if eintrag:
            kunde_name = eintrag.name

    fehlend = []
    if not kunde_name:
        fehlend.append("kunde")
    if roh["stunden"] is None:
        fehlend.append("stunden")

    return {
        "datum": date.today().strftime("%Y-%m-%d"),
        "kunde": kunde_name,
        "stunden": roh["stunden"],
        "taetigkeiten": pseudo.aufloesen(roh["taetigkeiten"]),
        "material": roh["material"],
        "folgetermin": roh["folgetermin"],
        "fehlend": fehlend,
        "unbekannte_namen": zuordnung.unbekannt,
        "rueckfrage": _rueckfrage(fehlend, kunde_name, zuordnung.unbekannt),
    }


def _rueckfrage(fehlend, kunde, unbekannt):
    if not fehlend:
        return ""
    if unbekannt:
        return ("Den Namen %s kenne ich noch nicht. Zu welchem Kunden "
                "gehoert der Rapport?" % unbekannt[0])
    if fehlend == ["stunden"]:
        return "Wie lange warst du bei %s?" % (kunde or "dem Kunden")
    if fehlend == ["kunde"]:
        return "Bei welchem Kunden war das?"
    return "Bei welchem Kunden warst du, und wie lange?"


@app.post("/api/rapport")
def rapport_speichern(daten: RapportDaten, x_code: str = Header(default="")):
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    if not daten.kunde.strip():
        return JSONResponse({"fehler": "Kunde fehlt"}, status_code=400)
    if not (0.25 <= daten.stunden <= 16):
        return JSONResponse({"fehler": "Stunden unplausibel"},
                            status_code=400)
    neu_id = db.rapport_speichern(nutzer["betrieb_id"], nutzer["id"],
                                  daten.model_dump())
    return {"id": neu_id, "gespeichert": True}


@app.get("/api/rapporte")
def rapporte(x_code: str = Header(default="")):
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    return {"rapporte": db.rapporte_lesen(nutzer["betrieb_id"])[:50]}


@app.get("/api/auswertung")
def auswertung(tage: int = 7, x_code: str = Header(default="")):
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    return db.wochenauswertung(nutzer["betrieb_id"], max(1, min(tage, 90)))


# ------------------------------------------------------------------ bexio

@app.get("/bexio/verbinden")
def bexio_verbinden(code: str = ""):
    nutzer, fehler = _anmelden(code)
    if fehler:
        return fehler
    try:
        url = bexio.anmelde_url(nutzer["betrieb_id"],
                               BASIS_URL + "/bexio/rueckruf")
    except bexio.BexioFehler as e:
        return JSONResponse({"fehler": str(e)}, status_code=503)
    return RedirectResponse(url)


@app.get("/bexio/rueckruf")
def bexio_rueckruf(code: str = "", state: str = ""):
    if not code or not state:
        return HTMLResponse("<p>Verbindung abgebrochen.</p>",
                            status_code=400)
    try:
        token = bexio.token_holen(code, BASIS_URL + "/bexio/rueckruf")
    except bexio.BexioFehler as e:
        return HTMLResponse("<p>bexio: %s</p>" % e, status_code=502)
    db.bexio_token_speichern(state, token["access_token"],
                             token.get("refresh_token", ""),
                             token.get("expires_in", 3600))
    # Kundenstamm gleich mitziehen - ohne ihn kann nichts pseudonymisiert
    # werden.
    try:
        for name in bexio.kunden_abrufen(token["access_token"]):
            db.kunde_anlegen(state, name)
    except bexio.BexioFehler:
        pass
    return HTMLResponse(
        "<p style='font-family:sans-serif;padding:40px'>bexio verbunden. "
        "Du kannst dieses Fenster schliessen.</p>")


@app.post("/api/rapport/{rapport_id}/bexio")
def nach_bexio(rapport_id: int, x_code: str = Header(default="")):
    nutzer, fehler = _anmelden(x_code)
    if fehler:
        return fehler
    treffer = [r for r in db.rapporte_lesen(nutzer["betrieb_id"])
               if r["id"] == rapport_id]
    if not treffer:
        return JSONResponse({"fehler": "Rapport nicht gefunden"},
                            status_code=404)
    betrieb = db.betrieb_lesen(nutzer["betrieb_id"])
    try:
        token = bexio.gueltiges_token(
            betrieb,
            lambda t, r, s: db.bexio_token_speichern(
                nutzer["betrieb_id"], t, r, s))
        antwort = bexio.zeit_eintragen(token, treffer[0])
    except bexio.NichtVerbunden as e:
        return JSONResponse({"fehler": str(e)}, status_code=409)
    except bexio.BexioFehler as e:
        return JSONResponse({"fehler": str(e)}, status_code=502)
    return {"uebertragen": True, "bexio": antwort}


# --------------------------------------------------------------- Oberflaeche

@app.get("/")
def start_seite():
    return FileResponse(os.path.join(STATIC, "index.html"))


app.mount("/", StaticFiles(directory=STATIC), name="static")
