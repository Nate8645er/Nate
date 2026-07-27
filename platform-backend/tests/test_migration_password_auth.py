"""Struktur-Test der Passwort-Auth-Migration (ohne laufende DB). Der echte
Laufzeit-Beweis steht in test_auth_integration.py."""
import pathlib

MIG = (
    pathlib.Path(__file__).resolve().parent.parent
    / "migrations"
    / "012_password_auth.sql"
).read_text(encoding="utf-8")


def test_password_hash_column_is_nullable():
    # Kein NOT NULL -- bestehende, per /admin/provision oder Webhook
    # angelegte Zeilen haben (noch) kein Passwort und muessen gueltig bleiben.
    assert "ADD COLUMN IF NOT EXISTS password_hash text" in MIG
    assert "password_hash text NOT NULL" not in MIG


def test_sessions_table_stores_only_a_hash_never_cleartext():
    assert "token_hash" in MIG
    assert "token_clear" not in MIG and "token_plain" not in MIG


def test_user_directory_has_no_password_column():
    # Der RLS-freie E-Mail-Lookup darf KEIN Geheimnis enthalten -- der
    # eigentliche password_hash bleibt in `users` (RLS-gebunden).
    block = MIG.split("CREATE TABLE IF NOT EXISTS user_directory")[1].split(");")[0]
    assert "password" not in block


def test_user_directory_email_is_globally_unique():
    block = MIG.split("CREATE TABLE IF NOT EXISTS user_directory")[1].split(");")[0]
    assert "email_lower text PRIMARY KEY" in block


def test_users_table_is_not_exempted_from_rls_here():
    # Diese Migration darf `users` NICHT von RLS ausnehmen -- app/billing.py
    # (resolve_metadata_tenant) verlaesst sich beim Stripe-Metadaten-Haerten
    # darauf, dass `users` weiterhin RLS-gefiltert ist.
    assert "DISABLE ROW LEVEL SECURITY" not in MIG
    # Die EINZIGE Beruehrung von `users` in dieser Migration darf das
    # Hinzufuegen der password_hash-Spalte sein.
    assert MIG.count("ALTER TABLE users") == 1


def test_new_tables_granted_to_app_rw():
    assert "GRANT SELECT, INSERT, DELETE ON user_directory TO app_rw" in MIG
    assert "sessions TO app_rw" in MIG
