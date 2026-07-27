"""Pflicht-Tests fuer die SSRF-Absicherung des web_fetch-Chat-Werkzeugs
(app/web_fetch_tool.py). Das Wichtigste in dieser Datei: `check_url_is_safe`
wird ISOLIERT getestet (kein echter Netzwerk-Request noetig) -- die Pruefung
muss VOR jedem Request greifen, nicht nur "meistens" funktionieren.
"""
from __future__ import annotations

import asyncio
import ipaddress
import socket

import httpx
import pytest

from app.web_fetch_tool import UnsafeUrlError, check_url_is_safe, web_fetch

UNSAFE_URLS = [
    "http://127.0.0.1/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/",
    "http://[::1]/",
    "file:///etc/passwd",
]

# Bekannte Bypass-Schreibweisen fuer 127.0.0.1 bzw. 169.254.169.254 (siehe
# Sicherheitsreview, Punkt 3): der glibc-Resolver loest sie alle auf die
# gleiche numerische Adresse auf wie die "normale" Schreibweise -- die
# Pruefung klassifiziert die AUFGELOESTE sockaddr, nicht den rohen
# Hostname-Text, und muss deshalb auch diese Formen ablehnen.
KNOWN_BYPASS_URLS = [
    "http://[::ffff:127.0.0.1]/",  # IPv4-in-IPv6-mapped
    "http://2130706433/",  # Dezimal-IP fuer 127.0.0.1
    "http://0x7f000001/",  # Hex-IP fuer 127.0.0.1
    "http://127.1/",  # verkuerzte Notation fuer 127.0.0.1
    "http://public.example.com@169.254.169.254/",  # userinfo-Verwirrung
]


@pytest.mark.parametrize("url", UNSAFE_URLS)
def test_check_url_is_safe_rejects_unsafe_urls(url):
    """Kernpruefung: jede dieser fuenf Adressen muss von check_url_is_safe
    ALLEIN (kein echter HTTP-Client noetig) abgelehnt werden."""
    with pytest.raises(UnsafeUrlError):
        asyncio.run(check_url_is_safe(url))


@pytest.mark.parametrize(
    "url",
    [
        "http://172.16.0.1/",
        "http://172.31.255.255/",
        "http://192.168.1.1/",
        "http://0.0.0.0/",
        "http://localhost/",
        "ftp://example.com/",
        "gopher://example.com/",
    ],
)
def test_check_url_is_safe_rejects_further_private_and_disallowed_cases(url):
    with pytest.raises(UnsafeUrlError):
        asyncio.run(check_url_is_safe(url))


@pytest.mark.parametrize("url", KNOWN_BYPASS_URLS)
def test_check_url_is_safe_rejects_known_bypass_notations(url):
    """Regressionstest fuer Punkt 3 des Sicherheitsreviews: alternative
    IP-Schreibweisen und Userinfo-Verwirrung muessen weiterhin abgelehnt
    werden. Nutzt die ECHTE OS-Aufloesung (kein Mock) -- genau das soll
    bewiesen werden: dass der glibc-Resolver diese Formen bereits auf die
    gesperrte numerische Adresse abbildet und die Klassifizierung danach
    greift."""
    with pytest.raises(UnsafeUrlError):
        asyncio.run(check_url_is_safe(url))


def test_check_url_is_safe_accepts_public_looking_host(monkeypatch):
    """Positivfall: eine oeffentliche IP darf die Pruefung passieren. DNS wird
    hier gefaelscht, damit der Test nicht von echter Netzwerk-Aufloesung
    abhaengt -- geprueft wird ausschliesslich die IP-Klassifizierung. Die
    Pruefung gibt zusaetzlich (Hostname, IP) zurueck -- fuer das spaetere
    IP-Pinning im tatsaechlichen Request (DNS-Rebinding-Haertung)."""

    def _fake_getaddrinfo(host, *a, **kw):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo)
    host, pinned_ip = asyncio.run(check_url_is_safe("http://example.com/"))  # wirft nicht
    assert host == "example.com"
    assert pinned_ip == "93.184.216.34"


