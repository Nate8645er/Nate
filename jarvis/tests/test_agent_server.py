"""Tests fuer die lokale Agent-Bruecke (HTTP-Server, nur stdlib)."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from open_jarvis.agent import server as S


def test_run_task_builds_shop_preview(tmp_path) -> None:
    result = S.run_task({"task": "baue mir einen Shop fuer Kaffee namens Bergbohne", "model": "local"}, workspace=tmp_path)
    assert result["ok"] is True
    assert result["steps"][0]["tool"] == "shop_bauen"
    assert result["execute"] is False
    assert "text" in result  # menschenlesbarer Bericht


def test_run_task_executes_and_writes(tmp_path) -> None:
    result = S.run_task({"task": "baue mir einen Shop fuer Tee namens Blattgold", "model": "local", "execute": True}, workspace=tmp_path)
    assert result["ok"] is True
    assert (tmp_path / "shops" / "blattgold" / "shop_plan.md").exists()


def test_run_task_rejects_empty_task(tmp_path) -> None:
    assert S.run_task({"task": ""}, workspace=tmp_path)["ok"] is False


def test_run_task_rejects_unknown_model(tmp_path) -> None:
    out = S.run_task({"task": "hallo", "model": "gpt-9"}, workspace=tmp_path)
    assert out["ok"] is False
    assert "gpt-9" in out["error"]


@pytest.fixture()
def bridge(tmp_path):
    handler = type("H", (S._Handler,), {"workspace": str(tmp_path)})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)  # freier Port
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    time.sleep(0.2)
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def _get(url):
    return json.loads(urllib.request.urlopen(url, timeout=5).read())


def _post(url, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    return json.loads(urllib.request.urlopen(req, timeout=5).read())


def test_health_endpoint(bridge) -> None:
    health = _get(bridge + "/health")
    assert health["ok"] is True
    assert "fable-5" in health["models"]


def test_agent_endpoint_runs_command(bridge) -> None:
    res = _post(bridge + "/agent", {"task": "suche nach Kaffee", "model": "local"})
    assert res["ok"] is True
    assert res["steps"][0]["tool"] == "web_suche"


def test_agent_endpoint_rejects_bad_json(bridge) -> None:
    req = urllib.request.Request(bridge + "/agent", data=b"nicht-json", headers={"Content-Type": "application/json"}, method="POST")
    with pytest.raises(urllib.error.HTTPError) as exc:
        urllib.request.urlopen(req, timeout=5)
    assert exc.value.code == 400


def test_hud_served_at_root(bridge) -> None:
    html = urllib.request.urlopen(bridge + "/", timeout=5).read().decode("utf-8")
    assert "J.A.R.V.I.S" in html
    assert "Command Center" in html


def test_cors_and_options(bridge) -> None:
    req = urllib.request.Request(bridge + "/agent", method="OPTIONS")
    resp = urllib.request.urlopen(req, timeout=5)
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"


def test_serve_rejects_non_localhost() -> None:
    with pytest.raises(ValueError):
        S.serve(host="0.0.0.0")
