"""Backup & Restore (Phase 8 · Hardening).

Zwei zustandsbehaftete Speicher müssen gesichert werden:
- **Postgres** (Plattform-/Tenant-Metadaten, Audit-Log): logisches Dump via
  `pg_dump`/`pg_restore` (custom-Format `-Fc`, komprimiert, selektiv rücksicher).
- **Qdrant** (Vektoren pro Mandant): Snapshot-API des Servers (pro Collection).

Design:
- **Kein Secret im Code/Log.** Passwörter kommen über die Umgebung
  (`PGPASSWORD`), nicht über die Kommandozeile (dort wären sie in der
  Prozessliste sichtbar). Die DSN wird für die Anzeige/Logs redigiert.
- **Kommando-Ausführung ist injizierbar** (`runner`) und läuft mit `shell=False`
  und festen Argumentlisten (keine Shell-Injection) — offline testbar.
- Ehrliche Fehler: fehlt ein Werkzeug/Dienst, wird das klar gemeldet.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

#: Ein Runner führt eine Argumentliste aus und gibt (returncode, stdout, stderr).
#: `env` sind ZUSÄTZLICHE Umgebungsvariablen (z. B. PGPASSWORD) — nie in argv.
Runner = Callable[[Sequence[str], dict[str, str]], tuple[int, str, str]]


def default_runner(argv: Sequence[str], env: dict[str, str]) -> tuple[int, str, str]:
    import os

    merged = {**os.environ, **env}
    proc = subprocess.run(  # noqa: S603 — feste Argv, shell=False, kein User-Input in argv[0]
        list(argv), capture_output=True, text=True, env=merged, timeout=600
    )
    return proc.returncode, proc.stdout, proc.stderr


def redact_dsn(dsn: str) -> str:
    """Entfernt das Passwort aus einer DSN für Logs/Anzeige."""
    try:
        p = urlparse(dsn)
    except ValueError:
        return "<ungültige DSN>"
    if p.password:
        netloc = p.netloc.replace(f":{p.password}@", ":***@")
        p = p._replace(netloc=netloc)
    return urlunparse(p)


@dataclass(frozen=True)
class BackupResult:
    ok: bool
    detail: str
    target: str  # z. B. Dateipfad oder Snapshot-Name


def _split_dsn(dsn: str) -> tuple[list[str], dict[str, str]]:
    """Zerlegt eine Postgres-DSN in `pg_*`-Flags + `PGPASSWORD`-Env (nie in argv)."""
    p = urlparse(dsn)
    if p.scheme not in ("postgres", "postgresql"):
        raise ValueError(f"keine Postgres-DSN: {p.scheme or 'leer'}")
    args: list[str] = []
    if p.hostname:
        args += ["-h", p.hostname]
    if p.port:
        args += ["-p", str(p.port)]
    if p.username:
        args += ["-U", p.username]
    db = (p.path or "/").lstrip("/")
    if db:
        args += ["-d", db]
    env = {"PGPASSWORD": p.password} if p.password else {}
    return args, env


def backup_postgres(
    dsn: str,
    out_path: str,
    runner: Runner = default_runner,
) -> BackupResult:
    """Sichert die DB als komprimiertes custom-Format-Dump (`pg_dump -Fc`)."""
    try:
        conn_args, env = _split_dsn(dsn)
    except ValueError as exc:
        return BackupResult(False, str(exc), out_path)
    argv = ["pg_dump", "-Fc", "--no-owner", "--no-privileges", *conn_args, "-f", out_path]
    code, _out, err = runner(argv, env)
    if code != 0:
        return BackupResult(False, f"pg_dump fehlgeschlagen (rc={code}): {err.strip()}", out_path)
    return BackupResult(True, f"Dump geschrieben ({redact_dsn(dsn)})", out_path)


def restore_postgres(
    dsn: str,
    in_path: str,
    runner: Runner = default_runner,
    clean: bool = True,
) -> BackupResult:
    """Spielt ein `pg_dump -Fc`-Dump zurück (`pg_restore`)."""
    try:
        conn_args, env = _split_dsn(dsn)
    except ValueError as exc:
        return BackupResult(False, str(exc), in_path)
    argv = ["pg_restore", "--no-owner", "--no-privileges"]
    if clean:
        argv += ["--clean", "--if-exists"]
    argv += [*conn_args, in_path]
    code, _out, err = runner(argv, env)
    if code != 0:
        return BackupResult(False, f"pg_restore fehlgeschlagen (rc={code}): {err.strip()}", in_path)
    return BackupResult(True, f"Restore eingespielt ({redact_dsn(dsn)})", in_path)


def snapshot_qdrant(client, collection: str) -> BackupResult:
    """Erstellt einen Server-seitigen Snapshot einer Qdrant-Collection.

    `client` ist ein `qdrant_client.QdrantClient`. Der Snapshot liegt im
    Storage des Servers und kann von dort gesichert/zurückgespielt werden.
    """
    try:
        if not client.collection_exists(collection):
            return BackupResult(False, f"Collection '{collection}' existiert nicht", collection)
        desc = client.create_snapshot(collection_name=collection)
        name = getattr(desc, "name", None) or str(desc)
        return BackupResult(True, f"Qdrant-Snapshot erstellt: {name}", name)
    except Exception as exc:  # noqa: BLE001 — ehrlicher Fehler an der Schichtgrenze
        return BackupResult(False, f"Qdrant-Snapshot fehlgeschlagen: {exc}", collection)


def list_qdrant_snapshots(client, collection: str) -> list[str]:
    """Listet vorhandene Snapshots einer Collection (Namen)."""
    snaps = client.list_snapshots(collection_name=collection)
    return [getattr(s, "name", str(s)) for s in snaps]
