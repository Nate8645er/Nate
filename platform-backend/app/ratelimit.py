"""Rate-Limiting pro Mandant (Sliding-Window).

Zwei Implementierungen, gleiche Schnittstelle (`check`/`reset`):
  - SlidingWindowLimiter      : In-Process (Standard, kein Redis noetig).
    Reicht bei einem einzelnen Backend-Prozess.
  - RedisSlidingWindowLimiter : Zustand in Redis (Sorted Set pro Schluessel),
    atomar ueber ein Lua-Script. Noetig, sobald mehr als ein Prozess/Pod
    parallel laeuft — sonst sieht jeder Prozess nur seinen eigenen Zaehler
    und das tatsaechliche Limit ist (max_calls * Prozessanzahl). Das war
    bislang als Kommentar dokumentierte, unbehobene Luecke; jetzt behoben,
    aktiviert per Umgebungsvariable REDIS_URL (siehe config.py).

Deckt den in den Reviews benannten Luecken-Punkt "kein Rate-Limiting" ab.
Ergaenzt (ersetzt nicht) die bestehenden Payload-Groessen-Limits.
"""
from __future__ import annotations

import threading
import time
import uuid
from collections import deque

from fastapi import HTTPException, Request

from .config import settings


def client_ip(request: Request) -> str:
    """Client-IP fuer IP-gebundene Limiter (Signup, Login, Checkout-Claim).
    An EINER Stelle definiert statt in jeder Route dupliziert. Ein fehlender
    `request.client` (z.B. bestimmte Test-/Proxy-Setups ohne echten
    Transport) faellt auf eine feste Zeichenkette zurueck statt zu crashen --
    das Limit greift dann eben global statt pro Quelle, lieber das als ein
    500er auf einem unauthentifizierten Endpunkt."""
    return request.client.host if request.client else "unknown"


class SlidingWindowLimiter:
    """Pro Schluessel (z.B. tenant_id) hoechstens `max_calls` Aufrufe je
    `window_s` Sekunden. Thread-safe (FastAPI/uvicorn kann mit mehreren
    Worker-Threads laufen)."""

    def __init__(self, max_calls: int, window_s: float):
        self.max_calls = max_calls
        self.window_s = window_s
        self._hits: dict[str, deque] = {}
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> None:
        """Wirft HTTPException(429), wenn das Limit fuer `key` ueberschritten ist.
        Zaehlt den Aufruf sonst mit."""
        t = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits.setdefault(key, deque())
            cutoff = t - self.window_s
            while q and q[0] < cutoff:
                q.popleft()
            if len(q) >= self.max_calls:
                retry_after = max(0.0, self.window_s - (t - q[0]))
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate-Limit erreicht ({self.max_calls}/{int(self.window_s)}s)",
                    headers={"Retry-After": str(int(retry_after) + 1)},
                )
            q.append(t)

    def reset(self) -> None:
        """Nur fuer Tests: Zustand leeren."""
        with self._lock:
            self._hits.clear()


class RedisSlidingWindowLimiter:
    """Wie SlidingWindowLimiter, aber der Zaehlerstand liegt in Redis statt im
    Prozessspeicher — korrekt bei mehreren Backend-Prozessen/Pods.

    Atomar ueber ein Lua-Script (EVAL): Redis fuehrt das Script als einzelnen
    Befehl aus, dadurch keine Race Condition zwischen "zaehlen" und
    "eintragen", selbst wenn zwei Prozesse im selben Millisekunden anfragen.
    Zeiten werden in Millisekunden gerechnet, weil Redis-Lua Rueckgabewerte
    auf Ganzzahlen abschneidet (Sekunden-Bruchteile wuerden sonst verloren
    gehen und das Sliding Window verfaelschen)."""

    _SCRIPT = """
        local key = KEYS[1]
        local now_ms = tonumber(ARGV[1])
        local window_ms = tonumber(ARGV[2])
        local max_calls = tonumber(ARGV[3])
        local member = ARGV[4]
        local cutoff = now_ms - window_ms
        redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
        local count = redis.call('ZCARD', key)
        if count >= max_calls then
            local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
            local retry_after_ms = 0
            if oldest[2] then
                retry_after_ms = window_ms - (now_ms - tonumber(oldest[2]))
                if retry_after_ms < 0 then retry_after_ms = 0 end
            end
            return retry_after_ms
        end
        redis.call('ZADD', key, now_ms, member)
        redis.call('PEXPIRE', key, window_ms)
        return -1
    """

    def __init__(self, max_calls: int, window_s: float, redis_client, prefix: str = "ratelimit"):
        self.max_calls = max_calls
        self.window_s = window_s
        self._redis = redis_client
        self._prefix = prefix

    def check(self, key: str, now: float | None = None) -> None:
        now_s = time.time() if now is None else now
        now_ms = int(round(now_s * 1000))
        window_ms = int(round(self.window_s * 1000))
        member = f"{now_ms}-{uuid.uuid4().hex}"
        redis_key = f"{self._prefix}:{key}"
        retry_after_ms = self._redis.eval(
            self._SCRIPT, 1, redis_key, now_ms, window_ms, self.max_calls, member
        )
        retry_after_ms = int(retry_after_ms)
        if retry_after_ms >= 0:
            retry_after_s = retry_after_ms / 1000.0
            raise HTTPException(
                status_code=429,
                detail=f"Rate-Limit erreicht ({self.max_calls}/{int(self.window_s)}s)",
                headers={"Retry-After": str(int(retry_after_s) + 1)},
            )

    def reset(self) -> None:
        """Nur fuer Tests: alle Schluessel mit diesem Prefix loeschen."""
        for k in self._redis.scan_iter(f"{self._prefix}:*"):
            self._redis.delete(k)


