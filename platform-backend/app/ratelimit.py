"""Einfaches Rate-Limiting pro Mandant (Sliding-Window, In-Process).

Bewusst ohne Redis: bei einem einzelnen Backend-Prozess reicht ein
In-Memory-Zaehler; bei horizontaler Skalierung (mehrere Prozesse/Pods)
muesste das durch einen gemeinsamen Speicher (Redis) ersetzt werden — hier
als Kommentar dokumentiert statt stillschweigend falsch zu skalieren.

Deckt den in den Reviews benannten Luecken-Punkt "kein Rate-Limiting" ab.
Ergaenzt (ersetzt nicht) die bestehenden Payload-Groessen-Limits.
"""
from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import HTTPException


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


# Chat/Agenten-Ausfuehrung ist der teuerste Pfad (LLM-Aufruf) -> eigenes,
# enges Limit. Andere Lese-Routen sind unkritisch und bleiben ungedrosselt.
chat_limiter = SlidingWindowLimiter(max_calls=30, window_s=60.0)
