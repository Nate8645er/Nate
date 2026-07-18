"""Dashboard-API-Tests: alle Endpunkte, Fehlerpfade, Host-Guard, Claw-Code-Route.

Diese Tests decken die vorher komplett ungetestete FastAPI-Schicht ab:
  - /api/state, /api/task (inkl. ungültiger Adresse -> 400, Worker überlebt),
  - /api/employee, /api/org, /api/memory, /api/business,
  - /api/security/* (dürfen auch auf Nicht-Windows nie 500 werfen),
  - /api/brain und /api/brain/key (Key-Validierung),
  - Host-Guard-Middleware (DNS-Rebinding-Schutz),
  - Claw-Code-Route (!plugin code) End-to-End über /api/task inkl. Gating.
"""

import os
import tempfile
import time

import pytest

# Muss VOR dem Import der App gesetzt sein (DATA_DIR wird beim Import gelesen).
os.environ.setdefault("JARVIS_DATA", tempfile.mkdtemp(prefix="jarvis-test-"))
os.environ["JARVIS_SECURITY"] = "0"       # keine Hintergrund-Threads im Test
os.environ.pop("JARVIS_AUTOPILOT", None)
os.environ.pop("JARVIS_DEMO", None)

from fastapi.testclient import TestClient  # noqa: E402

from jarvis.dashboard.app import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    # base_url localhost, damit der Host-Guard (DNS-Rebinding-Schutz) durchlässt
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def _wait_done(client: TestClient, task_id: int, timeout_s: float = 10.0) -> dict:
    """Pollt eine Aufgabe bis fertig/fehler — wie das Frontend."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = client.get(f"/api/task/{task_id}")
        if r.status_code == 200 and r.json()["status"] in ("fertig", "fehler"):
            return r.json()
        time.sleep(0.05)
    raise AssertionError(f"Aufgabe {task_id} wurde nicht fertig")


# ---------------------------------------------------------------------------
# Systemzustand & Seiten
# ---------------------------------------------------------------------------

def test_state_has_all_subsystems(client):
    r = client.get("/api/state")
    assert r.status_code == 200
    s = r.json()
    for key in ("plugins", "skills", "belegschaft", "autopilot", "sicherheit",
                "bodyguards", "finanzen", "modell", "modell_modus", "logs",
                "boss_modell", "worker_modell"):
        assert key in s, f"Feld {key} fehlt in /api/state"
    assert isinstance(s["plugins"], list) and s["plugins"]
    # Boss/Worker sind sichtbar und nicht leer (Worte statt exaktes Modell, da
    # der aktive Boss-Name durch Fallback variieren kann).
    assert s["boss_modell"] and s["worker_modell"]


def test_all_pages_and_static_served(client):
    for path in ("/", "/uebersicht", "/gehirn", "/mitarbeiter", "/werkzeuge",
                 "/autopilot", "/sicherheit"):
        r = client.get(path)
        assert r.status_code == 200, f"Seite {path} nicht erreichbar"
        assert "<html" in r.text.lower()
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/fable.js").status_code == 200
    assert client.get("/favicon.ico").status_code == 200


def test_host_guard_blocks_dns_rebinding(client):
    r = client.get("/api/state", headers={"host": "evil.example.com"})
    assert r.status_code == 403
    r = client.get("/api/state", headers={"host": "localhost:8000"})
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Aufgaben-API
# ---------------------------------------------------------------------------

def test_task_lifecycle(client):
    r = client.post("/api/task", json={"beschreibung": "!plugin calc eval expression=6*7"})
    assert r.status_code == 200
    t = _wait_done(client, r.json()["id"])
    assert t["status"] == "fertig" and t["ergebnis"] == "42"


def test_task_empty_description_rejected(client):
    assert client.post("/api/task", json={"beschreibung": "   "}).status_code == 400


def test_task_invalid_address_rejected_and_worker_survives(client):
    """Regression: ungültige Adresse hat früher einen Worker-Slot getötet
    (materialize außerhalb des try) — die Aufgabe verschwand kommentarlos."""
    r = client.post("/api/task", json={"beschreibung": "hallo", "adresse": "nicht-numerisch"})
    assert r.status_code == 400
    assert "Adresse" in r.json()["detail"]
    # Adressen außerhalb des Adressraums ebenfalls abgelehnt
    r = client.post("/api/task", json={"beschreibung": "x", "adresse": "100000000000"})
    assert r.status_code == 400
    # System bleibt voll funktionsfähig
    r = client.post("/api/task", json={"beschreibung": "!plugin calc eval expression=1+1"})
    assert r.status_code == 200
    assert _wait_done(client, r.json()["id"])["ergebnis"] == "2"


def test_orchestrator_worker_survives_invalid_address(tmp_path):
    """Regression: mit nur EINEM Worker muss nach einer ungültigen Adresse
    die nächste Aufgabe trotzdem verarbeitet werden (vorher: toter Worker,
    queue.join() hing für immer)."""
    import asyncio
    from jarvis.core.orchestrator import Orchestrator

    async def scenario():
        orch = Orchestrator(tmp_path, max_active=1)
        await orch.start()
        bad = orch.submit("test", address="abc")
        good = orch.submit("!plugin calc eval expression=2+3")
        await asyncio.wait_for(orch.queue.join(), timeout=10)
        await orch.stop()
        return bad, good

    bad, good = asyncio.run(scenario())
    assert bad.status == "fehler" and "Ungültige" in bad.result
    assert good.status == "fertig" and good.result == "5"


def test_task_not_found(client):
    assert client.get("/api/task/999999").status_code == 404


# ---------------------------------------------------------------------------
# Mitarbeiter / Organisation
# ---------------------------------------------------------------------------

def test_employee_endpoint(client):
    r = client.get("/api/employee/42")
    assert r.status_code == 200
    e = r.json()
    assert e["adresse"] == "42" and e["name"] and e["team"]
    assert isinstance(e["plugins_autorisiert"], list)
    # hierarchische Adresse über {address:path}
    assert client.get("/api/employee/42/777/31337").status_code == 200
    # ungültig -> 400, kein 500
    assert client.get("/api/employee/abc").status_code == 400
    assert client.get("/api/employee/100000000000").status_code == 400


def test_org_endpoint_clamps_count(client):
    r = client.get("/api/org/7?count=99999")
    assert r.status_code == 200
    assert len(r.json()["mitarbeiter_auszug"]) <= 50
    assert client.get("/api/org/xyz").status_code == 400


def test_memory_endpoint_clamps_limit(client):
    r = client.get("/api/memory?limit=99999")
    assert r.status_code == 200
    assert len(r.json()["eintraege"]) <= 100


def test_business_endpoint_honest(client):
    b = client.get("/api/business").json()
    assert "hinweis" in b and "umsatz_chf_real" in b
    assert b["umsatz_chf_real"] == b["saldo_chf_real"] + b["kosten_chf_real"]


# ---------------------------------------------------------------------------
# Sicherheit (dürfen plattformunabhängig nie 500 werfen)
# ---------------------------------------------------------------------------

def test_security_endpoints_never_500(client):
    r = client.post("/api/security/check")
    assert r.status_code == 200 and "zeit" in r.json()
    for action in ("scan", "signatures", "update", "threats", "remove", "fullscan"):
        r = client.post(f"/api/security/{action}")
        assert r.status_code == 200, f"/api/security/{action} -> {r.status_code}"
        assert isinstance(r.json()["ergebnis"], str)


# ---------------------------------------------------------------------------
# Gehirn / Fable-5-Key
# ---------------------------------------------------------------------------

def test_brain_status(client):
    b = client.get("/api/brain").json()
    assert b["modus"] in ("api", "offline") and b["modell"]


def test_brain_key_too_short_rejected(client):
    assert client.post("/api/brain/key", json={"schluessel": "kurz"}).status_code == 400


def test_openrouter_key_endpoint(client, monkeypatch):
    """OpenRouter-Key über das Dashboard setzen: Status, Validierung, Aktivierung."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    # zu kurz -> 400
    assert client.post("/api/modelle/key", json={"schluessel": "kurz"}).status_code == 400
    # gültig -> aktiv true, Env gesetzt
    r = client.post("/api/modelle/key", json={"schluessel": "sk-or-test-1234567890"})
    assert r.status_code == 200 and r.json()["aktiv"] is True
    assert os.environ.get("OPENROUTER_API_KEY") == "sk-or-test-1234567890"
    # Status-Endpoint spiegelt das wider
    assert client.get("/api/modelle/key").json()["aktiv"] is True


