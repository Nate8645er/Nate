# Zahlung (Stripe) & Login (Supabase) aktivieren

Beides ist im Code fertig verdrahtet und läuft **ehrlich im „nicht-konfiguriert"-
Modus**, solange keine Keys gesetzt sind – kein Schein-Login, keine Fehlbuchung.
Sobald Sie die folgenden Umgebungsvariablen (z. B. in Vercel) setzen, wird der
jeweilige Teil automatisch aktiv. Vorlage: `.env.example`.

## 1) Stripe – Abo-Checkout, Kundenportal, Webhook

| Variable | Woher | Wofür |
|---|---|---|
| `STRIPE_SECRET_KEY` | Stripe → Entwickler → API-Keys (`sk_live_…` / `sk_test_…`) | Checkout & Kundenportal |
| `STRIPE_WEBHOOK_SECRET` | Stripe → Entwickler → Webhooks → Endpoint (`whsec_…`) | Signaturprüfung des Webhooks |

**Schritte**
1. `STRIPE_SECRET_KEY` setzen. Der Checkout (`POST /api/checkout`) erzeugt dann
   echte Stripe-Sessions; Preise kommen inline aus `lib/preise.ts` (kein
   manuelles Anlegen von Stripe-Preisen nötig). Enterprise und Gratis sind
   bewusst kein Self-Checkout.
2. Webhook-Endpoint in Stripe anlegen:
   - URL: `https://IHRE-DOMAIN/api/stripe/webhook`
   - Ereignisse: `checkout.session.completed`,
     `customer.subscription.updated`, `customer.subscription.deleted`
   - Das erzeugte `whsec_…` als `STRIPE_WEBHOOK_SECRET` setzen.
   Der Endpoint verifiziert jede Signatur (HMAC-SHA256, konstante Zeit,
   5-Minuten-Replay-Schutz) und weist gefälschte Aufrufe mit 400 ab.
3. **Kundenportal** (`POST /api/portal`): öffnet das Stripe-Billing-Portal für
   Rechnungen/Kündigung. **Sicherheit:** Die `customerId` wird serverseitig aus
   der Sitzung abgeleitet (acc_rt-Cookie → Supabase-User → E-Mail → gespeicherte
   customerId) – **nie** aus dem Request-Body (kein IDOR). Aktiv, sobald Login
   (Supabase) **und** Kunden-Store (Schritt 4) konfiguriert sind; sonst 501.

## 3) Plan-Freischaltung & Kunden-Store (Supabase Postgres)
Damit nach dem Kauf automatisch das richtige Paket freigeschaltet und das Portal
den Kunden findet, braucht es eine Tabelle plus einen serverseitigen Schlüssel.

| Variable | Woher | Hinweis |
|---|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Project Settings → API (service_role) | **serverseitiges Geheimnis**, umgeht RLS, nie `NEXT_PUBLIC_` |
| `APP_URL` | Ihre öffentliche Shop-URL | sichere Return-URL fürs Portal |

**Schritte**
1. `supabase/schema.sql` im Supabase-SQL-Editor ausführen (Tabelle `abos` mit
   RLS **an**, ohne Client-Policy – Zugriff nur über den Service-Role-Key).
2. `SUPABASE_SERVICE_ROLE_KEY` und `APP_URL` setzen.
3. Danach schaltet `/api/stripe/webhook` verifizierte Käufe automatisch frei
   (Upsert auf `customer_id`, idempotent) und `/api/portal` wird für angemeldete
   Kund:innen mit hinterlegtem Abo aktiv.

> **Anschlusspunkt:** Die eigentliche Plan-Freischaltung nach einem verifizierten
> Webhook (aus `metadata.planId`) hängt von der Kundendatenbank ab und ist in
> `app/api/stripe/webhook/route.ts` klar markiert – bewusst kein stiller
> Platzhalter in der Logik.

## 2) Supabase – Kundenkonto (Login/Registrierung)

| Variable | Woher | Hinweis |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase → Project Settings → API (`https://…​.supabase.co`) | öffentlich |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase → Project Settings → API (anon public) | **bewusst öffentlich**; Schutz via Row-Level-Security |

**Schritte**
1. Supabase-Projekt anlegen, E-Mail-Auth aktivieren (Authentication → Providers).
2. Beide `NEXT_PUBLIC_*`-Werte setzen. Danach zeigt `/konto` ein echtes
   Login-/Registrierungsformular (`POST /api/auth/login`,
   `POST /api/auth/register`). Ohne die Werte bleibt der Login ehrlich
   deaktiviert und der Zugang läuft über den Lizenzschlüssel per E-Mail.
