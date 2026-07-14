"""Befehlsversteher: übersetzt natürliche Sprache in echte Werkzeug-Aktionen.

Damit „öffne YouTube" (im Chat oder per Sprache) wirklich YouTube öffnet,
statt nur eine Textantwort zu erzeugen. Erkennt gängige deutsche (und ein
paar englische) Kommandos und bildet sie auf `!plugin pc ...` bzw.
`!plugin web ...` ab. Wird KEIN Kommando erkannt, gibt der Parser None
zurück und die Aufgabe geht wie bisher ans Gehirn.

Sicherheit: Die erzeugten Aktionen laufen durch den normalen Plugin-Gate —
PC-Steuerung bleibt gesperrt, bis JARVIS_ALLOW_PC=1 gesetzt ist.
"""

from __future__ import annotations

import re

# Bekannte Webseiten -> URL
SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "google mail": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "chatgpt": "https://chat.openai.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.de",
    "wikipedia": "https://de.wikipedia.org",
    "spotify": "https://open.spotify.com",
    "twitch": "https://www.twitch.tv",
    "github": "https://github.com",
    "reddit": "https://www.reddit.com",
    "x": "https://x.com",
    "twitter": "https://x.com",
    "tiktok": "https://www.tiktok.com",
    "linkedin": "https://www.linkedin.com",
    "outlook": "https://outlook.live.com",
}

# Umgangssprachliche Programmnamen -> echter Programmname
PROGRAMS = {
    "rechner": "calc", "taschenrechner": "calc", "calculator": "calc",
    "editor": "notepad", "notizblock": "notepad", "notepad": "notepad",
    "paint": "mspaint", "explorer": "explorer", "datei explorer": "explorer",
    "dateimanager": "explorer", "browser": "https://www.google.com",
    "einstellungen": "ms-settings:", "systemsteuerung": "control",
    "aufgabenmanager": "taskmgr", "task manager": "taskmgr",
    "cmd": "cmd", "eingabeaufforderung": "cmd", "word": "winword", "excel": "excel",
    "chrome": "chrome", "google chrome": "chrome", "firefox": "firefox",
    "edge": "msedge", "microsoft edge": "msedge", "brave": "brave", "opera": "opera",
}

BROWSERS = {"chrome", "google chrome", "firefox", "edge", "microsoft edge",
            "brave", "opera", "vivaldi"}

# "mach X auf" — Ziel steht zwischen mach und auf
_OPEN_MACH = re.compile(r"^(?:bitte\s+)?mach\s+(?:mir\s+)?(.+?)\s+auf[.!?]?$", re.IGNORECASE)
# "öffne/starte/... X"
_OPEN = re.compile(
    r"^(?:bitte\s+)?(?:öffne|oeffne|starte|start|zeig(?:e|\s+mir)?|"
    r"geh(?:e)?\s+auf|open|launch)\s+(.+?)(?:\s+(?:auf|bitte|für mich))?[.!?]?$",
    re.IGNORECASE)
# Füllwörter am Anfang des Ziels entfernen
_FILLER = re.compile(r"^(?:mir|bitte|das|die|der|den|dem|ein|eine|einen|mal|doch|jetzt)\s+",
                     re.IGNORECASE)


def _strip_filler(t: str) -> str:
    prev = None
    while prev != t:
        prev = t
        t = _FILLER.sub("", t).strip()
    return t
_CLOSE = re.compile(
    r"^(?:bitte\s+)?(?:schließe|schliesse|beende|schließ|close|kill|stopp(?:e)?)\s+"
    r"(?:das\s+|die\s+|den\s+)?(.+?)[.!?]?$", re.IGNORECASE)
_SHOT = re.compile(r"(screenshot|bildschirmfoto|bildschirm\s*foto|mach.*bildschirm)", re.IGNORECASE)
_SEARCH = re.compile(
    r"^(?:bitte\s+)?(?:suche|such|google|recherchiere|find(?:e)?)\s+(?:nach\s+|im internet\s+)?(.+?)[.!?]?$",
    re.IGNORECASE)