def test_fortschritt_top_and_employee_level(client):
    """Bestenliste-Endpunkt + Level-Felder in der Mitarbeiter-Identität."""
    # eine echte Aufgabe erledigen -> Mitarbeiter verdient XP
    t = client.post("/api/task", json={"beschreibung": "!plugin calc eval expression=8*8",
                                        "adresse": "555"}).json()
    _wait_done(client, t["id"])
    board = client.get("/api/fortschritt/top").json()
    assert "bestenliste" in board and board["summe"]["aufgaben_gesamt"] >= 1
    # Mitarbeiter-Identität trägt Level/Meisterschaft
    e = client.get("/api/employee/555").json()
    assert 1 <= e["level"] <= 99 and e["meisterschaft"]
    assert e["erledigte_aufgaben"] >= 1


def test_teammode_toggle(client):
    """Team-Modus an/aus über das Dashboard schaltbar."""
    assert client.post("/api/teammode", json={"schluessel": "an"}).json()["an"] is True
    assert client.get("/api/teammode").json()["an"] is True
    assert client.post("/api/teammode", json={"schluessel": "aus"}).json()["an"] is False


def test_teams_endpoint(client):
    d = client.get("/api/teams").json()
    assert d["anzahl_teams"] == 25 and len(d["teams"]) == 25
    assert all("chef" in t and "team" in t for t in d["teams"])