def test_check_url_is_safe_rejects_dns_rebinding_to_private_ip(monkeypatch):
    """Ein oeffentlich klingender Hostname, der auf eine private Adresse
    aufloest, muss trotzdem abgelehnt werden -- die Pruefung haengt an der
    aufgeloesten IP, nicht am Hostnamen-Text."""

    def _fake_getaddrinfo(host, *a, **kw):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 0))]

    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo)
    with pytest.raises(UnsafeUrlError):
        asyncio.run(check_url_is_safe("http://looks-public.example.com/"))


def test_check_url_is_safe_rejects_dns_failure():
    with pytest.raises(UnsafeUrlError):
        asyncio.run(check_url_is_safe("http://this-host-does-not-resolve.invalid/"))


def test_check_url_is_safe_dns_lookup_is_offloaded_and_times_out(monkeypatch):
    """Beweist Finding 1: eine haengende (nie zurueckkehrende) DNS-Aufloesung
    blockiert den Event-Loop NICHT -- sie laeuft in einem Executor-Thread und
    wird nach DNS_RESOLVE_TIMEOUT_S mit einem klaren Fehler abgebrochen,
    statt den Aufrufer (und damit den ganzen Worker-Prozess) unbegrenzt
    haengen zu lassen."""
    import time

    from app import web_fetch_tool

    def _hanging_getaddrinfo(host, *a, **kw):
        # Deutlich laenger als das (hier verkuerzte) DNS_RESOLVE_TIMEOUT_S,
        # aber bewusst nicht uebertrieben lang: asyncio.run() wartet beim
        # Beenden des Event-Loops auf alle noch laufenden Executor-Threads
        # (loop.shutdown_default_executor()) -- ein sehr langer Sleep hier
        # wuerde also trotz erfolgreichem Timeout die TEST-Laufzeit unnoetig
        # aufblaehen (siehe Moduldoc: der Thread selbst ist nicht hart
        # abbrechbar, das ist der dokumentierte Restrisiko-Fall).
        time.sleep(1.5)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(web_fetch_tool, "DNS_RESOLVE_TIMEOUT_S", 0.2)
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _hanging_getaddrinfo)

    async def _run_with_concurrent_proof():
        # Ein paralleler Task muss waehrend der haengenden DNS-Aufloesung
        # weiterlaufen koennen -- das ist der eigentliche Beweis, dass der
        # Event-Loop NICHT blockiert ist.
        progressed = False

        async def _ticker():
            nonlocal progressed
            await asyncio.sleep(0.05)
            progressed = True

        ticker_task = asyncio.create_task(_ticker())
        with pytest.raises(UnsafeUrlError, match="laenger als"):
            await check_url_is_safe("http://example.com/")
        await ticker_task
        return progressed

    assert asyncio.run(_run_with_concurrent_proof())


class _ExplodingAsyncClient:
    """Beweist, dass web_fetch() fuer unsichere URLs NIE einen echten
    Netzwerk-Request auslaesst: jeder Versuch, tatsaechlich zu streamen,
    laesst den Test sofort fehlschlagen."""

    def __init__(self, *a, **kw):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def stream(self, *a, **kw):
        raise AssertionError("web_fetch darf fuer unsichere URLs keinen Request absetzen")


@pytest.mark.parametrize("url", UNSAFE_URLS)
def test_web_fetch_returns_error_without_any_network_request(url, monkeypatch):
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", _ExplodingAsyncClient)
    result = asyncio.run(web_fetch(url))
    assert result.startswith("Fehler")


class _FakeStreamResponse:
    def __init__(self, status_code, headers, body):
        self.status_code = status_code
        self.headers = headers
        self._body = body
        self.encoding = "utf-8"

    async def aiter_bytes(self):
        yield self._body

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeAsyncClient:
    def __init__(self, responses):
        self._responses = list(responses)

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def stream(self, method, url, **kw):
        return self._responses.pop(0)


