"""Tests: k8s/k3s-Manifeste — Syntax + Sicherheits-/Betriebs-Invarianten.

Verhindert Regressionen an den Härtungs-Vorgaben (Phase 8): non-root, gedroppte
Capabilities, Ressourcen-Limits, echte Liveness/Readiness und KEINE Klartext-
Secrets im Git.
"""

import glob
import os

import pytest

yaml = pytest.importorskip("yaml")

K8S_DIR = os.path.join(os.path.dirname(__file__), "..", "deploy", "k8s")


def _load_all() -> list[dict]:
    docs: list[dict] = []
    for f in sorted(glob.glob(os.path.join(K8S_DIR, "*.yaml"))):
        docs.extend(d for d in yaml.safe_load_all(open(f, encoding="utf-8")) if d)
    return docs


def _by_kind(kind: str) -> list[dict]:
    return [d for d in _load_all() if d.get("kind") == kind]


def test_alle_manifeste_parsen():
    docs = _load_all()
    assert len(docs) >= 5
    for d in docs:
        assert "kind" in d and "apiVersion" in d


def test_deployment_ist_non_root_und_gehaertet():
    dep = _by_kind("Deployment")[0]
    pod = dep["spec"]["template"]["spec"]
    assert pod["securityContext"]["runAsNonRoot"] is True
    c = pod["containers"][0]
    sc = c["securityContext"]
    assert sc["allowPrivilegeEscalation"] is False
    assert sc["readOnlyRootFilesystem"] is True
    assert sc["capabilities"]["drop"] == ["ALL"]


def test_deployment_hat_probes_und_limits():
    c = _by_kind("Deployment")[0]["spec"]["template"]["spec"]["containers"][0]
    assert c["livenessProbe"]["httpGet"]["path"] == "/health/live"
    assert c["readinessProbe"]["httpGet"]["path"] == "/health/ready"
    # Ressourcen-Limits gesetzt (kein unbegrenzter Verbrauch).
    assert c["resources"]["limits"]["cpu"]
    assert c["resources"]["limits"]["memory"]
    assert c["resources"]["requests"]["memory"]


def test_rollout_ist_zero_downtime():
    ru = _by_kind("Deployment")[0]["spec"]["strategy"]["rollingUpdate"]
    assert ru["maxUnavailable"] == 0  # Readiness-Gate schützt Traffic
    assert _by_kind("Deployment")[0]["spec"]["replicas"] >= 2


def test_keine_klartext_secrets_im_git():
    # Das Secret existiert als Schnittstelle, aber ohne echte Werte.
    secret = _by_kind("Secret")[0]
    for _k, v in (secret.get("stringData") or {}).items():
        assert v == "", "Secret-Manifest enthält einen Klartext-Wert — verboten!"


def test_prometheus_scrape_annotation():
    tmpl = _by_kind("Deployment")[0]["spec"]["template"]["metadata"]["annotations"]
    assert tmpl["prometheus.io/scrape"] == "true"
    assert tmpl["prometheus.io/path"] == "/metrics"


def test_pod_security_restricted_und_pdb():
    ns = _by_kind("Namespace")[0]
    assert ns["metadata"]["labels"]["pod-security.kubernetes.io/enforce"] == "restricted"
    assert _by_kind("PodDisruptionBudget"), "PDB fehlt (Schutz bei Node-Drain)"
