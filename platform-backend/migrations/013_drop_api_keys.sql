-- Entfernt das API-Schluessel-Konzept vollstaendig aus der Plattform --
-- Produktentscheidung: Session-Cookie-Login (E-Mail+Passwort,
-- `012_password_auth.sql`) ist jetzt der EINZIGE Authentifizierungsweg, auch
-- fuer Entwickler-/Programmzugriff. Es gibt kein Nebeneinander mehr.
--
-- Diese Migration ist ein echtes DROP, kein "deprecated liegen lassen" --
-- es existieren keine echten Kundendaten in dieser Umgebung, die dabei
-- verloren gehen koennten (siehe Aufgabenstellung). Historische Migrationen
-- (001_init.sql, 003_grants.sql), die `api_keys` anlegen/granten,  werden
-- bewusst NICHT nachtraeglich umgeschrieben -- Migrationen sind ein
-- Ablaufprotokoll, kein lebendiges Dokument; die Historie "es gab einmal
-- api_keys" bleibt so nachvollziehbar. Der aktuelle Zustand der DB nach
-- Anwendung ALLER Migrationen (inkl. dieser) hat kein `api_keys` mehr --
-- das ist, was zaehlt.
--
-- Zweite Aenderung, aus demselben Grund: `checkout_handoffs.api_key_clear`
-- (Migration 010) enthielt frueher den Klartext-API-Key als Abholschein nach
-- einem Stripe-Kauf. Der Stripe-Checkout-Webhook (app/routes/billing.py)
-- legt dort jetzt einen Session-Token ab (dieselbe Technik wie `sessions`:
-- der Klartext-Wert wird dem Kunden per `GET /v1/checkout/{id}/claim`
-- genau einmal als Set-Cookie ausgeliefert, danach geloescht) -- die Spalte
-- wird umbenannt, damit ihr Inhalt nicht mehr faelschlich als API-Key
-- beschriftet ist.

BEGIN;

DROP TABLE IF EXISTS api_keys;

ALTER TABLE checkout_handoffs RENAME COLUMN api_key_clear TO session_token_clear;

COMMIT;
