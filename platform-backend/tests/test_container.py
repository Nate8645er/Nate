"""Tests: Container-/Compose-Invarianten (Phase 9 · Containerisierung).

Sichert die Härtungs-Vorgaben im Dockerfile und docker-compose gegen
Regressionen — passend zum k8s-securityContext (uid 10001, non-root, cap-drop).
"""

import os

import pytest

yaml = pytest.importorskip("yaml")

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _read(rel: str) -> str:
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def test_dockerfile_ist_multistage_und_nonroot():
    df = _read("Dockerfile")
    assert "AS builder" in df and "AS runtime" in df, "Multi-Stage erwartet"
    # Non-root: uid 10001 muss zum Deployment (runAsUser: 10001) passen.
    assert "10001" in df
    assert "USER 10001" in df
    # uvicorn als Entrypoint auf 0.0.0.0:8000.
    assert "uvicorn" in df and "8000" in df
    assert "HEALTHCHECK" in df


def test_dockerfile_uid_passt_zu_k8s_deployment():
    df = _read("Dockerfile")
    dep = None
    for doc in yaml.safe_load_all(_read("deploy/k8s/backend.yaml")):
        if doc and doc.get("kind") == "Deployment":
            dep = doc
            break
    assert dep is not None
    run_as = dep["spec"]["template"]["spec"]["securityContext"]["runAsUser"]
    assert str(run_as) in df, "Dockerfile-USER muss zu runAsUser im Deployment passen"


def test_dockerignore_schliesst_ballast_aus():
    di = _read(".dockerignore")
    for pattern in ["tests/", ".venv/", "deploy/", "requirements-dev.txt"]:
        assert pattern in di, f"{pattern} sollte nicht ins Image"


def test_compose_backend_ist_gehaertet():
    compose = yaml.safe_load(_read("docker-compose.dev.yml"))
    backend = compose["services"]["backend"]
    assert backend["user"] == "10001:10001"
    assert backend["read_only"] is True
    assert "no-new-privileges:true" in backend["security_opt"]
    assert backend["cap_drop"] == ["ALL"]
    # Kein echtes Secret als Klartext, das wie ein Produktions-Key aussieht.
    for _k, v in backend["environment"].items():
        assert "sk-" not in str(v) and "BEGIN" not in str(v)


def test_ci_hat_lint_sast_und_docker_gate():
    ci = _read(os.path.join("..", ".github", "workflows", "platform-backend.yml"))
    assert "ruff check" in ci
    assert "bandit" in ci
    assert "build-push-action" in ci
    assert "health/live" in ci  # Smoke-Test des gebauten Images
