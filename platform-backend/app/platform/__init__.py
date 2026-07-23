"""platform/ — Tenancy, RBAC, Quota, Audit (Phase 6, implementiert).

- auth.py     : Keycloak/OIDC-Token-Verify → Principal (tenant, roles)
- rbac.py     : Rollen → Rechte, require()
- tenancy.py  : TenantRepository (Code-Ebene) + Postgres-RLS (DB-Ebene)
- quota.py    : Kontingente pro Tenant/Tag
- audit.py    : append-only Audit-Log (In-Memory + SQL)

Mandantentrennung ist zweifach abgesichert (Code + DB-RLS).
"""