def _fake_getaddrinfo_public(host, *a, **kw):
    """Klassifiziert Literal-IPs echt (ipaddress), loest jeden anderen
    Hostnamen deterministisch auf eine oeffentliche IP auf -- macht die
    web_fetch-Funktionstests unabhaengig von echter DNS-Aufloesung/Internet-
    Zugriff in der Sandbox."""
    try:
        ipaddress.ip_address(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (host, 0))]
    except ValueError:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]


def test_web_fetch_strips_html_and_truncates(monkeypatch):
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)
    html = b"<html><body><h1>Titel</h1><p>Hallo " + b"Welt " * 3000 + b"</p></body></html>"
    fake = _FakeAsyncClient([_FakeStreamResponse(200, httpx.Headers({}), html)])
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/"))
    assert "<" not in result
    assert "Titel" in result
    assert len(result) <= 6000


def test_web_fetch_follows_redirect_with_recheck(monkeypatch):
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)
    responses = [
        _FakeStreamResponse(302, httpx.Headers({"location": "http://example.com/final"}), b""),
        _FakeStreamResponse(200, httpx.Headers({}), b"<p>Ziel erreicht</p>"),
    ]
    fake = _FakeAsyncClient(responses)
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/start"))
    assert "Ziel erreicht" in result


def test_web_fetch_rejects_redirect_to_private_ip(monkeypatch):
    """Der wichtigste Redirect-Fall: ein Redirect darf die Sperre nicht
    umgehen -- das Ziel wird beim naechsten Hop erneut geprueft."""
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)
    responses = [
        _FakeStreamResponse(302, httpx.Headers({"location": "http://127.0.0.1/secret"}), b""),
    ]
    fake = _FakeAsyncClient(responses)
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/start"))
    assert result.startswith("Fehler")


def test_web_fetch_gives_up_after_too_many_redirects(monkeypatch):
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)
    responses = [
        _FakeStreamResponse(302, httpx.Headers({"location": f"http://example.com/{i}"}), b"")
        for i in range(10)
    ]
    fake = _FakeAsyncClient(responses)
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/start"))
    assert result.startswith("Fehler")


def test_web_fetch_enforces_response_size_limit(monkeypatch):
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)
    """Streamt in Chunks bis zum Limit und bricht danach ab, statt einen
    beliebig grossen Body vollstaendig in den Speicher zu laden."""
    from app import web_fetch_tool

    class _HugeStreamResponse:
        status_code = 200
        headers = httpx.Headers({})
        encoding = "utf-8"

        async def aiter_bytes(self):
            chunk = b"x" * 500_000
            for _ in range(20):  # 10 MB gesamt, weit ueber dem 2-MB-Limit
                yield chunk

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

    fake = _FakeAsyncClient([_HugeStreamResponse()])
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/huge"))
    # Kein Crash, klarer (ggf. gekuerzter) Text zurueck -- die genaue Grenze
    # ist Implementierungsdetail, wichtig ist: es kommt zurueck und ist
    # begrenzt auf MAX_RESULT_CHARS.
    assert len(result) <= web_fetch_tool.MAX_RESULT_CHARS


class _CapturingAsyncClient:
    """Zeichnet jede per `.stream()` tatsaechlich angefragte URL (inkl.
    Headers/Extensions) auf, statt echte Antworten zu liefern -- damit
    pruefbar ist, WOGEGEN der eigentliche Request verbindet (Finding-2-Beweis:
    IP-Pinning statt Hostname-basiertem Connect)."""

    def __init__(self, response):
        self._response = response
        self.calls: list[dict] = []

    def __call__(self, *a, **kw):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def stream(self, method, url, headers=None, extensions=None, **kw):
        self.calls.append({"url": url, "headers": headers, "extensions": extensions})
        return self._response


