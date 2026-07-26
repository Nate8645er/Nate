"""Beweist den Redis-backed Limiter gegen einen echten lokalen redis-server
(kein Mock) — startet/stoppt ihn selbst auf einem freien Port, damit der Test
ohne manuellen Vorlauf laeuft. Reine Unit-Ebene (RedisSlidingWindowLimiter
direkt), die Route-Integration ist bereits in test_ratelimit_integration.py
abgedeckt (dort mit dem In-Process-Limiter)."""
from __future__ import annotations

import shutil
import socket
import subprocess
import time

import pytest
from fastapi import HTTPException

from app.ratelimit import RedisSlidingWindowLimiter

pytestmark = pytest.mark.skipif(
    shutil.which("redis-server") is None, reason="redis-server nicht installiert"
)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture()
def redis_client():
    import redis as redis_lib

    port = _free_port()
    proc = subprocess.Popen(
        [
            "redis-server", "--port", str(port), "--bind", "127.0.0.1",
            "--save", "", "--appendonly", "no", "--daemonize", "no",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    client = redis_lib.Redis(host="127.0.0.1", port=port)
    try:
        for _ in range(50):
            try:
                if client.ping():
                    break
            except redis_lib.exceptions.ConnectionError:
                pass
            time.sleep(0.1)
        else:
            raise RuntimeError("redis-server nicht rechtzeitig hochgekommen")
        yield client
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def test_allows_up_to_max_calls(redis_client):
    lim = RedisSlidingWindowLimiter(max_calls=3, window_s=60, redis_client=redis_client)
    for _ in range(3):
        lim.check("t1", now=0.0)  # kein Fehler


def test_blocks_after_max_calls(redis_client):
    lim = RedisSlidingWindowLimiter(max_calls=3, window_s=60, redis_client=redis_client)
    for _ in range(3):
        lim.check("t1", now=0.0)
    with pytest.raises(HTTPException) as exc:
        lim.check("t1", now=0.1)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_window_slides_and_allows_again(redis_client):
    lim = RedisSlidingWindowLimiter(max_calls=2, window_s=10, redis_client=redis_client)
    lim.check("t1", now=0.0)
    lim.check("t1", now=1.0)
    with pytest.raises(HTTPException):
        lim.check("t1", now=2.0)
    lim.check("t1", now=10.1)  # Fenster abgelaufen -> wieder frei


def test_keys_are_independent(redis_client):
    lim = RedisSlidingWindowLimiter(max_calls=1, window_s=60, redis_client=redis_client)
    lim.check("tenant-a", now=0.0)
    lim.check("tenant-b", now=0.0)  # anderer Mandant, eigenes Kontingent
    with pytest.raises(HTTPException):
        lim.check("tenant-a", now=0.1)


def test_reset_clears_state(redis_client):
    lim = RedisSlidingWindowLimiter(max_calls=1, window_s=60, redis_client=redis_client)
    lim.check("t1", now=0.0)
    lim.reset()
    lim.check("t1", now=0.1)  # kein Fehler nach Reset


def test_shared_state_across_two_limiter_instances(redis_client):
    """Der eigentliche Zweck: zwei getrennte Prozesse (hier: zwei Python-
    Objekte auf demselben Redis) teilen sich EIN Kontingent — genau das,
    was der In-Process-Limiter nicht kann."""
    lim_a = RedisSlidingWindowLimiter(max_calls=2, window_s=60, redis_client=redis_client)
    lim_b = RedisSlidingWindowLimiter(max_calls=2, window_s=60, redis_client=redis_client)
    lim_a.check("shared", now=0.0)
    lim_b.check("shared", now=0.0)
    with pytest.raises(HTTPException):
        lim_a.check("shared", now=0.1)
    with pytest.raises(HTTPException):
        lim_b.check("shared", now=0.1)
