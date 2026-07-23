"""Tests für die Routing-Policy — reine Logik, ohne Netz/LiteLLM."""

from app.models.router import (
    DataClass,
    ModelRequest,
    RoutingContext,
    decide,
)


def _ctx(**kw):
    base = {"local_available": True, "local_capabilities": frozenset({"text", "vision"}), "cloud_available": True}
    base.update(kw)
    return RoutingContext(**base)


def test_local_only_bindend_bleibt_lokal():
    d = decide(ModelRequest(100, data_class=DataClass.LOCAL_ONLY), _ctx())
    assert d.placement == "local"
    assert d.fallback is None  # local_only darf NIE in die Cloud fallen


def test_local_only_ohne_backend_trotzdem_lokal_best_effort():
    d = decide(ModelRequest(100, data_class=DataClass.LOCAL_ONLY), _ctx(local_available=False))
    assert d.placement == "local"
    assert "kein lokales Backend" in d.reason


def test_fehlende_faehigkeit_geht_in_cloud():
    req = ModelRequest(100, needs=frozenset({"video"}))
    d = decide(req, _ctx())  # local kann nur text/vision
    assert d.placement == "cloud"
    assert d.fallback == "local"


def test_local_only_mit_fehlender_faehigkeit_bleibt_lokal():
    req = ModelRequest(100, data_class=DataClass.LOCAL_ONLY, needs=frozenset({"video"}))
    d = decide(req, _ctx())
    assert d.placement == "local"  # Datenhoheit schlägt Fähigkeit
    assert d.fallback is None


def test_lokal_bevorzugt_wenn_frei():
    d = decide(ModelRequest(100), _ctx(local_load_pct=10.0))
    assert d.placement == "local"


def test_lokal_ueberlastet_weicht_in_cloud():
    d = decide(ModelRequest(100), _ctx(local_load_pct=95.0))
    assert d.placement == "cloud"
    assert "überlastet" in d.reason


def test_kein_lokal_geht_cloud():
    d = decide(ModelRequest(100), _ctx(local_available=False))
    assert d.placement == "cloud"


def test_jede_entscheidung_hat_begruendung():
    for dc in DataClass:
        d = decide(ModelRequest(50, data_class=dc), _ctx())
        assert d.reason  # nie leer
