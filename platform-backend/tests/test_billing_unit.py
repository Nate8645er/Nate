"""Unit-Tests der Abrechnungs-Logik — ohne DB."""
import hashlib
import hmac

import pytest

from app.billing import (
    parse_stripe_signature,
    plan_code_from_event,
    verify_stripe_signature,
)

SECRET = "whsec_test"


def sign(body: bytes, ts: int, secret: str = SECRET) -> str:
    payload = f"{ts}.".encode() + body
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_parse_signature_header():
    ts, sigs = parse_stripe_signature("t=123,v1=aaa,v1=bbb,v0=zzz")
    assert ts == 123 and sigs == ["aaa", "bbb"]


def test_valid_signature_accepted():
    body = b'{"id":"evt_1"}'
    assert verify_stripe_signature(body, sign(body, 1000), SECRET, now=1000) is True


def test_wrong_secret_rejected():
    body = b'{"id":"evt_1"}'
    assert verify_stripe_signature(body, sign(body, 1000), "other", now=1000) is False


def test_tampered_body_rejected():
    header = sign(b'{"id":"evt_1"}', 1000)
    assert verify_stripe_signature(b'{"id":"evt_HACK"}', header, SECRET, now=1000) is False


def test_replay_outside_tolerance_rejected():
    body = b'{"id":"evt_1"}'
    header = sign(body, 1000)
    # 301 s spaeter -> ausserhalb der Toleranz von 300 s.
    assert verify_stripe_signature(body, header, SECRET, now=1301) is False
    assert verify_stripe_signature(body, header, SECRET, now=1299) is True


def test_missing_pieces_rejected():
    body = b"{}"
    assert verify_stripe_signature(body, "", SECRET, now=1000) is False
    assert verify_stripe_signature(body, "t=1000", SECRET, now=1000) is False
    assert verify_stripe_signature(body, sign(body, 1000), "", now=1000) is False


def test_non_ascii_signature_candidate_rejected_not_crashed():
    # compare_digest wirft TypeError bei Nicht-ASCII-Strings — muss als
    # Nicht-Treffer behandelt werden, nicht als 500 durchschlagen.
    body = b'{"id":"evt_1"}'
    header = f"t=1000,v1={chr(252)}"  # 'ü' — kam frueher als latin-1-Byte durch
    assert verify_stripe_signature(body, header, SECRET, now=1000) is False


def test_plan_code_from_metadata():
    assert plan_code_from_event({"metadata": {"plan_code": "Pro"}}) == "pro"


def test_plan_code_from_price_map(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_MAP", "price_abc:business,price_def:pro")
    obj = {"items": {"data": [{"price": {"id": "price_def"}}]}}
    assert plan_code_from_event(obj) == "pro"


def test_plan_code_unknown_returns_none(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_MAP", "")
    assert plan_code_from_event({"items": {"data": [{"price": {"id": "x"}}]}}) is None
