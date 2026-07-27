"""Server-seitiges Web-Lese-Werkzeug fuer den Chat (`web_fetch`): liest den
Text einer oeffentlichen Webseite, damit das Modell z.B. "was steht auf
https://... " beantworten kann.

NICHT im Scope (bewusst): kein Login, keine Formulare, keine Aktionen mit
Nebeneffekten auf fremden Seiten, kein Browser, kein Klicken -- nur ein
HTTP-GET auf eine oeffentliche URL und grobe Text-Extraktion.

SICHERHEITSKRITISCH: `url` kommt vom Modell/Nutzer und loest einen
server-seitigen Request in einer Multi-Tenant-Umgebung aus -- klassisches
SSRF-Risiko (u.a. Cloud-Metadata-Endpunkt 169.254.169.254, internes Netz,
localhost). ALLE Pruefungen in `check_url_is_safe` MUESSEN greifen, bevor
irgendein Netzwerk-Request gemacht wird -- inklusive bei jedem Redirect-Hop
erneut, sonst kann ein Redirect die Sperre umgehen.

DNS-Rebinding ist strukturell ausgeschlossen, nicht nur geprueft: der
Hostname wird pro Hop GENAU EINMAL aufgeloest (`check_url_is_safe` gibt die
validierte IP zurueck), und der tatsaechliche Request verbindet sich DIREKT
zu dieser IP (`httpx.URL.copy_with(host=<ip>)`) -- httpx bekommt dadurch nie
die Chance, den Hostnamen ein zweites Mal, unabhaengig aufzuloesen (die
klassische Rebinding-Luecke: Pruefung sieht eine oeffentliche IP, der
eigentliche Connect eine zweite, unabhaengige Antwort mit z.B.
169.254.169.254). Damit HTTPS (SNI + Zertifikatspruefung) und namensbasiertes
virtuelles Hosting trotz IP-Connect korrekt bleiben, werden `Host`-Header und
TLS-SNI (`extensions={"sni_hostname": ...}`, von httpx/httpcore 0.28
unterstuetzt) weiterhin auf den ORIGINAL-Hostnamen gesetzt -- nur die
Socket-Verbindung selbst geht gegen die geprueften IP. Verifiziert gegen
einen lokalen HTTPS-Server mit selbstsigniertem Zertifikat (Connect per IP,
Zertifikatspruefung greift trotzdem korrekt gegen den Hostnamen; ohne
SNI/Host-Override schlaegt dieselbe Verbindung nachweislich mit einem
Hostname-Mismatch fehl -- siehe PR-Beschreibung/README).

Die DNS-Aufloesung selbst laeuft NICHT blockierend im Event-Loop: sie wird
per `run_in_executor` in einen Thread ausgelagert und mit
`asyncio.wait_for(timeout=DNS_RESOLVE_TIMEOUT_S)` begrenzt, damit ein
absichtlich haengender/nicht antwortender Nameserver nicht den gesamten
Worker-Prozess (und damit alle gleichzeitig bedienten Mandanten) blockiert,
sondern nach spaetestens ein paar Sekunden mit einem klaren Fehler abbricht.
Restrisiko (dokumentiert, nicht versteckt): der ausgelagerte Thread selbst
laesst sich nicht hart abbrechen, er laeuft im Hintergrund weiter, bis der
Resolver selbst aufgibt -- bei sehr vielen gleichzeitigen, absichtlich
haengenden Lookups kann das den Default-Executor-Threadpool auf Dauer
belegen. Fuer den Event-Loop (das eigentliche HOCH-Risiko: ALLE Mandanten
blockiert) ist das Problem damit geloest.
"""
from __future__ import annotations

import asyncio
import ipaddress
import logging
import re
import socket

import httpx

log = logging.getLogger("platform.web_fetch_tool")

ALLOWED_SCHEMES = {"http", "https"}
MAX_REDIRECTS = 3
MAX_RESPONSE_BYTES = 2_000_000
REQUEST_TIMEOUT_S = 8.0
MAX_RESULT_CHARS = 6000
# Obergrenze fuer die (in einen Thread ausgelagerte) DNS-Aufloesung -- ein
# absichtlich nicht antwortender Nameserver darf den Request nicht laenger
# als das haengen lassen (siehe Moduldoc: blockierender-DNS-Call-Fix).
DNS_RESOLVE_TIMEOUT_S = 3.0

