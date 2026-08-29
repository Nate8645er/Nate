# JAVIER MOBILE - Agent tools
# All tools operate on local files under data/ or call read-only external APIs.

import json
import os
import re
import subprocess
import sys
import uuid
from datetime import datetime, timedelta

import requests

import instagram

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TODO_FILE = os.path.join(DATA_DIR, "todos.json")
ICS_FILE = os.path.join(DATA_DIR, "calendar.ics")
CONTACTS_FILE = os.path.join(BASE_DIR, "contacts.json")
OUTBOX_DIR = os.path.join(DATA_DIR, "outbox")
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")

# Rapperswil-Jona, Switzerland
WEATHER_LAT = 47.2266
WEATHER_LON = 8.8184


def _ensure_dirs():
    for d in (DATA_DIR, OUTBOX_DIR, SCREENSHOT_DIR):
        os.makedirs(d, exist_ok=True)


# ---------------------------------------------------------------- todos

def _load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_todos(todos):
    _ensure_dirs()
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def manage_todos(action, text=None, todo_id=None):
    todos = _load_todos()
    if action == "add":
        if not text:
            return {"error": "text is required for action=add"}
        item = {
            "id": max([t["id"] for t in todos], default=0) + 1,
            "text": text,
            "done": False,
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        todos.append(item)
        _save_todos(todos)
        return {"ok": True, "added": item}
    if action == "list":
        return {"todos": todos}
    if action == "complete":
        for t in todos:
            if t["id"] == todo_id:
                t["done"] = True
                _save_todos(todos)
                return {"ok": True, "completed": t}
        return {"error": "no todo with id %s" % todo_id}
    if action == "delete":
        kept = [t for t in todos if t["id"] != todo_id]
        if len(kept) == len(todos):
            return {"error": "no todo with id %s" % todo_id}
        _save_todos(kept)
        return {"ok": True, "deleted_id": todo_id}
    return {"error": "unknown action: %s" % action}


# ------------------------------------------------------------- calendar

ICS_HEADER = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//JAVIER//DE\r\n"
ICS_FOOTER = "END:VCALENDAR\r\n"


def _read_events():
    if not os.path.exists(ICS_FILE):
        return []
    with open(ICS_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    events = []
    for block in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", content, re.S):
        ev = {}
        for line in block.strip().splitlines():
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.split(";")[0].strip()
            ev[key] = val.strip()
        if "DTSTART" in ev:
            events.append(ev)
    return events


def _write_events(events):
    _ensure_dirs()
    parts = [ICS_HEADER]
    for ev in events:
        parts.append("BEGIN:VEVENT\r\n")
        for key in ("UID", "DTSTART", "DTEND", "SUMMARY", "LOCATION"):
            if key in ev and ev[key]:
                parts.append("%s:%s\r\n" % (key, ev[key]))
        parts.append("END:VEVENT\r\n")
    parts.append(ICS_FOOTER)
    with open(ICS_FILE, "w", encoding="utf-8") as f:
        f.write("".join(parts))


def _parse_dt(value):
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def read_calendar(days=7):
    now = datetime.now()
    horizon = now + timedelta(days=days)
    result = []
    for ev in _read_events():
        dt = _parse_dt(ev.get("DTSTART", ""))
        if dt and now - timedelta(hours=12) <= dt <= horizon:
            result.append({
                "summary": ev.get("SUMMARY", "(ohne Titel)"),
                "start": dt.isoformat(timespec="minutes"),
                "location": ev.get("LOCATION", ""),
            })
    result.sort(key=lambda e: e["start"])
    return {"events": result, "days": days}


def add_event(title, date, time="09:00", duration_minutes=60, location=""):
    try:
        start = datetime.strptime("%s %s" % (date, time), "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "date must be YYYY-MM-DD and time HH:MM"}
    end = start + timedelta(minutes=duration_minutes)
    events = _read_events()
    events.append({
        "UID": str(uuid.uuid4()),
        "DTSTART": start.strftime("%Y%m%dT%H%M%S"),
        "DTEND": end.strftime("%Y%m%dT%H%M%S"),
        "SUMMARY": title,
        "LOCATION": location,
    })
    _write_events(events)
    return {"ok": True, "title": title, "start": start.isoformat(timespec="minutes")}


# -------------------------------------------------------------- weather

WEATHER_CODES = {
    0: "klar", 1: "ueberwiegend klar", 2: "teils bewoelkt", 3: "bedeckt",
    45: "Nebel", 48: "Reifnebel", 51: "leichter Nieselregen",
    53: "Nieselregen", 55: "starker Nieselregen", 61: "leichter Regen",
    63: "Regen", 65: "starker Regen", 71: "leichter Schneefall",
    73: "Schneefall", 75: "starker Schneefall", 80: "Regenschauer",
    81: "Regenschauer", 82: "starke Regenschauer", 95: "Gewitter",
    96: "Gewitter mit Hagel", 99: "schweres Gewitter mit Hagel",
}


def get_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=%s&longitude=%s"
        "&current=temperature_2m,apparent_temperature,weather_code,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code"
        "&timezone=Europe%%2FZurich&forecast_days=3"
    ) % (WEATHER_LAT, WEATHER_LON)
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        d = r.json()
    except requests.RequestException as e:
        return {"error": "weather request failed: %s" % e}
    cur = d.get("current", {})
    daily = d.get("daily", {})
    days = []
    for i, day in enumerate(daily.get("time", [])):
        days.append({
            "date": day,
            "min": daily["temperature_2m_min"][i],
            "max": daily["temperature_2m_max"][i],
            "rain_probability": daily["precipitation_probability_max"][i],
            "condition": WEATHER_CODES.get(daily["weather_code"][i], "unbekannt"),
        })
    return {
        "location": "Rapperswil-Jona",
        "now": {
            "temperature": cur.get("temperature_2m"),
            "feels_like": cur.get("apparent_temperature"),
            "wind_kmh": cur.get("wind_speed_10m"),
            "condition": WEATHER_CODES.get(cur.get("weather_code"), "unbekannt"),
        },
        "forecast": days,
    }


# -------------------------------------------------------------- shopify

def get_shopify_status(days=7):
    store = os.environ.get("SHOPIFY_STORE", "")
    token = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")
    if not store or not token:
        return {"error": "SHOPIFY_STORE / SHOPIFY_ACCESS_TOKEN fehlen in .env"}
    since = (datetime.now() - timedelta(days=days)).isoformat()
    url = "https://%s/admin/api/2024-01/orders.json" % store
    params = {"status": "any", "created_at_min": since, "limit": 250,
              "fields": "id,name,created_at,total_price,currency,financial_status"}
    try:
        r = requests.get(url, params=params,
                         headers={"X-Shopify-Access-Token": token}, timeout=15)
        r.raise_for_status()
        orders = r.json().get("orders", [])
    except requests.RequestException as e:
        return {"error": "shopify request failed: %s" % e}
    total = sum(float(o.get("total_price", 0)) for o in orders)
    currency = orders[0]["currency"] if orders else "CHF"
    return {
        "store": "MeowUfo",
        "days": days,
        "order_count": len(orders),
        "revenue": round(total, 2),
        "currency": currency,
        "latest_orders": [
            {"name": o["name"], "created": o["created_at"],
             "total": o["total_price"], "status": o.get("financial_status")}
            for o in orders[:5]
        ],
    }


# ------------------------------------------------------------- messages

def _load_contacts():
    # Two sources, merged: contacts.json next to the code (example file,
    # do NOT put real numbers there - the repo is public) and the private
    # CONTACTS environment variable (set it in Render). The env var wins
    # and accepts either JSON ({"Mutter": "+41791234567"}) or the simple
    # form: Mutter=+41791234567, Bruder=+41761234567
    contacts = {}
    if os.path.exists(CONTACTS_FILE):
        try:
            with open(CONTACTS_FILE, "r", encoding="utf-8") as f:
                contacts.update(json.load(f))
        except (ValueError, OSError):
            pass
    env = ""
    for key, value in os.environ.items():
        if key.upper() == "CONTACTS":
            env = value.strip()
            break
    if env:
        try:
            if env.startswith("{"):
                contacts.update(json.loads(env))
            else:
                for part in re.split(r"[,;\n]+", env):
                    if "=" in part:
                        name, num = part.split("=", 1)
                        if name.strip() and num.strip():
                            contacts[name.strip()] = num.strip()
        except ValueError:
            pass
    return contacts


def list_contacts():
    contacts = _load_contacts()
    return {
        "contacts": sorted(contacts.keys()),
        "count": len(contacts),
        "note": "Nummern werden aus Datenschutzgruenden nicht vorgelesen. "
                "Neue Kontakte traegt Nate in Render als CONTACTS-"
                "Umgebungsvariable ein (Format: Name=+41791234567, ...).",
    }


def prepare_message(contact_name, message, channel="whatsapp"):
    # Honest semi-automatic flow: this only prepares the message. The
    # frontend shows a button that opens sms: or wa.me with the text
    # prefilled - Nate taps send himself. iOS does not allow apps or web
    # pages to send SMS/WhatsApp fully automatically.
    contacts = _load_contacts()
    number = None
    for name, num in contacts.items():
        if name.lower() == contact_name.lower():
            number = num
            break
    if not number:
        return {"error": "Kontakt '%s' nicht in contacts.json gefunden. "
                         "Vorhandene Kontakte: %s"
                         % (contact_name, ", ".join(contacts) or "(keine)")}
    return {
        "ok": True,
        "note": "Nachricht vorbereitet. Nate sieht jetzt einen Button und "
                "muss selbst auf Senden tippen - automatisches Senden ist "
                "auf iOS nicht moeglich.",
        "_frontend_action": {
            "type": "message",
            "channel": channel,
            "contact": contact_name,
            "number": number,
            "text": message,
        },
    }


# ------------------------------------------------------------ instagram

def prepare_instagram_post(caption, image_path=""):
    _ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    post_dir = os.path.join(OUTBOX_DIR, "post_%s" % stamp)
    os.makedirs(post_dir, exist_ok=True)
    with open(os.path.join(post_dir, "caption.txt"), "w", encoding="utf-8") as f:
        f.write(caption)
    copied = False
    if image_path and os.path.exists(image_path):
        import shutil
        shutil.copy(image_path, post_dir)
        copied = True
    return {
        "ok": True,
        "outbox_folder": post_dir,
        "image_copied": copied,
        "note": "Post liegt im Ausgangskorb. Er wurde NICHT veroeffentlicht - "
                "Nate postet ihn selbst, oder nutzt publish_instagram_post, "
                "falls die Graph API konfiguriert ist.",
    }


def publish_instagram_post(image_url, caption):
    # Only registered as a tool when instagram.is_configured() is true.
    return instagram.publish_post(image_url, caption)


# ------------------------------------------------------------ open apps

# Apps JAVIER can open ON THE IPHONE: the backend only prepares a link,
# the frontend shows a button and Nate's tap opens the app (iOS only
# allows opening apps after a user gesture - honest limit).
APP_LINKS = {
    "youtube": ("YouTube", "https://www.youtube.com/results?search_query={q}",
                "https://www.youtube.com"),
    "snapchat": ("Snapchat", None, "https://www.snapchat.com/"),
    "instagram": ("Instagram", "https://www.instagram.com/{q}/",
                  "https://www.instagram.com"),
    "tiktok": ("TikTok", "https://www.tiktok.com/search?q={q}",
               "https://www.tiktok.com"),
    "spotify": ("Spotify", "https://open.spotify.com/search/{q}",
                "https://open.spotify.com"),
    "shopify": ("Shopify Admin", None, "https://admin.shopify.com/"),
    "maps": ("Karten", "https://maps.apple.com/?q={q}",
             "https://maps.apple.com"),
    "mail": ("Mail", "mailto:{q}", "mailto:"),
}


def _load_custom_apps():
    # Nate's own apps from the APPS environment variable (set in Render),
    # same friendly format as CONTACTS: Migros=migros.ch, Bank=ubs.com
    # Custom URL schemes work too: Snap=snapchat://
    apps = {}
    for key, value in os.environ.items():
        if key.upper() == "APPS":
            for part in re.split(r"[,;\n]+", value):
                if "=" in part:
                    name, link = part.split("=", 1)
                    name, link = name.strip(), link.strip()
                    if name and link:
                        if "://" not in link:
                            link = "https://" + link
                        apps[name] = link
            break
    return apps


def open_app(app, query="", url=""):
    from urllib.parse import quote
    app = (app or "").lower()
    if app == "web":
        if not url:
            return {"error": "url wird fuer app=web benoetigt"}
        if not (url.startswith("https://") or url.startswith("http://")):
            url = "https://" + url
        return {
            "ok": True,
            "note": "Link vorbereitet. Nate sieht einen Button und tippt "
                    "selbst - iOS erlaubt kein automatisches Oeffnen.",
            "_frontend_action": {"type": "link", "label": "Webseite",
                                 "url": url},
        }
    if app not in APP_LINKS:
        custom = _load_custom_apps()
        for name, link in custom.items():
            if name.lower() == app:
                return {
                    "ok": True,
                    "note": "Link zu %s vorbereitet. Nate tippt selbst auf "
                            "den Button." % name,
                    "_frontend_action": {"type": "link", "label": name,
                                         "url": link},
                }
        return {"error": "Unbekannte App '%s'. Eingebaut: %s, web. "
                         "Eigene Apps: %s. Neue kann Nate in Render als "
                         "APPS-Variable anlegen (Name=URL, ...)."
                         % (app, ", ".join(APP_LINKS),
                            ", ".join(sorted(custom)) or "(keine)")}
    label, search_tpl, home = APP_LINKS[app]
    if query and search_tpl:
        link = search_tpl.replace("{q}", quote(query))
    else:
        link = home
    return {
        "ok": True,
        "note": "Link zu %s vorbereitet. Nate sieht jetzt einen Button "
                "und tippt selbst darauf - dann oeffnet sich die App auf "
                "dem iPhone." % label,
        "_frontend_action": {"type": "link", "label": label, "url": link},
    }


# ----------------------------------------------------- safe PC commands

SAFE_FOLDERS = {
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "dokumente": os.path.join(os.path.expanduser("~"), "Documents"),
    "bilder": os.path.join(os.path.expanduser("~"), "Pictures"),
    "ausgangskorb": OUTBOX_DIR,
}

SCREENSHOT_PS = (
    "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
    "$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
    "$img = New-Object System.Drawing.Bitmap $b.Width, $b.Height; "
    "$g = [System.Drawing.Graphics]::FromImage($img); "
    "$g.CopyFromScreen($b.Location, [System.Drawing.Point]::Empty, $b.Size); "
    "$img.Save('%s'); $g.Dispose(); $img.Dispose()"
)


def run_safe_command(action, target="downloads"):
    # Strict whitelist - no arbitrary shell execution. 'target' must be one
    # of the named SAFE_FOLDERS keys, never a raw path.
    _ensure_dirs()
    target = (target or "downloads").lower()
    if action in ("open_folder", "list_files") and target not in SAFE_FOLDERS:
        return {"error": "Unbekannter Ordner '%s'. Erlaubt: %s"
                         % (target, ", ".join(SAFE_FOLDERS))}

    if action == "open_folder":
        path = SAFE_FOLDERS[target]
        if sys.platform == "win32":
            subprocess.Popen(["explorer", path])
            return {"ok": True, "opened": path}
        return {"error": "open_folder ist nur unter Windows verfuegbar"}

    if action == "list_files":
        path = SAFE_FOLDERS[target]
        if not os.path.isdir(path):
            return {"error": "Ordner existiert nicht: %s" % path}
        entries = sorted(os.listdir(path))[:50]
        return {"folder": path, "entries": entries, "count": len(entries)}

    if action == "screenshot":
        if sys.platform != "win32":
            return {"error": "screenshot ist nur unter Windows verfuegbar"}
        out = os.path.join(
            SCREENSHOT_DIR,
            "screen_%s.png" % datetime.now().strftime("%Y%m%d_%H%M%S"))
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command",
                 SCREENSHOT_PS % out.replace("'", "''")],
                check=True, capture_output=True, timeout=30)
        except (subprocess.SubprocessError, OSError) as e:
            return {"error": "screenshot failed: %s" % e}
        return {"ok": True, "saved": out}

    return {"error": "Unbekannte Aktion '%s'. Erlaubt: open_folder, "
                     "list_files, screenshot" % action}


