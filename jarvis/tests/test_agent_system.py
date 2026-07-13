"""Tests fuer den JARVIS-Systemzusammenbau (Architektur als lauffaehiges Ganzes)."""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from open_jarvis.agent import JarvisSystem, architecture
from open_jarvis.agent import server as S


# --------------------------- Architektur ------------------------------------ #
def test_architecture_brain_is_fable5() -> None:
    arch = architecture()
    assert arch["brain"]["label"] == "Fable 5"
    assert arch["brain"]["model_id"] == "claude-fable-5"
    assert "Gehirn" in arch["brain"]["role"]


def test_architecture_has_all_layers() -> None:
    names = [layer["name"] for layer in architecture()["layers"]]
    assert names == ["Chrome Browser", "Lokaler Server (Bridge)", "Externe Services", "Lokale Tools"]
    # Das Gehirn taucht in den externen Services auf und traegt Fable 5.
    extern = next(l for l in architecture()["layers"] if l["name"] == "Externe Services")
    assert any("Fable 5" in c["name"] for c in extern["components"])


def test_architecture_flow_mentions_fable5_thinking() -> None:
    flow = architecture()["flow"]
    assert "Nutzer spricht" in flow[0]
    assert any("Fable 5 denkt" == step for step in flow)


# --------------------------- JarvisSystem ----------------------------------- #
def test_system_default_brain_is_fable5() -> None:
    assert JarvisSystem().brain.key == "fable-5"


def test_system_handle_builds_shop_and_speaks(tmp_path) -> None:
    system = JarvisSystem(model="local", workspace=tmp_path)
    resp = system.handle("baue mir einen Shop fuer Kaffee namens Bergbohne")
    assert resp.run.outcomes[0].tool == "shop_bauen"
    assert "Sir" in resp.spoken  # Persoenlichkeit
    payload = resp.to_dict()
    assert payload["command"].startswith("baue")
    assert "spoken" in payload and "steps" in payload
    json.dumps(payload)  # serialisierbar


def test_system_execute_writes_and_acknowledges(tmp_path) -> None:
    system = JarvisSystem(model="local", workspace=tmp_path, execute=True)
    resp = system.handle("baue mir einen Shop fuer Tee namens Blattgold")
    assert (tmp_path / "shops" / "blattgold" / "shop_plan.md").exists()
    assert resp.spoken.startswith("Sehr wohl, Sir.")


# --------------------------- Server /architecture --------------------------- #
@pytest.fixture()
def bridge(tmp_path):
    handler = type("H", (S._Handler,), {"workspace": str(tmp_path)})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def test_architecture_endpoint(bridge) -> None:
    data = json.loads(urllib.request.urlopen(bridge + "/architecture", timeout=5).read())
    assert data["ok"] is True
    assert data["architecture"]["brain"]["label"] == "Fable 5"


def test_agent_endpoint_returns_spoken(bridge) -> None:
    req = urllib.request.Request(
        bridge + "/agent",
        data=json.dumps({"task": "suche nach Kaffee", "model": "local"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    res = json.loads(urllib.request.urlopen(req, timeout=5).read())
    assert res["ok"] is True
    assert "Sir" in res["spoken"]