# OpenAI-kompatibles Function-Calling-Schema, wird 1:1 in payload["tools"]
# gereicht (siehe completions.run_chat).
WEB_FETCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": (
            "Ruft den lesbaren Text einer oeffentlichen Webseite ab (nur "
            "http/https, keine privaten/internen Adressen, kein Login, keine "
            "Formulare). Nuetzlich um den Inhalt einer vom Nutzer genannten "
            "URL zu lesen und in die Antwort einzubeziehen."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Die vollstaendige URL (http:// oder https://), die gelesen werden soll.",
                }
            },
            "required": ["url"],
        },
    },
}

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


class UnsafeUrlError(Exception):
    """Eine URL, die eine der SSRF-Pflicht-Pruefungen nicht besteht."""


async def _ensure_public_host(hostname: str) -> str:
    """Loest `hostname` GENAU EINMAL per DNS auf (in einem Executor-Thread,
    mit `DNS_RESOLVE_TIMEOUT_S`-Timeout, damit ein haengender Resolver nicht
    den Event-Loop blockiert -- siehe Moduldoc) und lehnt ab, wenn AUCH NUR
    EINE aufgeloeste Adresse privat/loopback/link-local/multicast/reserviert/
    unspezifiziert ist. Blockt u.a. 127.0.0.1, 169.254.169.254
    (Cloud-Metadata), 10.x/172.16-31.x/192.168.x, ::1 -- sowie deren
    alternative Schreibweisen (Dezimal/Hex/verkuerzte IPv4, IPv4-mapped
    IPv6), weil hier die vom Betriebssystem AUFGELOESTE Adresse klassifiziert
    wird, nicht der rohe Hostname-Text.

    Gibt die ERSTE aufgeloeste, als oeffentlich validierte Adresse zurueck --
    genau diese (und keine andere, spaeter erneut aufgeloeste) IP wird fuer
    den tatsaechlichen Request verwendet (DNS-Rebinding-Haertung, siehe
    Moduldoc)."""
    loop = asyncio.get_running_loop()
    try:
        infos = await asyncio.wait_for(
            loop.run_in_executor(None, socket.getaddrinfo, hostname, None),
            timeout=DNS_RESOLVE_TIMEOUT_S,
        )
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Hostname kann nicht aufgeloest werden: {exc}") from exc
    except TimeoutError as exc:
        raise UnsafeUrlError(
            f"Hostname-Aufloesung hat laenger als {DNS_RESOLVE_TIMEOUT_S}s gedauert"
        ) from exc
    if not infos:
        raise UnsafeUrlError("Hostname liefert keine Adresse")
    pinned_ip: str | None = None
    for _family, _type, _proto, _canonname, sockaddr in infos:
        ip_str = sockaddr[0]
        addr = ipaddress.ip_address(ip_str)
        if (
            addr.is_private
            or addr.is_loopback
            or addr.is_link_local
            or addr.is_multicast
            or addr.is_reserved
            or addr.is_unspecified
        ):
            raise UnsafeUrlError(f"Adresse '{ip_str}' ist nicht oeffentlich erreichbar")
        if pinned_ip is None:
            pinned_ip = ip_str
    assert pinned_ip is not None  # infos war nicht leer, also mind. eine Iteration
    return pinned_ip


async def check_url_is_safe(url: str) -> tuple[str, str]:
    """Wirft `UnsafeUrlError`, wenn `url` eine der Pflicht-Pruefungen nicht
    besteht (Schema, aufgeloeste IP). Macht sonst GENAU EINEN DNS-Lookup und
    gibt `(host, pinned_ip)` zurueck: `host` ist der Original-Hostname (fuer
    Host-Header/TLS-SNI), `pinned_ip` die validierte, oeffentliche Adresse,
    zu der der tatsaechliche Request verbunden werden MUSS -- niemals ein
    zweites Mal ueber den Hostnamen aufloesen (siehe Moduldoc,
    DNS-Rebinding)."""
    try:
        parsed = httpx.URL(url)
    except Exception as exc:  # ungueltige URL jeder Art
        raise UnsafeUrlError(f"Ungueltige URL: {exc}") from exc
    scheme = parsed.scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"Schema '{scheme}' nicht erlaubt (nur http/https)")
    host = parsed.host
    if not host:
        raise UnsafeUrlError("URL ohne Hostname")
    pinned_ip = await _ensure_public_host(host)
    return host, pinned_ip


