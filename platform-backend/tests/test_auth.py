"""Unit-Tests der Passwort-/Session-Token-Erzeugung -- laufen ohne DB/Gateway.

Es gibt keinen API-Schluessel mehr (siehe app/auth.py, Migration
013_drop_api_keys.sql) -- Session-Cookie ist der einzige Authentifizierungsweg."""
import asyncio

import pytest
from fastapi import HTTPException

from app.auth import (
    DUMMY_PASSWORD_HASH,
    generate_session_token,
    hash_key,
    hash_password,
    require_principal,
    verify_password,
)


def test_hash_is_deterministic_and_sha256():
    h = hash_key("some-session-token")
    assert h == hash_key("some-session-token")
    assert len(h) == 64  # sha256 hex
    assert all(c in "0123456789abcdef" for c in h)


def test_generate_session_token_shape_and_hash_matches():
    clear, h = generate_session_token()
    assert len(clear) > 20
    assert hash_key(clear) == h


def test_two_session_tokens_differ():
    a, _ = generate_session_token()
    b, _ = generate_session_token()
    assert a != b


def test_password_hash_is_bcrypt_and_verifies():
    h = hash_password("correct horse battery staple")
    assert h.startswith("$2")  # bcrypt-Kennung
    assert verify_password("correct horse battery staple", h)
    assert not verify_password("wrong password", h)


def test_password_hash_is_salted_two_calls_differ():
    a = hash_password("same-password")
    b = hash_password("same-password")
    assert a != b  # bcrypt.gensalt() -> unterschiedliches Salt pro Aufruf
    assert verify_password("same-password", a)
    assert verify_password("same-password", b)


def test_verify_password_never_raises_on_garbage_hash():
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False
    assert verify_password("anything", "") is False


def test_dummy_password_hash_is_a_valid_bcrypt_hash():
    # Wird beim Login fuer unbekannte E-Mails verglichen, um die Laufzeit
    # gegen einen echten Fehlversuch anzugleichen (Timing-Seitenkanal).
    assert DUMMY_PASSWORD_HASH.startswith("$2")
    assert not verify_password("irgendwas", DUMMY_PASSWORD_HASH)


def test_require_principal_without_cookie_is_401_without_db():
    """Kein Session-Cookie vorhanden -> 401, ohne dass ueberhaupt eine
    DB-Verbindung noetig ist (reiner Fast-Fail-Pfad). Es gibt keinen
    Bearer-Header-Parameter mehr, gegen den man pruefen koennte -- ein
    mitgeschickter Authorization-Header wird von require_principal gar
    nicht mehr entgegengenommen."""
    with pytest.raises(HTTPException) as exc:
        asyncio.run(require_principal(session=None))
    assert exc.value.status_code == 401
