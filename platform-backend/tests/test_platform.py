"""Tests Phase 6: RBAC, Tenancy-Isolation (SQLite), Quota, Audit."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.platform.audit import InMemoryAuditLog, SqlAuditLog
from app.platform.auth import Principal
from app.platform.quota import QuotaExceeded, QuotaManager
from app.platform.rbac import (
    Permission,
    PermissionDenied,
    has_permission,
    require,
)
from app.platform.tenancy import TenantRepository, create_all


def _principal(roles):
    return Principal(subject="u1", tenant="t1", roles=frozenset(roles), email=None)


# ---------------- RBAC ----------------
def test_rollen_rechte():
    viewer = _principal(["viewer"])
    member = _principal(["member"])
    owner = _principal(["owner"])
    assert has_permission(viewer, Permission.KNOWLEDGE_READ) is True
    assert has_permission(viewer, Permission.KNOWLEDGE_WRITE) is False
    assert has_permission(member, Permission.AGENT_RUN) is True
    assert has_permission(member, Permission.APPROVAL_DECIDE) is False
    assert has_permission(owner, Permission.BILLING_MANAGE) is True


def test_require_wirft_ohne_recht():
    with pytest.raises(PermissionDenied):
        require(_principal(["viewer"]), Permission.AGENT_RUN)
    require(_principal(["member"]), Permission.AGENT_RUN)  # kein Fehler


# ---------------- Tenancy-Isolation (Code-Ebene, SQLite) ----------------
@pytest.fixture()
def session():
    engine = create_engine("sqlite://")
    create_all(engine)
    with Session(engine) as s:
        yield s


def test_tenant_repository_isoliert(session):
    repo_a = TenantRepository(session, "tenant-a")
    repo_b = TenantRepository(session, "tenant-b")
    a1 = repo_a.add("note", {"text": "geheim A"})
    repo_b.add("note", {"text": "geheim B"})
    session.flush()

    # A sieht nur A
    assert [r.data["text"] for r in repo_a.list("note")] == ["geheim A"]
    assert [r.data["text"] for r in repo_b.list("note")] == ["geheim B"]
    # B kann A's Datensatz nicht per ID holen
    assert repo_b.get(a1.id) is None
    assert repo_a.get(a1.id) is not None


def test_repository_verlangt_tenant(session):
    with pytest.raises(ValueError):
        TenantRepository(session, "")


# ---------------- Quota ----------------
def test_quota_pro_tenant_und_ressource():
    q = QuotaManager(limits={"missions": 3, "tokens": 1000})
    assert q.remaining("t1", "missions") == 3
    q.consume("t1", "missions", 2)
    assert q.remaining("t1", "missions") == 1
    assert q.allow("t1", "missions", 2) is False
    with pytest.raises(QuotaExceeded):
        q.consume("t1", "missions", 2)
    # anderer Tenant unberührt
    assert q.remaining("t2", "missions") == 3


def test_quota_unbekannte_ressource():
    q = QuotaManager(limits={"tokens": 10})
    with pytest.raises(KeyError):
        q.remaining("t1", "storage")


def test_quota_tageswechsel_setzt_zurueck():
    tag = {"d": "2026-01-01"}
    q = QuotaManager(limits={"missions": 2}, _today=lambda: tag["d"])
    q.consume("t1", "missions", 2)
    assert q.remaining("t1", "missions") == 0
    tag["d"] = "2026-01-02"
    assert q.remaining("t1", "missions") == 2  # neuer Tag


# ---------------- Audit ----------------
def test_audit_inmemory_append_only_und_isoliert():
    log = InMemoryAuditLog(now=lambda: 1000)
    log.record("t1", "u1", "agent.run", "run-1")
    log.record("t2", "u9", "agent.run", "run-9")
    log.record("t1", "u1", "approval.approve", "apr-1")
    t1 = log.list("t1")
    assert len(t1) == 2
    assert t1[0].action == "approval.approve"  # neueste zuerst
    assert all(e.tenant == "t1" for e in t1)


def test_audit_verlangt_tenant():
    with pytest.raises(ValueError):
        InMemoryAuditLog().record("", "u", "a", "r")


def test_sql_audit_schreibt_und_liest(session):
    log = SqlAuditLog(session, now=lambda: 500)
    log.record("t1", "u1", "agent.run", "run-1", {"tokens": 42})
    log.record("t2", "u2", "agent.run", "run-2")
    session.flush()
    rows = log.list("t1")
    assert len(rows) == 1
    assert rows[0].detail == {"tokens": 42}
    assert log.list("t2")[0].tenant == "t2"
