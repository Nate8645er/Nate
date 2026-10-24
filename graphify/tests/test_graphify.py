"""End-to-End-Tests: scannen ein Mini-Projekt und pruefen Graph + CLI-Output."""

import io
import json
import os
import subprocess
import sys
import textwrap

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from graphify.graph import Graph
from graphify.scanner import scan


@pytest.fixture()
def project(tmp_path):
    (tmp_path / "models.py").write_text(textwrap.dedent("""\
        class ModelField:
            def validate(self, value):
                return value
    """))
    (tmp_path / "handlers.py").write_text(textwrap.dedent("""\
        from models import ModelField

        def get_request_handler(field: ModelField):
            return field.validate(None)
    """))
    (tmp_path / "app.py").write_text(textwrap.dedent("""\
        from handlers import get_request_handler

        class FastAPI:
            def setup(self):
                return get_request_handler(None)
    """))
    return tmp_path


def test_scan_builds_nodes_and_edges(project):
    g = scan(str(project))
    names = {n.name for n in g.nodes.values()}
    assert {"FastAPI", "ModelField", "get_request_handler"} <= names
    assert any(n.kind == "method" and n.name == "FastAPI.setup" for n in g.nodes.values())
    assert g.edges, "Graph muss Kanten enthalten"
    assert g.communities, "Communities muessen berechnet sein"


def test_save_and_load_roundtrip(project):
    g = scan(str(project))
    g.save(str(project))
    loaded = Graph.load(str(project))
    assert set(loaded.nodes) == set(g.nodes)
    assert len(loaded.edges) == len(g.edges)


def test_shortest_path_fastapi_to_modelfield(project):
    g = scan(str(project))
    src = g.resolve("FastAPI")[0]
    dst = g.resolve("ModelField")[0]
    path = g.shortest_path(src.id, dst.id)
    assert path is not None
    assert path[0][0] == src.id
    assert path[-1][0] == dst.id


def test_resolve_accepts_video_style_names(project):
    g = scan(str(project))
    assert g.resolve("get_request_handler()")[0].kind == "function"
    assert g.resolve('"FastAPI"'.strip('"'))[0].name == "FastAPI"


def _cli(project, *argv):
    return subprocess.run(
        [sys.executable, "-m", "graphify", *argv],
        cwd=str(project),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..")},
    )


def test_cli_end_to_end(project):
    r = _cli(project, "scan", ".")
    assert r.returncode == 0, r.stderr
    assert "Graph saved" in r.stdout

    r = _cli(project, "explain", "ModelField")
    assert r.returncode == 0, r.stderr
    assert "Node: ModelField" in r.stdout
    assert "Community:" in r.stdout
    assert "Connections" in r.stdout

    r = _cli(project, "path", "FastAPI", "ModelField")
    assert r.returncode == 0, r.stderr
    assert "Shortest path" in r.stdout
    assert "Zero files opened." in r.stdout

    r = _cli(project, "search", "handler")
    assert r.returncode == 0, r.stderr
    assert "get_request_handler" in r.stdout

    r = _cli(project, "stats")
    assert r.returncode == 0, r.stderr
    assert "Communities" in r.stdout


def test_mcp_server_protocol(project):
    _cli(project, "scan", ".")
    requests = "\n".join(json.dumps(r) for r in [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "graphify_path",
                    "arguments": {"src": "FastAPI", "dst": "ModelField"}}},
    ]) + "\n"
    r = subprocess.run(
        [sys.executable, "-m", "graphify", "mcp"],
        cwd=str(project), input=requests, capture_output=True, text=True,
        env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(__file__), "..")},
    )
    lines = [json.loads(l) for l in r.stdout.strip().splitlines()]
    by_id = {l["id"]: l for l in lines}
    assert by_id[1]["result"]["serverInfo"]["name"] == "graphify"
    tool_names = {t["name"] for t in by_id[2]["result"]["tools"]}
    assert {"graphify_explain", "graphify_path", "graphify_search", "graphify_stats"} <= tool_names
    text = by_id[3]["result"]["content"][0]["text"]
    assert "Zero files opened." in text
