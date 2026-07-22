# Fundament-Plan: Datenbank + Login + Mandantentrennung (Enterprise)

Ausführungsfertiger Plan für den letzten großen Enterprise-Schritt. Wird umgesetzt,
sobald eine Postgres-URL vorliegt (Supabase empfohlen). Ziel: bestehende Funktionen
bleiben erhalten, Daten wandern von `localStorage` auf serverseitige, pro Mandant
isolierte Speicherung.

## Was der Kunde bereitstellen muss (einmalig, extern)
- **Supabase-Projekt** anlegen (kostenloser Tarif reicht zum Start).
- Diese Werte als Umgebungsvariablen (Vercel + lokale `.env`, NIE ins Git):
  - `DATABASE_URL` (Postgres-Connection-String)
  - `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
  - `AUTH_SECRET` (für Session-Cookies)
- Bestehend bleiben: `LICENSE_SECRET`, `ADMIN_SECRET`, die 3 KI-Keys.

## Technische Wahl
- **Postgres** (Supabase) + **Drizzle ORM** (leichtgewichtig, TypeScript-nativ,
  saubere Migrations) + **Auth.js (NextAuth v5)** für Login/Sessions.
- **Mandantentrennung** über eine `tenant_id`-Spalte in JEDER Fachtabelle, zusätzlich
  Postgres **Row-Level-Security (RLS)** als zweite Verteidigungslinie.

## Datenmodell (Kern)
```
tenants        (id, name, plan, created_at)
users          (id, email, name, password_hash | oauth, created_at)
memberships    (id, tenant_id, user_id, role)          role ∈ owner|admin|member
missions       (id, tenant_id, user_id, goal, status, score, created_at, result_json)
usage_counters (tenant_id, day, used)                   -- serverseitiges Tageslimit
connections    (id, tenant_id, provider, secret_enc, status, created_at)  -- Integrations-Hub
audit_log      (id, tenant_id, user_id, action, target, approved, created_at)
```
- Alle Fachtabellen: `tenant_id NOT NULL` + Index; RLS-Policy `tenant_id = current_tenant()`.
- Secrets in `connections.secret_enc` verschlüsselt (AES-256-GCM, Schlüssel aus Env).

## Auth-Flow
1. Registrierung/Login via Auth.js (E-Mail+Passwort zuerst; Google/Microsoft später).
2. Beim ersten Login: Tenant anlegen + Membership `owner`.
3. Session-Cookie (HTTP-only, signiert) trägt `user_id` + aktiven `tenant_id`.
4. Rollen (`owner|admin|member`) steuern Schreibrechte + Freigaben.

## Serverseitige Härtung (behebt Phase-0-Befunde)
- **Tageslimit** wird gegen `usage_counters` in der DB erzwungen (nicht mehr client-
  seitig umgehbar → Befund 7).
- **Human-in-the-Loop:** schreibende Connector-Aktionen erzeugen einen Freigabe-
  Eintrag; erst nach Bestätigung ausgeführt; alles in `audit_log` (→ Befund 5).
- **Admin-Passwort** von `LICENSE_SECRET` entkoppeln (eigenes `ADMIN_SECRET` Pflicht
  → Befund 8), Rate-Limiting auf `/api/mission|chat|extract` (Vercel KV/Upstash).

## Migration von localStorage (ohne Bruch)
1. Data-Access-Schicht `lib/store/` mit Interface `Store` einführen.
2. Zwei Implementierungen: `localStore` (heutiges Verhalten) und `dbStore` (Postgres).
3. Auswahl per Env: ohne `DATABASE_URL` bleibt `localStore` aktiv → **App läuft
   unverändert weiter**, bis die DB bereitsteht (kein Big-Bang).
4. Import-Helfer: bestehende localStorage-Daten des Nutzers beim ersten Login
   optional in den Tenant übernehmen.

## Umsetzungs-Schritte (in dieser Reihenfolge, jeweils Build+Test grün)
1. Drizzle + Schema + erste Migration; `DATABASE_URL`-Check.
2. Auth.js einbinden (Login/Logout/Session), geschützte Routen.
3. `Store`-Interface + `dbStore` (Missionen, Usage) hinter Env-Flag.
4. Serverseitiges Limit + Audit-Log + Rollenrechte.
5. Integrations-Hub: `connections` + verschlüsselter Token-Store + 1–2 echte OAuth-
   Connectors (Google/Microsoft) mit Verbindungstest.
6. Regressionstests (Vitest) je Schicht; RLS-Policy-Tests.

## Definition of Done
- Bestehende Funktionen laufen weiter (mit und ohne `DATABASE_URL`).
- Daten pro Tenant isoliert (Spalte + RLS), Secrets verschlüsselt.
- Login + Rollenrechte greifen; jede Freigabe im Audit-Log.
- Tests + CI grün.