def _build_limiter(max_calls: int, window_s: float):
    """REDIS_URL gesetzt -> Redis-backed (mehrere Prozesse/Pods sicher),
    sonst In-Process (Standard fuer lokale Entwicklung/Tests, keine
    zusaetzliche Infrastruktur noetig)."""
    if not settings.redis_url:
        return SlidingWindowLimiter(max_calls=max_calls, window_s=window_s)
    import redis as redis_lib

    client = redis_lib.Redis.from_url(settings.redis_url)
    return RedisSlidingWindowLimiter(max_calls=max_calls, window_s=window_s, redis_client=client)


# Chat/Agenten-Ausfuehrung ist der teuerste Pfad (LLM-Aufruf) -> eigenes,
# enges Limit. Andere Lese-Routen sind unkritisch und bleiben ungedrosselt.
chat_limiter = _build_limiter(max_calls=30, window_s=60.0)

# Selbstbedienungs-Registrierung (/v1/auth/signup): schuetzt gegen
# Massen-Registrierung (z.B. Free-Tarif-Abuse per Skript) -- pro IP, da eine
# neue Registrierung per Definition noch keine bekannte E-Mail-Identitaet hat.
signup_limiter = _build_limiter(max_calls=5, window_s=3600.0)

# Zusaetzlich pro E-Mail (Security-Review, Punkt C): das 409 "bereits
# registriert" verraet, ob eine E-Mail schon existiert (akzeptierter
# Self-Service-Signup-Trade-off, siehe README) -- ein reines IP-Limit bremst
# aber nur EINEN Absender, nicht verteilte Massen-Enumeration derselben
# Ziel-E-Mail ueber viele IPs. Analog zu login_limiter_email.
signup_limiter_email = _build_limiter(max_calls=5, window_s=3600.0)

# Login (/v1/auth/login): Brute-Force-Schutz in ZWEI Richtungen --
#   - pro IP: verhindert, dass ein Angreifer viele verschiedene E-Mails von
#     einer Quelle aus durchprobiert (Credential Stuffing).
#   - pro E-Mail: verhindert, dass EIN Konto von vielen IPs aus (verteilter
#     Angriff) durchprobiert wird -- ein reines IP-Limit wuerde das nicht
#     abdecken.
login_limiter_ip = _build_limiter(max_calls=20, window_s=300.0)
login_limiter_email = _build_limiter(max_calls=8, window_s=300.0)

# Checkout-Claim (/v1/checkout/{session_id}/claim, app/routes/billing.py):
# anders als Login/Signup war dieser unauthentifizierte Endpunkt bisher OHNE
# Limiter, obwohl er eine DB-Schreiboperation ausloest (Session anlegen,
# Handoff-Zeile loeschen) -- ein Angreifer koennte beliebig viele
# Session-IDs durchprobieren/DB-Last erzeugen. Nur pro IP (kein E-Mail-Bezug
# moeglich, die Session-ID ist das einzige, was der Aufrufer mitbringt).
checkout_claim_limiter = _build_limiter(max_calls=20, window_s=300.0)