def _target_to_open(target: str) -> str:
    t = target.strip().strip("\"'").lower()
    # bekannte Seite?
    if t in SITES:
        return SITES[t]
    # bekanntes Programm?
    if t in PROGRAMS:
        return PROGRAMS[t]
    # sieht nach Domain/URL aus?
    if t.startswith(("http://", "https://")):
        return target.strip()
    if "." in t and " " not in t:
        return "https://" + t
    if " punkt " in t or t.endswith(" com") or t.endswith(" de"):
        dom = t.replace(" punkt ", ".").replace(" com", ".com").replace(" de", ".de").replace(" ", "")
        return "https://" + dom
    # sonst: als Programmname versuchen (Original beibehalten)
    return target.strip()


def interpret(text: str) -> str | None:
    """Gibt einen `!plugin ...`-Befehl zurück oder None, wenn kein Kommando erkannt."""
    s = text.strip()
    if not s or s.startswith("!"):
        return None

    if _SHOT.search(s) and re.search(r"\b(mach|nimm|erstell|screenshot|foto)\b", s, re.IGNORECASE):
        return "!plugin pc screenshot"

    # --- Browser-Automatisierung (JARVIS steuert den Browser selbst) ---
    mnav = re.match(r"^(?:bitte\s+)?(?:navigiere|surfe|browse|geh(?:e)?\s+im\s+browser)"
                    r"\s+(?:zu|auf|nach)\s+(.+?)[.!?]?$", s, re.IGNORECASE)
    if mnav:
        return f"!plugin browser_auto goto url={_target_to_open(_strip_filler(mnav.group(1)))}"
    if re.search(r"(lies|lese|zeig(?:e)?\s+mir)\s+(?:die\s+)?(web)?seite|was\s+steht\s+auf\s+der\s+seite",
                 s, re.IGNORECASE):
        return "!plugin browser_auto read"
    if re.search(r"(welche|zeig(?:e)?\s+mir\s+die|liste?\s+die)\s+links", s, re.IGNORECASE):
        return "!plugin browser_auto links"
    mbc = re.match(r"^(?:bitte\s+)?(?:im\s+browser\s+)?klicke?\s+(?:im\s+browser\s+)?"
                   r"(?:auf\s+)?(.+?)[.!?]?$", s, re.IGNORECASE)
    if mbc and "browser" in s.lower():
        return f"!plugin browser_auto click ziel=text={mbc.group(1).strip()}"

    # "öffne <seite> in/mit/im <browser>"  bzw. "öffne <browser> mit <seite>"
    mb = re.match(r"^(?:bitte\s+)?(?:öffne|oeffne|starte|zeig(?:e|\s+mir)?|open)\s+(.+?)"
                  r"\s+(?:in|mit|im|auf)\s+(.+?)[.!?]?$", s, re.IGNORECASE)
    if mb:
        a, b = _strip_filler(mb.group(1)).strip().lower(), mb.group(2).strip().lower()
        site, browser = (None, None)
        if b in BROWSERS:        # "youtube in chrome"
            site, browser = a, b
        elif a in BROWSERS:      # "chrome mit youtube"
            site, browser = b, a
        if browser:
            url = SITES.get(site, "")
            if not url and site:
                url = _target_to_open(site)
                if not url.startswith("http"):
                    url = "https://www.google.com/search?q=" + site.replace(" ", "+")
            return f"!plugin pc browser browser={browser} url={url}"

    m = _OPEN_MACH.match(s) or _OPEN.match(s)
    if m:
        raw = _strip_filler(m.group(1)).strip()
        if raw.lower() in BROWSERS:        # "öffne chrome" → Browser starten
            return f"!plugin pc browser browser={raw.lower()}"
        target = _target_to_open(raw)
        return f"!plugin pc open program={target}"

    m = _CLOSE.match(s)
    if m:
        name = m.group(1).strip()
        # Programmnamen normalisieren (rechner -> calc.exe etc.)
        prog = PROGRAMS.get(name.lower(), name)
        if not prog.lower().endswith(".exe") and "/" not in prog and ":" not in prog:
            prog = prog + ".exe"
        return f"!plugin pc close name={prog}"

    m = _SEARCH.match(s)
    if m:
        return f"!plugin web suche query={m.group(1).strip()}"

    return None