# --------------------------------------------------------- system status

def _next_event():
    # Nearest upcoming event (from now on), or None.
    now = datetime.now()
    upcoming = []
    for ev in _read_events():
        dt = _parse_dt(ev.get("DTSTART", ""))
        if dt and dt >= now:
            upcoming.append((dt, ev.get("SUMMARY", "(ohne Titel)")))
    if not upcoming:
        return None
    dt, summary = min(upcoming, key=lambda e: e[0])
    return {"summary": summary, "start": dt.isoformat(timespec="minutes")}


def get_system_status():
    # JARVIS-style read-only systems check: a single at-a-glance overview
    # of JAVIER's state and which integrations are wired up. No external
    # calls - fast and offline-safe.
    todos = _load_todos()
    open_todos = [t for t in todos if not t.get("done")]
    contacts = _load_contacts()
    custom_apps = _load_custom_apps()
    return {
        "time": datetime.now().isoformat(timespec="minutes"),
        "todos_open": len(open_todos),
        "todos_total": len(todos),
        "next_event": _next_event(),
        "contacts": len(contacts),
        "custom_apps": len(custom_apps),
        "integrations": {
            "shopify": bool(os.environ.get("SHOPIFY_STORE")) and
            bool(os.environ.get("SHOPIFY_ACCESS_TOKEN")),
            "instagram": instagram.is_configured(),
            "voice_elevenlabs": bool(os.environ.get("ELEVENLABS_API_KEY")) and
            bool(os.environ.get("ELEVENLABS_VOICE_ID")),
        },
    }