def test_web_fetch_connects_to_pinned_ip_not_hostname_https(monkeypatch):
    """Pflicht-Test fuer Finding 2 (strukturelle DNS-Rebinding-Haertung):
    beweist, dass der TATSAECHLICHE Verbindungsversuch gegen die zuerst
    validierte IP geht (nicht gegen den Hostnamen), waehrend Host-Header und
    TLS-SNI-Extension trotzdem den Original-Hostnamen tragen (noetig fuer
    HTTPS-Zertifikatspruefung/virtuelles Hosting)."""
    getaddrinfo_calls: list[str] = []

    def _counting_getaddrinfo(host, *a, **kw):
        getaddrinfo_calls.append(host)
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _counting_getaddrinfo)

    fake = _CapturingAsyncClient(
        _FakeStreamResponse(200, httpx.Headers({}), b"<p>Hallo</p>")
    )
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("https://looks-public.example.com/pfad"))
    assert "Hallo" in result

    # GENAU EIN Resolver-Aufruf fuer den gesamten web_fetch()-Durchlauf --
    # httpx bekommt eine bereits IP-basierte URL und kann daher gar keine
    # eigene, zweite (potenziell unabhaengig manipulierte) Aufloesung mehr
    # ausloesen.
    assert getaddrinfo_calls == ["looks-public.example.com"]

    assert len(fake.calls) == 1
    call = fake.calls[0]
    # Der tatsaechliche Connect geht gegen die VALIDIERTE IP, nicht den Host.
    assert httpx.URL(call["url"]).host == "93.184.216.34"
    # Host-Header und TLS-SNI bleiben trotzdem der Original-Hostname.
    assert call["headers"] == {"Host": "looks-public.example.com"}
    assert call["extensions"] == {"sni_hostname": "looks-public.example.com"}


def test_web_fetch_http_scheme_sets_host_header_without_sni_extension(monkeypatch):
    """Fuer HTTP (kein TLS) darf keine sni_hostname-Extension gesetzt werden
    (es gibt kein TLS-Handshake, fuer den SNI relevant waere) -- der
    Host-Header fuer namensbasiertes virtuelles Hosting bleibt aber
    trotzdem gesetzt."""
    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo_public)

    fake = _CapturingAsyncClient(
        _FakeStreamResponse(200, httpx.Headers({}), b"<p>Hallo</p>")
    )
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("http://example.com/pfad"))
    assert "Hallo" in result

    call = fake.calls[0]
    assert httpx.URL(call["url"]).host == "93.184.216.34"
    assert call["headers"] == {"Host": "example.com"}
    assert call["extensions"] == {}


def test_web_fetch_rebinding_attempt_never_reaches_a_second_resolution(monkeypatch):
    """Simuliert einen DNS-Rebinding-Angriff direkt: der ERSTE
    Resolver-Aufruf liefert eine oeffentliche IP (besteht die Pruefung), ein
    HYPOTHETISCHER zweiter, unabhaengiger Aufruf wuerde 169.254.169.254
    (Cloud-Metadata) liefern. Vor dem Fix haette httpx's eigene DNS-
    Aufloesung genau diesen zweiten Aufruf ausgeloest -- nach dem Fix darf es
    ihn nicht mehr geben: der tatsaechliche Request geht nachweislich gegen
    die beim EINZIGEN Aufruf validierte, oeffentliche IP."""
    responses_by_call = [
        [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))],
        [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))],
    ]
    call_count = 0

    def _fake_getaddrinfo(host, *a, **kw):
        nonlocal call_count
        result = responses_by_call[min(call_count, len(responses_by_call) - 1)]
        call_count += 1
        return result

    monkeypatch.setattr("app.web_fetch_tool.socket.getaddrinfo", _fake_getaddrinfo)

    fake = _CapturingAsyncClient(
        _FakeStreamResponse(200, httpx.Headers({}), b"<p>Sicher</p>")
    )
    monkeypatch.setattr("app.web_fetch_tool.httpx.AsyncClient", fake)

    result = asyncio.run(web_fetch("https://rebinding-attacker.example.com/"))

    assert call_count == 1, (
        "es darf nur der ERSTE (als oeffentlich validierte) Resolver-Aufruf "
        "stattfinden -- ein zweiter, unabhaengiger Aufruf waere die "
        "DNS-Rebinding-Luecke"
    )
    assert "Sicher" in result
    assert httpx.URL(fake.calls[0]["url"]).host == "93.184.216.34"
