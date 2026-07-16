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
# Füllwörter am Anfang des Ziels entfernen (auch wenn sie das GANZE Ziel sind,
# z. B. "öffne mir" -> Ziel wird leer -> geht ans Gehirn statt kaputt an pc)
_FILLER = re.compile(r"^(?:mir|bitte|das|die|der|den|dem|ein|eine|einen|mal|doch|jetzt)(?:\s+|$)",
                     re.IGNORECASE)


def _strip_filler(t: str) -> str:
    prev = None
    while prev != t:
        prev = t
        t = _FILLER.sub("", t).strip()
    return t


# Weckwort am Anfang entfernen: "hey jarvis", "ok jarvis", "hallo jarvis",
# "jarvis," ... So wird "hey jarvis öffne youtube" wirklich als Befehl erkannt
# (früher fiel alles mit "hey jarvis"-Vorsatz durch und landete nur im Chat).
_WAKE = re.compile(
    r"^\s*(?:hey|hi|hallo|halo|ok|okay|okey|yo|he)?\s*jarvis\b[\s,:.!-]*",
    re.IGNORECASE)


def _strip_wake(t: str) -> str:
    return _WAKE.sub("", t).strip()


# YouTube: "spiel/play/zeig … auf youtube" ODER "spiel mir ein video/lied/song …".
# Bewusst eng gehalten, damit normale Fragen NICHT als YouTube-Befehl enden.
_YT_VERB = r"(?:spiel(?:e|\s+mir|\s+doch)?|spiel\s+ab|play|zeig(?:e|\s+mir)?|abspielen)"
_YT_ON = re.compile(
    rf"^(?:bitte\s+)?{_YT_VERB}\s+(.+?)\s+(?:auf|bei|in|über|ueber)\s+"
    r"(?:youtube|yt|dem\s+youtube)(?:\s+ab)?[.!?]?$", re.IGNORECASE)
_YT_MEDIA = re.compile(
    rf"^(?:bitte\s+)?{_YT_VERB}\s+(?:mir\s+)?(?:ein(?:en)?\s+|das\s+|die\s+|den\s+)?"
    r"(?:video|lied|song|musik(?:video)?|clip|film|trailer)\s+"
    r"(?:von|über|ueber|zu|mit|namens|über\s+)?\s*(.+?)[.!?]?$", re.IGNORECASE)


def _youtube_url(query: str) -> str:
    """YouTube-Suche, die das erste Ergebnis automatisch abspielt."""
    import urllib.parse
    q = urllib.parse.quote_plus(query.strip().strip("\"'"))
    return "https://www.youtube.com/results?search_query=" + q
_CLOSE = re.compile(
    r"^(?:bitte\s+)?(?:schließe|schliesse|beende|schließ|close|kill|stopp(?:e)?)\s+"
    r"(?:das\s+|die\s+|den\s+)?(.+?)[.!?]?$", re.IGNORECASE)
_SHOT = re.compile(r"(screenshot|bildschirmfoto|bildschirm\s*foto|mach.*bildschirm)", re.IGNORECASE)
# "finde …" ist absichtlich NICHT dabei — zu breit (z. B. "finde den Fehler im Code"
# soll ans Gehirn, nicht in die Websuche). Nur klare Such-Verben lösen eine Suche aus.
_SEARCH = re.compile(
    r"^(?:bitte\s+)?(?:suche|such|google|recherchiere)\s+(?:nach\s+|im internet\s+)?(.+?)[.!?]?$",
    re.IGNORECASE)


def _resolve_open(target: str) -> str | None:
    """Löst ein Öffnen-Ziel zu Seite/Programm/URL auf ODER gibt None zurück.

    None = das Ziel ist KEIN erkennbares Programm/keine Seite (z. B. „die Analyse
    des Quartalsberichts"). Dann darf die Aufgabe NICHT auf das gesperrte
    pc-Plugin gemappt werden, sondern geht ans Gehirn.
    """
    t = target.strip().strip("\"'").lower()
    if t in SITES:
        return SITES[t]
    if t in PROGRAMS:
        return PROGRAMS[t]
    if t.startswith(("http://", "https://")):
        return target.strip()
    if "." in t and " " not in t:                 # sieht nach Domain aus (youtube.com)
        return "https://" + t
    if " punkt " in t or t.endswith(" com") or t.endswith(" de"):
        dom = t.replace(" punkt ", ".").replace(" com", ".com").replace(" de", ".de").replace(" ", "")
        return "https://" + dom
    if " " not in t and t.isascii() and t.isalnum():  # einzelnes Wort -> Programmname versuchen
        return target.strip()
    return None                                    # freier Text -> ans Gehirn, nicht ans pc-Plugin


def _target_to_open(target: str) -> str:
    """Wie _resolve_open, aber mit Fallback auf den Rohtext (für Browser-Navigation)."""
    return _resolve_open(target) or target.strip()


