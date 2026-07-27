"""Regressionstest fuer einen frueher im README als offen dokumentierten
Punkt: "Enterprise-'*' laesst jedes Modell zu; unbekannte enden als 502 statt
403". Empirisch gegen eine echte Postgres-DB geprueft (26.07.): das stimmt
nicht mehr (falls es je stimmte) -- is_registered() in models_catalog.py
prueft unabhaengig vom Tarif-Wildcard gegen die registrierte Gateway-Liste,
BEVOR ueberhaupt an das Gateway weitergeleitet wird. Dieser Test haelt das
fest, damit es nicht unbemerkt wieder regressiert."""
from __future__ import annotations

import os

import pytest

DSN = os.environ.get("PLATFORM_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DSN, reason="PLATFORM_TEST_DATABASE_URL nicht gesetzt (keine Test-DB)"
)


def test_enterprise_wildcard_unregistered_model_is_403_not_502(client, prov):
    prov("enterprise")
    r = client.post(
        "/v1/chat",
        json={"model": "erfundenes/modell-xyz", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code == 403
    assert "nicht verfuegbar" in r.json()["detail"]


def test_enterprise_wildcard_registered_model_passes_validation(client, prov):
    """Enterprise + registriertes Modell kommt durch die Validierung (503/502
    vom nicht erreichbaren Gateway ist erwartet -- hier geht es nur darum,
    dass KEIN 403 vor dem Gateway-Aufruf kommt)."""
    prov("enterprise")
    r = client.post(
        "/v1/chat",
        json={"model": "ollama/llama3.2", "messages": [{"role": "user", "content": "hi"}]},
    )
    assert r.status_code != 403
