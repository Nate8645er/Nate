"""Unit-Tests des Sliding-Window-Rate-Limiters — ohne DB, deterministisch
ueber injizierte Zeit."""
import pytest
from fastapi import HTTPException

from app.ratelimit import SlidingWindowLimiter


def test_allows_up_to_max_calls():
    lim = SlidingWindowLimiter(max_calls=3, window_s=60)
    for _ in range(3):
        lim.check("t1", now=0.0)  # kein Fehler


def test_blocks_after_max_calls():
    lim = SlidingWindowLimiter(max_calls=3, window_s=60)
    for _ in range(3):
        lim.check("t1", now=0.0)
    with pytest.raises(HTTPException) as exc:
        lim.check("t1", now=0.1)
    assert exc.value.status_code == 429
    assert "Retry-After" in exc.value.headers


def test_window_slides_and_allows_again():
    lim = SlidingWindowLimiter(max_calls=2, window_s=10)
    lim.check("t1", now=0.0)
    lim.check("t1", now=1.0)
    with pytest.raises(HTTPException):
        lim.check("t1", now=2.0)
    # Nach Ablauf des Fensters (10s seit erstem Hit) wieder frei.
    lim.check("t1", now=10.1)


def test_keys_are_independent():
    lim = SlidingWindowLimiter(max_calls=1, window_s=60)
    lim.check("tenant-a", now=0.0)
    lim.check("tenant-b", now=0.0)  # anderer Mandant, eigenes Kontingent
    with pytest.raises(HTTPException):
        lim.check("tenant-a", now=0.1)


def test_reset_clears_state():
    lim = SlidingWindowLimiter(max_calls=1, window_s=60)
    lim.check("t1", now=0.0)
    lim.reset()
    lim.check("t1", now=0.1)  # kein Fehler nach Reset