def test_training_build_endpoint(client):
    """Datensatz-Bau per Klick liefert eine gültige Antwort (auch bei 0 Beispielen)."""
    r = client.post("/api/training/build")
    assert r.status_code == 200
    d = r.json()
    assert "beispiele" in d and "hinweis" in d and "datei" in d


def test_voice_endpoints(client, monkeypatch):
    """Echte Stimme (ElevenLabs): Status, Key setzen, Fallback ohne Key (204)."""
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    # Standard-Stimm-ID ist die vorgegebene
    st = client.get("/api/voice/status").json()
    assert st["aktiv"] is False and st["stimm_id"] == "hx3VHMzUAVVvishlV9u9"
    # ohne Key -> 204 (Weboberfläche nutzt dann Browser-Stimme)
    assert client.post("/api/voice/say", json={"schluessel": "hallo"}).status_code == 204
    # Key + Stimm-ID setzen -> aktiv
    r = client.post("/api/voice/key",
                    json={"schluessel": "11labs-test-key-123", "stimm_id": "abc123voiceid"})
    assert r.status_code == 200 and r.json()["aktiv"] is True
    assert r.json()["stimm_id"] == "abc123voiceid"
    # zu kurzer Key -> 400
    assert client.post("/api/voice/key", json={"schluessel": "x"}).status_code == 400


# ---------------------------------------------------------------------------
# Claw-Code-Route: End-to-End über das Dashboard
# ---------------------------------------------------------------------------

def test_clawcode_route_gated_without_dangerous(client, monkeypatch):
    """'!plugin code' ist gefährlich und muss ohne Freischaltung sauber sperren
    (Fehler-Status mit Hinweis, kein 500, kein toter Worker)."""
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    r = client.post("/api/task", json={"beschreibung": "!plugin code prompt prompt=schreibe test"})
    assert r.status_code == 200
    t = _wait_done(client, r.json()["id"])
    assert t["status"] == "fehler" and "gesperrt" in t["ergebnis"].lower()


def test_clawcode_natural_language_routed(client, monkeypatch):
    """'claw code …' in freier Sprache wird erkannt und auf die Code-Route geleitet."""
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    r = client.post("/api/task", json={"beschreibung": "claw code hallo welt"})
    assert r.status_code == 200
    t = _wait_done(client, r.json()["id"])
    # ohne Freischaltung: klarer Sperr-Hinweis statt Absturz
    assert t["status"] == "fehler" and "gesperrt" in t["ergebnis"].lower()


def test_clawcode_fallback_without_binary(client, monkeypatch, tmp_path):
    """Mit Freischaltung, aber ohne Binary/Key: ehrlicher Fallback über das Gehirn."""
    monkeypatch.setenv("JARVIS_ALLOW_DANGEROUS", "1")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from jarvis.dashboard.app import orchestrator
    code = orchestrator.plugins.plugins["code"]
    monkeypatch.setattr(code, "binary", None)
    r = client.post("/api/task", json={"beschreibung": "!plugin code prompt prompt=sag hallo"})
    t = _wait_done(client, r.json()["id"])
    assert t["status"] == "fertig"
    assert "Binary nicht gefunden" in t["ergebnis"] or "kein API-Key" in t["ergebnis"]


def test_zugaenge_vault_crud(client):
    """Zugang speichern -> in Liste (maskiert, ohne Klartext-Passwort) -> löschen."""
    r = client.post("/api/zugaenge", json={
        "plattform": "instagram", "benutzer": "meinuser", "passwort": "geheim12345"})
    assert r.status_code == 200 and r.json()["gespeichert"] is True

    d = client.get("/api/zugaenge").json()
    plats = [z["plattform"] for z in d["zugaenge"]]
    assert "instagram" in plats
    # Übersicht enthält NIE das Klartext-Passwort
    assert "geheim12345" not in r.text
    body = client.get("/api/zugaenge").text
    assert "geheim12345" not in body and "meinuser" not in body  # nur maskiert

    r2 = client.delete("/api/zugaenge/instagram")
    assert r2.status_code == 200 and r2.json()["geloescht"] is True


def test_zugaenge_login_command_routed(client, monkeypatch):
    """'logge dich bei X ein' wird als Login-Aktion erkannt (Gate greift ohne Freischaltung)."""
    monkeypatch.delenv("JARVIS_ALLOW_PC", raising=False)
    monkeypatch.delenv("JARVIS_ALLOW_DANGEROUS", raising=False)
    client.post("/api/zugaenge", json={
        "plattform": "github", "benutzer": "u", "passwort": "pw1234567890"})
    r = client.post("/api/task", json={"beschreibung": "hey jarvis logge dich bei github ein"})
    assert r.status_code == 200
    t = _wait_done(client, r.json()["id"])
    # ohne Freischaltung: ehrlicher Sperrhinweis, kein Absturz
    assert t["status"] == "fehler" and "gesperrt" in t["ergebnis"].lower()
    client.delete("/api/zugaenge/github")
