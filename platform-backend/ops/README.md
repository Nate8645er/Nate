# Betrieb — Backup & Wiederherstellung (Phase 7)

## Backup

```bash
DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/platform \
  ops/backup.sh ./backups
```

Nutzt `pg_dump --format=custom`, schliesst `schema_migrations` bewusst aus
(Begründung siehe Kommentar in `backup.sh`). Für einen Produktivbetrieb als
Cron/Scheduled-Job einplanen (z. B. täglich) und die Dumps versioniert extern
ablegen (nicht im selben Cluster wie die Quelle).

## Restore

```bash
DATABASE_URL_ADMIN=postgresql://postgres:...@host:5432/<ziel-db> \
  ops/restore.sh backups/platform_<stamp>.dump

# Pflicht-Folgeschritt: Rollen/Grants wiederherstellen (das Skript weist
# selbst darauf hin). schema_migrations ist nicht im Dump -> migrate()
# laeuft vollstaendig neu, sicher weil jede Migration idempotent ist:
MIGRATE_DATABASE_URL=<privilegiert> DATABASE_URL=<app_rw-Verbindung> \
  python -m app.migrate
```

**Wichtig:** Niemals ungeprüft gegen eine Produktions-Zieldatenbank
restaurieren. Für die Wiederherstellungsprobe eine frische, temporäre
Datenbank verwenden (`ops/restore.sh` erwartet keine bestehenden Daten im
Ziel — `pg_restore --clean --if-exists` räumt vorher auf).

## Wiederherstellungsprobe — durchgeführt und bestätigt

Der komplette Zyklus wurde real ausgeführt (nicht nur beschrieben):

1. Mandant + Agent über die laufende Anwendung angelegt (Quelle: temporärer
   Postgres-Cluster, DB `platform`).
2. `ops/backup.sh` → Dump geschrieben (Custom-Format, ohne `schema_migrations`).
3. Frische, leere Ziel-DB (`restore_target`) angelegt.
4. `ops/restore.sh` → Daten + Schema + RLS-Policies wiederhergestellt.
5. `python -m app.migrate` gegen die Ziel-DB → Rolle `app_rw` + alle Grants
   erneut gesetzt (bewusst getestet: **ohne** diesen Schritt schlägt der
   Zugriff mit `permission denied` fehl — deshalb ist er im Skript-Output
   als Pflichtschritt vermerkt, nicht optional).
6. Verbindung als `app_rw` gegen die Ziel-DB: derselbe Mandant (gleiche
   UUID), derselbe Agent sind vorhanden. Ohne gesetzten Mandantenkontext
   liefert `agents` **0 Zeilen** — RLS ist nach dem Restore weiterhin wirksam,
   nicht nur die Rohdaten sind da.

Ergebnis: **Backup → Restore → Rechte → RLS** funktioniert durchgängig und
ist nicht nur behauptet, sondern einmal vollständig durchgespielt.

## Monitoring / Lasttest (bewusst offen)

- Monitoring: `/health` liefert Liveness + DB-Erreichbarkeit; strukturierte
  Logs über `logging` (siehe `app/routes/chat.py`, `app/billing.py`). Anbindung
  an Grafana/Prometheus (Master-Prompt Kap. 3.2) ist noch nicht umgesetzt.
- Lasttest: noch nicht durchgeführt — braucht eine laufende Umgebung mit
  echtem LiteLLM-Gateway, die hier nicht verfügbar ist.
