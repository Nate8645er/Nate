"""Unit-Tests der API-Key-Erzeugung/Hashing — laufen ohne DB/Gateway."""
from app.auth import generate_key, hash_key


def test_hash_is_deterministic_and_sha256():
    h = hash_key("pk_example")
    assert h == hash_key("pk_example")
    assert len(h) == 64  # sha256 hex
    assert all(c in "0123456789abcdef" for c in h)


def test_generate_key_shape_and_hash_matches():
    clear, h = generate_key()
    assert clear.startswith("pk_")
    assert len(clear) > 20
    assert hash_key(clear) == h


def test_two_keys_differ():
    a, _ = generate_key()
    b, _ = generate_key()
    assert a != b
