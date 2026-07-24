"""Integrationstest: Router -> LiteLLM -> lokaler OpenAI-kompatibler Endpoint.

Beweist den lokalen Inferenzpfad END-TO-END, ohne Netz und ohne GPU: ein
winziger stdlib-HTTP-Server spielt die OpenAI-`/v1/chat/completions`-Schnittstelle
(genau die, die echtes Ollama/vLLM bedient). Es fehlen nur echte Modellgewichte
— die Integrationskette (Routing-Entscheidung, LiteLLM-Call, Antwort-Parsing)
läuft real.

Überspringt sauber, falls litellm nicht installiert ist.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

litellm = pytest.importorskip("litellm")

from app.models.router import DataClass, ModelRequest, ModelRouter, RoutingContext


class _OpenAIStub(BaseHTTPRequestHandler):
    def log_message(self, *args):  # still im Test
        pass

    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        user = next((m.get("content", "") for m in body.get("messages", []) if m.get("role") == "user"), "")
        payload = {
            "id": "chatcmpl-stub", "object": "chat.completion", "created": 1,
            "model": body.get("model", "local-model"),
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": f"echo:{user}"}}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
        }
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@pytest.fixture()
def local_endpoint():
    server = HTTPServer(("127.0.0.1", 0), _OpenAIStub)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{port}/v1"
    finally:
        server.shutdown()


def test_local_only_geht_end_to_end_ueber_litellm(local_endpoint):
    ctx = RoutingContext(local_available=True, local_capabilities=frozenset({"text"}), cloud_available=False)
    router = ModelRouter(ctx, local_base_url=local_endpoint)
    req = ModelRequest(prompt_tokens_est=3, data_class=DataClass.LOCAL_ONLY,
                       needs=frozenset({"text"}), model="tiny")
    out = router.complete(req, [{"role": "user", "content": "hallo"}])

    assert out["decision"]["placement"] == "local"
    assert out["ok"] is True
    assert out["response"].choices[0].message.content == "echo:hallo"


def test_lokal_ohne_url_gibt_ehrlichen_fehler():
    ctx = RoutingContext(local_available=True, local_capabilities=frozenset({"text"}), cloud_available=False)
    router = ModelRouter(ctx, local_base_url=None)
    out = router.complete(ModelRequest(3, data_class=DataClass.LOCAL_ONLY), [{"role": "user", "content": "x"}])
    assert out["ok"] is False
    assert "LOCAL_LLM_URL" in out["error"]