# ------------------------------------------------------ tool definitions

def tool_definitions():
    tools = [
        {
            "name": "manage_todos",
            "description": "Nates Todo-Liste verwalten: Eintrag anlegen, "
                           "alle auflisten, abhaken oder loeschen. Lokale "
                           "JSON-Datei auf dem PC.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                               "enum": ["add", "list", "complete", "delete"]},
                    "text": {"type": "string",
                             "description": "Text des Todos (bei add)"},
                    "todo_id": {"type": "integer",
                                "description": "ID (bei complete/delete)"},
                },
                "required": ["action"],
            },
        },
        {
            "name": "read_calendar",
            "description": "Nates Termine der naechsten Tage aus der lokalen "
                           "ICS-Kalenderdatei lesen.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer",
                             "description": "Zeitraum in Tagen (Standard 7)"},
                },
            },
        },
        {
            "name": "add_event",
            "description": "Einen Termin in Nates lokalen ICS-Kalender "
                           "eintragen.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "date": {"type": "string", "description": "YYYY-MM-DD"},
                    "time": {"type": "string", "description": "HH:MM, Standard 09:00"},
                    "duration_minutes": {"type": "integer", "description": "Standard 60"},
                    "location": {"type": "string"},
                },
                "required": ["title", "date"],
            },
        },
        {
            "name": "get_weather",
            "description": "Aktuelles Wetter und 3-Tage-Prognose fuer "
                           "Rapperswil-Jona (Open-Meteo).",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_system_status",
            "description": "JAVIERs eigener Statusbericht (Systemcheck): "
                           "offene Todos, naechster Termin, Anzahl Kontakte "
                           "und eigener Apps sowie welche Integrationen "
                           "(Shopify, Instagram, eigene Stimme) aktiv sind. "
                           "Read-only, keine externen Abfragen. Ideal bei "
                           "Fragen wie 'Statusbericht' oder 'Wie ist der "
                           "Stand?'.",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "get_shopify_status",
            "description": "Read-only Status des MeowUfo-Shopify-Shops: "
                           "Bestellungen und Umsatz der letzten Tage.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer",
                             "description": "Zeitraum in Tagen (Standard 7)"},
                },
            },
        },
        {
            "name": "list_contacts",
            "description": "Auflisten, welche Kontakte JAVIER fuer "
                           "Nachrichten kennt (nur Namen, keine Nummern).",
            "input_schema": {"type": "object", "properties": {}},
        },
        {
            "name": "prepare_message",
            "description": "Eine SMS- oder WhatsApp-Nachricht an einen "
                           "Kontakt aus contacts.json VORBEREITEN. Es wird "
                           "nur ein Link mit vorbefuelltem Text erzeugt - "
                           "Nate muss selbst auf Senden tippen. Vorher immer "
                           "Nates Bestaetigung einholen.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "contact_name": {"type": "string",
                                     "description": "Name wie in contacts.json, z.B. Mutter"},
                    "message": {"type": "string"},
                    "channel": {"type": "string", "enum": ["sms", "whatsapp"],
                                "description": "Standard whatsapp"},
                },
                "required": ["contact_name", "message"],
            },
        },
        {
            "name": "prepare_instagram_post",
            "description": "Instagram-Post fuer MeowUfo VORBEREITEN: Caption "
                           "(und optional Bild) in den Ausgangskorb-Ordner "
                           "legen. Veroeffentlicht NICHTS.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "caption": {"type": "string"},
                    "image_path": {"type": "string",
                                   "description": "Optionaler lokaler Bildpfad"},
                },
                "required": ["caption"],
            },
        },
        {
            "name": "open_app",
            "description": "Eine App oder Webseite auf Nates iPhone "
                           "OEFFNEN. Eingebaut: youtube, snapchat, "
                           "instagram, tiktok, spotify, shopify, maps, "
                           "mail, web (mit URL). Zusaetzlich alle Apps, "
                           "die Nate in der APPS-Umgebungsvariable "
                           "definiert hat - bei unbekanntem Namen einfach "
                           "aufrufen, die Fehlermeldung listet die "
                           "verfuegbaren. Optional mit Suchbegriff. Es "
                           "wird ein Button angezeigt - Nate tippt selbst.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "app": {"type": "string",
                            "description": "App-Name, z.B. youtube oder "
                                           "ein eigener Name aus APPS"},
                    "query": {"type": "string",
                              "description": "Suchbegriff/Profilname "
                                             "(optional)"},
                    "url": {"type": "string",
                            "description": "Volle URL (nur bei app=web)"},
                },
                "required": ["app"],
            },
        },
        {
            "name": "run_safe_command",
            "description": "Eine harmlose PC-Aktion aus einer festen "
                           "Whitelist ausfuehren: open_folder, list_files "
                           "(erlaubte Ordner: downloads, desktop, dokumente, "
                           "bilder, ausgangskorb) oder screenshot.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                               "enum": ["open_folder", "list_files", "screenshot"]},
                    "target": {"type": "string",
                               "description": "Ordnername aus der Whitelist"},
                },
                "required": ["action"],
            },
        },
    ]
    if instagram.is_configured():
        tools.append({
            "name": "publish_instagram_post",
            "description": "Einen Post WIRKLICH auf dem MeowUfo-Instagram-"
                           "Account veroeffentlichen (Graph API). Das Bild "
                           "muss auf einer oeffentlich erreichbaren URL "
                           "liegen. Irreversibel - vorher IMMER Nates "
                           "ausdrueckliche Bestaetigung einholen.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "image_url": {"type": "string",
                                  "description": "Oeffentliche HTTPS-Bild-URL"},
                    "caption": {"type": "string"},
                },
                "required": ["image_url", "caption"],
            },
        })
    return tools


TOOL_FUNCTIONS = {
    "manage_todos": manage_todos,
    "read_calendar": read_calendar,
    "add_event": add_event,
    "get_weather": get_weather,
    "get_system_status": get_system_status,
    "get_shopify_status": get_shopify_status,
    "list_contacts": list_contacts,
    "prepare_message": prepare_message,
    "prepare_instagram_post": prepare_instagram_post,
    "publish_instagram_post": publish_instagram_post,
    "open_app": open_app,
    "run_safe_command": run_safe_command,
}


def execute_tool(name, tool_input):
    fn = TOOL_FUNCTIONS.get(name)
    if not fn:
        return {"error": "unknown tool: %s" % name}
    try:
        return fn(**tool_input)
    except TypeError as e:
        return {"error": "bad arguments for %s: %s" % (name, e)}
    except Exception as e:
        return {"error": "%s failed: %s" % (name, e)}