def interpret(text: str) -> str | None:
    """Gibt einen `!plugin ...`-Befehl zurück oder None, wenn kein Kommando erkannt."""
    s = text.strip()
    if not s or s.startswith("!"):
        return None
    # Weckwort "hey jarvis" / "jarvis," am Anfang entfernen, sonst wird der
    # eigentliche Befehl nicht erkannt und alles landet nur im Chat.
    s = _strip_wake(s)
    if not s:
        return None

    # --- YouTube: Video/Song wirklich abspielen (Browser öffnet & spielt ab) ---
    myt = _YT_ON.match(s) or _YT_MEDIA.match(s)
    if myt:
        ziel = _strip_filler(myt.group(1)).strip()
        if ziel:
            return f"!plugin pc open program={_youtube_url(ziel)}"

    # Claw Code / Claude Code als Werkzeug: "claw code <prompt>", "clawcode <prompt>", "claude code <prompt>"
    mcc = re.match(r"^(?:bitte\s+)?(?:claw\s?code|clawcode|claude\s?code|claw)\s*[:,]?\s+(.+)$",
                   s, re.IGNORECASE)
    if mcc:
        return f"!plugin code prompt prompt={mcc.group(1).strip()}"

    # Multi-Modell (OpenRouter): mehrere Modelle vergleichen
    mcmp = re.match(r"^(?:bitte\s+)?(?:vergleiche?\s+(?:die\s+)?modelle?|modell[- ]?vergleich)"
                    r"\s*[:,]?\s+(.+)$", s, re.IGNORECASE)
    if mcmp:
        return f"!plugin modelle vergleich prompt={mcmp.group(1).strip()}"
    # Ein bestimmtes Modell fragen: "modell gpt: <prompt>", "frag(e) gemini <prompt>"
    mmod = re.match(r"^(?:bitte\s+)?(?:modell|frag(?:e)?\s+(?:das\s+modell\s+)?)"
                    r"\s*([a-zA-Z0-9._-]+)\s*[:,]\s+(.+)$", s, re.IGNORECASE)
    if mmod:
        return (f"!plugin modelle frage model={mmod.group(1).strip()} "
                f"prompt={mmod.group(2).strip()}")

    # Bildschirm-Verstehen (Vision): "was ist auf dem bildschirm", "was siehst du", "analysiere den bildschirm"
    if re.search(r"was\s+(ist|siehst\s+du|steht)\s+.*(bildschirm|screen|bild)|"
                 r"analysiere\s+(den\s+)?(bildschirm|screen)|"
                 r"(schau|sieh)\s+(dir\s+)?(den\s+)?bildschirm|was\s+siehst\s+du",
                 s, re.IGNORECASE):
        return "!plugin pc sehen"
    if _SHOT.search(s) and re.search(r"\b(mach|nimm|erstell|screenshot|foto)\b", s, re.IGNORECASE):
        return "!plugin pc screenshot"

    # --- Einloggen auf Plattformen (mit hinterlegten Zugangsdaten) ---
    # "logge dich überall / bei allen ein" -> alle hinterlegten Konten
    if re.match(r"^(?:bitte\s+)?(?:logg?e?\s+dich|melde\s+dich|login|einloggen|anmelden)"
                r"\s+(?:bitte\s+)?(?:überall|ueberall|bei\s+allen?|in\s+alle[sn]?|"
                r"auf\s+allen?)(?:\s+(?:konten|accounts?|plattformen|ein|an))?[.!?]?$",
                s, re.IGNORECASE):
        return "!plugin browser_auto login plattform=alle"
    mlogin = re.match(
        r"^(?:bitte\s+)?(?:logg?e?\s+dich|melde\s+dich|log\s+in|login|einloggen|anmelden)"
        r"\s+(?:bitte\s+)?(?:bei|in|auf|at|to|in\s+mein[a-z]*)\s+"
        r"(?:mein[a-z]*\s+)?(.+?)(?:\s+(?:ein|an|account|konto|profil))?[.!?]?$",
        s, re.IGNORECASE)
    if mlogin:
        plat = _strip_filler(mlogin.group(1)).strip().strip("\"'").lower()
        # 'youtube.com' -> 'youtube', 'www.instagram.com' -> 'instagram'
        plat = re.sub(r"^(?:www\.)|\.(?:com|de|net|org|tv)$", "", plat).strip()
        if plat:
            return f"!plugin browser_auto login plattform={plat}"

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
        target = _resolve_open(raw)
        if target:                          # nur echte Programme/Seiten ans pc-Plugin
            return f"!plugin pc open program={target}"
        # sonst: freier Text ("starte die Analyse …") -> weiter, endet am Gehirn

    m = _CLOSE.match(s)
    if m:
        name = m.group(1).strip()
        low = name.lower()
        # Nur schließen, wenn es ein bekanntes Programm / ein Browser / eine .exe ist —
        # "beende die Diskussion" darf NICHT das pc-Plugin ansteuern.
        if low in PROGRAMS or low in BROWSERS or low.endswith(".exe"):
            prog = PROGRAMS.get(low, name)
            if not prog.lower().endswith(".exe") and "/" not in prog and ":" not in prog:
                prog = prog + ".exe"
            return f"!plugin pc close name={prog}"
        # sonst: freier Text -> ans Gehirn

    m = _SEARCH.match(s)
    if m:
        return f"!plugin web suche query={m.group(1).strip()}"

    return None
