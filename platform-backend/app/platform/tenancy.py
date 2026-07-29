"""Mandantentrennung (Auftrag §6) — zwei Ebenen, Defense in Depth.

1. **DB-Ebene (Postgres RLS):** jede Tenant-Tabelle bekommt eine Policy
   `tenant_id = current_setting('app.current_tenant')`. Selbst bei einem
   Code-Fehler kann die DB keine fremden Zeilen liefern. SQL in `RLS_SQL` /
   `sql/tenancy_rls.sql`.
2. **Code-Ebene:** `TenantRepository` stempelt jeden Schreibzugriff mit der
   Tenant-ID und filtert JEDEN Lesezugriff darauf. Ohne Tenant kein Zugriff.

Getestet wird die Code-Ebene auf SQLite (RLS ist Postgres-spezifisch); die
RLS-SQL ist der zusätzliche Schutz in Produktion.
"""

from __future__ import annotations

import uuid

from sqlalchemy import JSON, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class TenantRecord(Base):
    __tablename__ = "tenant_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    data: Mapped[dict] = mapped_column(JSON, default=dict)


#: Postgres-RLS für Tenant-Tabellen. In Produktion einmal ausführen.
RLS_SQL = """
ALTER TABLE tenant_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_records FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_isolation ON tenant_records;
CREATE POLICY tenant_isolation ON tenant_records
  USING (tenant_id = current_setting('app.current_tenant', true))
  WITH CHECK (tenant_id = current_setting('app.current_tenant', true));
""".strip()


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)


class TenantRepository:
    """Alle Zugriffe sind auf genau einen Tenant beschränkt."""

    def __init__(self, session: Session, tenant: str) -> None:
        if not tenant:
            raise ValueError("TenantRepository verlangt einen tenant")
        self._session = session
        self._tenant = tenant

    def add(self, kind: str, data: dict) -> TenantRecord:
        rec = TenantRecord(id=str(uuid.uuid4()), tenant_id=self._tenant, kind=kind, data=data)
        self._session.add(rec)
        self._session.flush()
        return rec

    def list(self, kind: str | None = None) -> list[TenantRecord]:
        stmt = select(TenantRecord).where(TenantRecord.tenant_id == self._tenant)
        if kind is not None:
            stmt = stmt.where(TenantRecord.kind == kind)
        return list(self._session.scalars(stmt))

    def get(self, record_id: str) -> TenantRecord | None:
        rec = self._session.get(TenantRecord, record_id)
        # Isolation: fremde Tenant-Zeile wird nie zurückgegeben.
        return rec if rec and rec.tenant_id == self._tenant else None


def set_tenant_guc(session: Session, tenant: str) -> None:
    """Setzt die Postgres-Session-Variable für RLS. No-op auf Nicht-Postgres."""
    if session.bind is not None and session.bind.dialect.name == "postgresql":
        from sqlalchemy import text

        session.execute(text("SELECT set_config('app.current_tenant', :t, true)"), {"t": tenant})