def _strip_html(html: str) -> str:
    text = _TAG_RE.sub(" ", html)
    text = _WS_RE.sub(" ", text).strip()
    return text[:MAX_RESULT_CHARS]


async def _fetch_one_hop(client: httpx.AsyncClient, url: str) -> tuple[int, httpx.Headers, str]:
    """Prueft die URL erneut (Pflicht bei jedem Hop, auch dem ersten) und holt
    hoechstens MAX_RESPONSE_BYTES per gestreamtem Read.

    Verbindet sich DIREKT zur bei der Pruefung ermittelten, validierten IP
    (`copy_with(host=pinned_ip)`) statt zum Hostnamen -- httpx macht dadurch
    KEINE eigene, zweite DNS-Aufloesung mehr (strukturelle
    DNS-Rebinding-Haertung, siehe Moduldoc). `Host`-Header und TLS-SNI
    bleiben der Original-Hostname, damit HTTPS-Zertifikatspruefung und
    namensbasiertes virtuelles Hosting trotzdem korrekt funktionieren."""
    parsed = httpx.URL(url)
    original_host, pinned_ip = await check_url_is_safe(url)
    ip_url = parsed.copy_with(host=pinned_ip)
    headers = {"Host": original_host}
    extensions = {"sni_hostname": original_host} if parsed.scheme.lower() == "https" else {}
    async with client.stream("GET", ip_url, headers=headers, extensions=extensions) as resp:
        chunks: list[bytes] = []
        total = 0
        async for chunk in resp.aiter_bytes():
            total += len(chunk)
            if total > MAX_RESPONSE_BYTES:
                break
            chunks.append(chunk)
        body = b"".join(chunks)
        encoding = resp.encoding or "utf-8"
        text = body.decode(encoding, errors="replace")
        return resp.status_code, resp.headers, text


async def web_fetch(url: str) -> str:
    """Fuehrt den eigentlichen Abruf aus und gibt IMMER einen String zurueck
    (nie eine Exception nach aussen) -- Fehler jeder Art (Sicherheits-
    Ablehnung, DNS-Fehler, Timeout, HTTP-Fehler) werden als klarer
    Fehlertext zurueckgegeben, damit ein einzelner Tool-Aufruf nie die ganze
    Chat-Anfrage zum Absturz bringt."""
    current_url = url
    try:
        async with httpx.AsyncClient(
            timeout=REQUEST_TIMEOUT_S, follow_redirects=False
        ) as client:
            for hop in range(MAX_REDIRECTS + 1):
                status, headers, text = await _fetch_one_hop(client, current_url)
                if 300 <= status < 400:
                    location = headers.get("location")
                    if not location:
                        return "Fehler: Weiterleitung ohne Ziel-Adresse."
                    if hop == MAX_REDIRECTS:
                        return "Fehler: Zu viele Weiterleitungen."
                    current_url = str(httpx.URL(current_url).join(location))
                    continue
                if status >= 400:
                    return f"Fehler: Die Seite antwortete mit Status {status}."
                return _strip_html(text) or "(Seite enthielt keinen lesbaren Text.)"
        return "Fehler: Zu viele Weiterleitungen."
    except UnsafeUrlError as exc:
        log.info("web_fetch abgelehnt (SSRF-Schutz): %s", exc)
        return "Fehler: Diese Adresse kann nicht abgerufen werden."
    except httpx.TimeoutException:
        log.info("web_fetch Timeout fuer %s", current_url)
        return "Fehler: Diese Adresse kann nicht abgerufen werden."
    except httpx.HTTPError as exc:
        log.info("web_fetch HTTP-Fehler fuer %s: %s", current_url, exc)
        return "Fehler: Diese Adresse kann nicht abgerufen werden."
    except Exception as exc:  # noqa: BLE001 -- ein Tool-Ergebnis darf nie crashen
        log.warning("web_fetch unerwarteter Fehler fuer %s: %s", current_url, exc)
        return "Fehler: Diese Adresse kann nicht abgerufen werden."
