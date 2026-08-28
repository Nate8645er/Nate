# Feierabend - Anschluss an bexio.
#
# Das ist der Grund, warum jemand zahlen soll: Der Rapport landet als
# verrechenbare Zeit in bexio, ohne dass jemand tippt. bexio selbst hat
# keinen Rapport-Workflow - das ist die einzige belegbare Luecke bei einem
# Anbieter mit Reichweite.
#
# Ehrlich zum Stand: Der OAuth-Ablauf und der Endpunkt sind nach der
# bexio-Dokumentation gebaut (postCreate timesheet, OAuth 2.0 mit
# Authorization Code Grant). Gegen die echte API ist das NICHT getestet -
# dafuer braucht es eine bexio-Anwendung mit Kennung und Geheimnis.
# Die Feldnamen im Zeiteintrag sind der wahrscheinlichste Punkt, an dem
# beim ersten echten Aufruf nachjustiert werden muss.

import os
from datetime import datetime
from urllib.parse import urlencode

AUTH_URL = ("https://auth.bexio.com/realms/bexio/protocol/"
            "openid-connect/auth")
TOKEN_URL = ("https://auth.bexio.com/realms/bexio/protocol/"
             "openid-connect/token")
API_BASIS = "https://api.bexio.com"

# Schreibrechte fuer Zeiteintraege, Lesen von Kontakten fuer den
# Kundenabgleich. Bewusst eng: Was wir nicht brauchen, fragen wir nicht an.
SCOPES = "openid profile email offline_access monitoring_edit contact_show"


class BexioFehler(Exception):
    """Aufruf gegen bexio fehlgeschlagen."""


class NichtVerbunden(BexioFehler):
    """Dieser Betrieb hat bexio nicht verbunden."""


def konfiguriert():
    return bool(os.environ.get("BEXIO_CLIENT_ID")
                and os.environ.get("BEXIO_CLIENT_SECRET"))


def anmelde_url(betrieb_id, rueckadresse):
    """Die URL, auf die der Betrieb geschickt wird, um zu verbinden.

    betrieb_id reist als 'state' mit und kommt beim Rueckruf zurueck -
    so wissen wir, welcher Mandant gerade verbunden wurde. Das ist
    zugleich der CSRF-Schutz des Ablaufs.
    """
    if not konfiguriert():
        raise BexioFehler("BEXIO_CLIENT_ID / BEXIO_CLIENT_SECRET fehlen")
    return AUTH_URL + "?" + urlencode({
        "client_id": os.environ["BEXIO_CLIENT_ID"],
        "redirect_uri": rueckadresse,
        "response_type": "code",
        "scope": SCOPES,
        "state": betrieb_id,
    })


def _post(url, daten, kopf=None):
    import requests
    try:
        r = requests.post(url, data=daten, headers=kopf or {}, timeout=20)
    except Exception as e:
        raise BexioFehler("Netzwerkfehler: %s" % e)
    if r.status_code >= 400:
        raise BexioFehler("bexio antwortete %d: %s"
                          % (r.status_code, r.text[:300]))
    return r.json()


def token_holen(code, rueckadresse):
    """Den Anmeldecode gegen Zugangs- und Erneuerungstoken tauschen."""
    return _post(TOKEN_URL, {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": rueckadresse,
        "client_id": os.environ["BEXIO_CLIENT_ID"],
        "client_secret": os.environ["BEXIO_CLIENT_SECRET"],
    })


def token_erneuern(refresh_token):
    return _post(TOKEN_URL, {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": os.environ["BEXIO_CLIENT_ID"],
        "client_secret": os.environ["BEXIO_CLIENT_SECRET"],
    })


def gueltiges_token(betrieb, speichern):
    """Zugangstoken besorgen, notfalls erneuern.

    'speichern' ist eine Funktion (token, refresh, gueltig_sekunden),
    damit dieses Modul die Datenbank nicht kennen muss.
    """
    if not betrieb.get("bexio_token"):
        raise NichtVerbunden("Betrieb hat bexio nicht verbunden")
    ablauf = betrieb.get("bexio_ablauf")
    if ablauf and datetime.fromisoformat(ablauf) > datetime.now():
        return betrieb["bexio_token"]
    if not betrieb.get("bexio_refresh"):
        raise NichtVerbunden("Zugang abgelaufen, bitte neu verbinden")
    neu = token_erneuern(betrieb["bexio_refresh"])
    speichern(neu["access_token"],
              neu.get("refresh_token", betrieb["bexio_refresh"]),
              neu.get("expires_in", 3600))
    return neu["access_token"]


def zeit_eintragen(token, rapport, benutzer_id=None):
    """Einen Rapport als Zeiteintrag nach bexio schreiben.

    Die Dauer geht als HH:MM, weil bexio Zeitspannen so erwartet. Der
    Text traegt Taetigkeit und Material zusammen - dort steht bewusst
    KEIN Beiwortlaut ueber Kundschaft, das filtert bereits die
    Extraktion.
    """
    import requests
    stunden = float(rapport["stunden"])
    dauer = "%02d:%02d" % (int(stunden), round((stunden % 1) * 60))
    text = rapport.get("taetigkeiten", "") or "Arbeitsrapport"
    if rapport.get("material"):
        material = rapport["material"]
        if isinstance(material, list):
            material = ", ".join(material)
        if material:
            text += " · Material: " + material

    nutzlast = {
        "date": rapport["datum"],
        "duration": dauer,
        "text": text[:255],
        "allowable_bill": True,
    }
    if benutzer_id:
        nutzlast["user_id"] = benutzer_id

    try:
        r = requests.post(
            API_BASIS + "/2.0/timesheet",
            json=nutzlast,
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/json"},
            timeout=20)
    except Exception as e:
        raise BexioFehler("Netzwerkfehler: %s" % e)
    if r.status_code >= 400:
        raise BexioFehler("bexio lehnte den Zeiteintrag ab (%d): %s"
                          % (r.status_code, r.text[:300]))
    return r.json()


def kunden_abrufen(token, hoechstens=500):
    """Kontakte aus bexio holen, um den Kundenstamm zu fuellen.

    Der Kundenstamm ist das, was die Pseudonymisierung ueberhaupt
    ermoeglicht - ohne ihn koennen wir keine Namen erkennen und also
    auch keine ersetzen.
    """
    import requests
    try:
        r = requests.get(
            API_BASIS + "/2.0/contact",
            params={"limit": hoechstens},
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/json"},
            timeout=20)
    except Exception as e:
        raise BexioFehler("Netzwerkfehler: %s" % e)
    if r.status_code >= 400:
        raise BexioFehler("bexio antwortete %d" % r.status_code)
    namen = []
    for k in r.json():
        name = (k.get("name_1") or "").strip()
        if k.get("name_2"):
            name = (name + " " + k["name_2"]).strip()
        if name:
            namen.append(name)
    return namen
