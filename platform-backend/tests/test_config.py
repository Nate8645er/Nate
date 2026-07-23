"""Tests für den Config-Layer — honest not-configured."""

from app.config import ServiceConfig, Settings


def test_leer_ist_nicht_konfiguriert():
    s = Settings(env={})
    assert s.env_name == "development"
    snap = s.snapshot()
    assert snap == {k: False for k in snap}  # ohne Env: alles ehrlich 'nicht konfiguriert'


def test_service_braucht_url_und_secrets():
    ohne = ServiceConfig("x", url=None)
    assert ohne.configured is False
    nur_url = ServiceConfig("x", url="https://x", secrets=(None,))
    assert nur_url.configured is False  # Secret fehlt
    voll = ServiceConfig("x", url="https://x", secrets=("token",))
    assert voll.configured is True


def test_minio_braucht_beide_keys():
    s = Settings(env={"MINIO_ENDPOINT": "http://minio:9000", "MINIO_ACCESS_KEY": "a"})
    assert s.minio.configured is False  # SECRET_KEY fehlt
    s2 = Settings(env={"MINIO_ENDPOINT": "http://minio:9000", "MINIO_ACCESS_KEY": "a", "MINIO_SECRET_KEY": "b"})
    assert s2.minio.configured is True


def test_local_llm_key_optional():
    s = Settings(env={"LOCAL_LLM_URL": "http://localhost:11434/v1"})
    assert s.local_llm.configured is True  # keyOptional (selbst gehostet)


def test_require_wirft_bei_fehlend():
    try:
        ServiceConfig("db", url=None).require()
    except RuntimeError as e:
        assert "nicht-konfiguriert" in str(e)
    else:
        raise AssertionError("require() haette werfen muessen")
