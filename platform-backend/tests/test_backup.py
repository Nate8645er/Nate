"""Tests: Backup/Restore-Logik (offline, injizierter Runner)."""

from app.platform.backup import (
    backup_postgres,
    redact_dsn,
    restore_postgres,
)

DSN = "postgresql://user:s3cret@db.example:5432/platform"


def test_redact_dsn_entfernt_passwort():
    assert redact_dsn(DSN) == "postgresql://user:***@db.example:5432/platform"
    # Ohne Passwort unverändert.
    assert redact_dsn("postgresql://user@h/db") == "postgresql://user@h/db"


def test_backup_postgres_baut_sicheres_kommando():
    calls = []

    def runner(argv, env):
        calls.append((list(argv), dict(env)))
        return 0, "", ""

    res = backup_postgres(DSN, "/backups/pf.dump", runner=runner)
    assert res.ok
    argv, env = calls[0]
    # Passwort NIE in argv (Prozessliste!), sondern nur in PGPASSWORD-Env.
    assert "s3cret" not in " ".join(argv)
    assert env["PGPASSWORD"] == "s3cret"
    # Custom-Format + Zielpfad + Verbindungsflags.
    assert argv[0] == "pg_dump"
    assert "-Fc" in argv
    assert argv[-2:] == ["-f", "/backups/pf.dump"]
    assert "-h" in argv and "db.example" in argv
    assert "-p" in argv and "5432" in argv
    assert "-U" in argv and "user" in argv
    assert "-d" in argv and "platform" in argv


def test_backup_postgres_meldet_fehler_ehrlich():
    def runner(_argv, _env):
        return 1, "", "connection refused"

    res = backup_postgres(DSN, "/x.dump", runner=runner)
    assert not res.ok
    assert "connection refused" in res.detail


def test_backup_lehnt_nicht_postgres_dsn_ab():
    res = backup_postgres("mysql://u:p@h/db", "/x.dump", runner=lambda a, e: (0, "", ""))
    assert not res.ok
    assert "Postgres" in res.detail


def test_restore_postgres_clean_flags():
    calls = []

    def runner(argv, env):
        calls.append(list(argv))
        return 0, "", ""

    res = restore_postgres(DSN, "/backups/pf.dump", runner=runner, clean=True)
    assert res.ok
    argv = calls[0]
    assert argv[0] == "pg_restore"
    assert "--clean" in argv and "--if-exists" in argv
    assert argv[-1] == "/backups/pf.dump"
    assert "s3cret" not in " ".join(argv)