3. **Row-Level-Security** für alle Kundentabellen einschalten – der Anon-Key ist
   öffentlich; die Datentrennung kommt aus RLS-Policies, nicht aus Geheimhaltung.

**Sicherheit**
- Das Refresh-Token wird bei erfolgreicher Anmeldung nur als
  `HttpOnly; Secure; SameSite=Lax`-Cookie gesetzt – nie im JSON-Body, nie im
  Client-State. Der geheime `service_role`-Key gehört **nicht** in dieses Projekt.

## Sicherheits-To-dos vor dem Live-Gang
Umgesetzt (zwei Security-Reviews): Webhook-Signatur konstante Zeit + Replay-Schutz,
Refresh-Token nur als HttpOnly/Secure-Cookie, Stripe-/Service-Role-Key nie im
Client, generische Auth-/Webhook-Fehlermeldungen (keine User-Enumeration), Portal
ohne IDOR (customerId aus verifizierter Sitzung), **Portal nur mit bestätigter
E-Mail** (Schutz gegen Konto-Übernahme unabhängig von der Supabase-Einstellung),
Return-URL aus `APP_URL`-Allowlist, RLS auf `abos` an, **Event-Reihenfolge-Schutz**
beim Upsert (verspätetes „updated" reaktiviert kein gekündigtes Abo), **planId
gegen die echten Pakete validiert**, **Rate-Limit auf `/api/auth/*`** (10 Versuche
/ 10 Min pro IP+E-Mail; verteilt über Upstash oder Best-Effort-In-Memory).
**Empfehlungen:**
- In Supabase die E-Mail-Bestätigung aktiv lassen (Authentication → Providers →
  „Confirm email").
- Für echtes verteiltes Rate-Limit `UPSTASH_REDIS_REST_URL` + `_TOKEN` setzen
  (ohne Upstash zählt der Limiter nur pro Serverless-Instanz; die App warnt in
  Produktion einmalig im Log). Die Client-IP kommt aus `x-real-ip` (von Vercel
  gesetzt, nicht fälschbar); `x-forwarded-for` dient nur als Fallback.
- Restrisiko (bewusst): Fällt Upstash aus, lässt der Limiter fail-open durch
  (Verfügbarkeit vor Sperre) – das Signatur-/Passwort-Gate bleibt aber aktiv.

## 4) Lizenzschlüssel automatisch nach dem Kauf (E-Mail optional)
Nach einem verifizierten Kauf (`checkout.session.completed`) erzeugt der Webhook
**einmalig** einen Lizenzschlüssel für den gekauften Plan, speichert ihn und –
falls E-Mail konfiguriert – schickt ihn als Willkommens-Mail.

| Variable | Woher | Hinweis |
|---|---|---|
| `RESEND_API_KEY` | resend.com → API Keys | ohne Key wird keine Mail versendet |
| `MAIL_FROM` | in Resend verifizierte Absenderadresse | z. B. `shop@ihre-domain.ch` |

- **Ohne Resend** bleibt alles funktionsfähig: Der Schlüssel wird gespeichert und
  ist für die angemeldete Kundin unter `/konto` abrufbar (Selbstbedienung).
- Der Schlüssel wird über den bestehenden Weg eingelöst (`/onboarding` →
  `POST /api/license` → Lizenz-Token), womit die **serverseitige Plan-/Limit-
  Durchsetzung** (Missionen/Tag, Token-Budget) automatisch greift.
- Idempotent & race-sicher: Der Schlüssel wird **atomar** gesetzt (nur wenn
  `license_key` noch NULL ist). Parallele Stripe-Zustellungen erzeugen daher
  nie zwei gültige Schlüssel oder Doppel-Mails – genau ein Aufruf gewinnt.
- Empfehlung: `APP_URL` setzen, damit die Mail einen korrekten Einlöse-Link
  enthält; ohne `APP_URL` verweist sie sicher aufs Konto (kein Host-Header-Link).

## Konto zeigt den echten Plan
Nach Login ruft `/konto` den Endpunkt `GET /api/mein-abo` auf: Er leitet die
Identität aus der Sitzung ab und liefert `planId/planName/status/aktiv` aus dem
Kunden-Store. So sieht die Kundin nach dem Kauf automatisch ihr echtes Paket und
kann über „Rechnungen & Kündigung verwalten" das Stripe-Portal öffnen.

## Schnelltest ohne Live-Keys
`npm test` prüft beide Wege inkl. „nicht-konfiguriert", Webhook-Signatur
(gültig/veraltet/verändert) und Login-Flow mit injiziertem `fetch` –
komplett ohne echte Keys.
