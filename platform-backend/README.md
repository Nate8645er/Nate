# Platform Backend — Produkt A (Fundament)

Mandantengetrenntes KI-Plattform-Backend. Phase-2-Ziel des Master-Prompts:
**ein Modell, ein Mandant, ein Chat — lauffähig**, mit Mandantentrennung auf
Datenbankebene (Row Level Security), Tarif-Durchsetzung und Verbrauchsmessung.

## Architektur (kurz)

```
Browser ──E-Mail+Passwort──▶ POST /v1/auth/login/signup ──▶ HttpOnly-Session-Cookie
                              │  Auth: sessions → Mandant + Tarif
                              │  RLS:  SET LOCAL app.current_tenant
                              ▼
                          Postgres (RLS erzwingt Mandantentrennung)
                              ▲
        Chat ──▶ LiteLLM-Gateway ──▶ Anthropic / OpenAI / Ollama (lokal)
```

Es gibt **einen einzigen** Authentifizierungsweg: das HttpOnly-Session-Cookie.
Ein frueher parallel existierender `Authorization: Bearer pk_...`-API-Schluessel
(Entwickler-/Programmzugriff) ist **vollstaendig entfernt** — Migration
`013_drop_api_keys.sql`, `app/auth.py`. Es gibt keinen Weg mehr, sich ohne
Browser-Session zu authentifizieren, auch nicht fuer Automatisierung/CI.

- **Mandantentrennung (real erzwungen)**: `migrations/001_init.sql` aktiviert
  `ENABLE`+`FORCE ROW LEVEL SECURITY` auf allen mandantengebundenen Tabellen.
  Entscheidend ist die **Rollentrennung**: die App verbindet sich zur Laufzeit
  als `app_rw` (NOSUPERUSER, NOBYPASSRLS, **nicht** Tabellen-Owner) — nur für
  eine solche Rolle greift RLS. Superuser/Owner umgehen RLS (auch mit FORCE),
  deshalb laufen **Migrationen über eine separate, privilegierte Verbindung**
  (`MIGRATE_DATABASE_URL`), die Laufzeit über `DATABASE_URL` (app_rw). Die App
  setzt pro Transaktion `app.current_tenant`; die DB filtert automatisch. Ein
  App-Bug kann keine fremden Zeilen liefern — bewiesen durch
  `tests/test_rls_integration.py` gegen eine echte DB.
- **`sessions`** (Web-Login, s.u.) ist bewusst nicht RLS-gebunden: der
  Login-Lookup erfolgt über den Hash des hochentropischen Session-Cookie-
  Tokens; ohne diese Ausnahme entstünde ein Henne-Ei-Problem (der Mandant
  wird erst durch den Lookup bestimmt). **`user_directory`** (E-Mail →
  Mandant/Nutzer) ist ebenfalls nicht RLS-gebunden, speichert aber bewusst
  KEIN Geheimnis — der eigentliche `password_hash` bleibt in `users`,
  weiterhin voll RLS-gebunden (siehe Abschnitt "Web-Login" und Migration
  `012_password_auth.sql`). Die frühere `api_keys`-Tabelle (gleiches Muster,
  über `key_hash`) ist per Migration `013_drop_api_keys.sql` gedroppt.
- **Tarife**: `migrations/002_seed_plans.sql` (Free … Enterprise, Master-Prompt
  3.3). Modelle sind pro Tarif freigeschaltet, nicht pro Nutzer hart kodiert.
- **Gateway**: LiteLLM (`litellm/config.yaml`) — ein Zugang für alle Anbieter
  inkl. mindestens einem lokalen Modell (Ollama).
- **Verbrauch**: jede Chat-Antwort schreibt ein `usage_events`-Ereignis →
  Grundlage für Limit-Durchsetzung und spätere Abrechnung (Phase 4).

## Lokal starten

```bash
cp .env.example .env      # Pflichtwerte setzen: POSTGRES_PASSWORD, APP_DB_PASSWORD,
                          # LITELLM_MASTER_KEY, ADMIN_TOKEN (fehlt eines -> Start
                          # schlägt bewusst fehl, keine Default-Secrets)
docker compose up --build
```

Compose legt beim ersten Start via `db-init/01-app-role.sh` die eingeschränkte
Rolle `app_rw` an; die Migrationen (Owner-Rolle) erstellen Schema, Policies und
Grants. `migrate()` führt jede SQL-Datei genau einmal aus (Tracking-Tabelle
`schema_migrations`) — Neustarts gegen ein bestehendes Volume sind unkritisch.

Dann entweder als Kunde selbst (Self-Service, Free-Tarif):

```bash
# Signup setzt direkt ein Session-Cookie (-c speichert es in cookies.txt,
# -b schickt es bei Folgeanfragen mit).
curl -sX POST localhost:8080/v1/auth/signup -c cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{"name":"Acme","email":"chef@acme.ch","password":"ein-gutes-passwort"}'

curl -sX POST localhost:8080/v1/chat -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"model":"ollama/llama3.2","messages":[{"role":"user","content":"Hallo"}]}'

curl -s localhost:8080/v1/usage -b cookies.txt
```

... oder per Admin/Ops fuer einen bestehenden Tarif (Support-Fall, initiales
Passwort wird dem Kunden out-of-band mitgeteilt):

```bash
# 1) Mandant provisionieren -- Pflicht-Feld "password", kein API-Key mehr
curl -sX POST localhost:8080/admin/provision \
  -H "X-Admin-Token: $ADMIN_TOKEN" -H 'Content-Type: application/json' \
  -d '{"tenant_name":"Acme","owner_email":"chef@acme.ch","plan_code":"pro","password":"initiales-passwort"}'

# 2) Kunde meldet sich damit selbst an (Session-Cookie wie oben)
curl -sX POST localhost:8080/v1/auth/login -c cookies.txt \
  -H 'Content-Type: application/json' \
  -d '{"email":"chef@acme.ch","password":"initiales-passwort"}'
```

## Endpunkte

| Methode | Pfad | Zweck | Schutz |
|---------|------|-------|--------|
| GET  | `/` | Statisches Chat-UI (Modellwechsel + Verbrauch) | — |
| GET  | `/health` | Liveness + DB-Check | — |
| GET  | `/metrics` | Prometheus-Metriken (Requests, Latenz, Chat-Verbrauch) | — |
| POST | `/admin/provision` | Mandant + Owner mit initialem Passwort anlegen | `X-Admin-Token` |
| POST | `/v1/auth/signup` | Selbstbedienung: Free-Tarif-Mandant + Passwort anlegen, meldet direkt an | — (rate-limited) |
| POST | `/v1/auth/login` | E-Mail+Passwort prüfen, Session-Cookie setzen | — (rate-limited) |
| POST | `/v1/auth/logout` | Session serverseitig löschen + Cookie entfernen | Session-Cookie |
| POST | `/v1/chat` | Chat via Gateway, mit Tarif-/Limit-Prüfung (optional `enable_web_tool`, Bild-Anhänge, s.u.) | Session-Cookie |
| POST | `/v1/attachments/extract` | Dokument (PDF/Text/Markdown) hochladen, extrahierten Text zurückgeben (s.u.) | Session-Cookie |
| GET  | `/v1/models` | Im Tarif freigeschaltete Modelle (fürs UI-Dropdown), inkl. `vision`-Feld | Session-Cookie |
| GET  | `/v1/usage` | Monatsverbrauch des Mandanten | Session-Cookie |
| GET  | `/v1/conversations` | Liste der Unterhaltungen | Session-Cookie |
| GET  | `/v1/conversations/{id}` | Eine Unterhaltung mit Nachrichten | Session-Cookie |
| GET/POST | `/v1/agents…` | Agenten verwalten + ausführen (Tarif-Limit) | Session-Cookie |
| GET  | `/v1/billing` | Tarif, Abo-Zustand, Verbrauch, Historie | Session-Cookie |
| GET/POST/DELETE | `/v1/integrations…` | Integrationen-Gerüst (Tarif-Limit) — s.u. | Session-Cookie |
| POST | `/webhooks/shopify/orders-paid` | Kauf → Mandant freischalten | HMAC (Shopify) |
| POST | `/webhooks/stripe` | Abo-Ereignisse (Kauf/Wechsel/Zahlung/Kündigung) | HMAC (Stripe) |
| GET  | `/dashboard.html` | Widget-Dashboard (Agenten/Verbrauch/Historie, Drag-and-Drop) | — (E-Mail+Passwort im Browser) |
| GET  | `/v1/checkout/{session_id}/claim` | Setzt das Session-Cookie EINMAL per Set-Cookie (Onboarding, s.u.) | — (Session-ID als Abholschein) |
| GET  | `/checkout-success.html` | Erfolgsseite nach Stripe-Checkout — loggt automatisch ein | — |

## Web-Login: E-Mail+Passwort ist der EINZIGE Authentifizierungsweg

Frueher musste sich jeder Kunde im Chat-UI (`static/index.html`) einen
rohen `pk_...`-API-Schlüssel einfügen, UND es gab parallel einen
`Authorization: Bearer pk_...`-Entwickler-/Programmzugriff — ganz anders als
bei ChatGPT/Claude/Kimi (E-Mail+Passwort, nie ein Schlüssel zu Gesicht).
**Produktentscheidung**: das API-Schlüssel-Konzept ist vollstaendig aus der
Plattform entfernt — nicht nur aus der UI, auch als Entwickler-/
Programmzugriff. Migration `013_drop_api_keys.sql` droppt die `api_keys`-
Tabelle real (kein "deprecated liegen lassen"); `app/auth.py` kennt keinen
Bearer-Pfad mehr, `require_principal()` akzeptiert ausschließlich das
Session-Cookie. Ein mitgeschickter `Authorization`-Header wird schlicht
nicht mehr gelesen — auch ein wohlgeformt aussehender, frei erfundener
Bearer-Token führt zu 401, genau wie ein fehlendes Cookie (siehe
`tests/test_auth_integration.py::test_bearer_token_path_is_completely_gone`).

Dazu kam eine echte Lücke: es gab **überhaupt keinen** Weg, sich selbst für den
Free-Tarif anzumelden — nur `/admin/provision` (admin-token-geschützt) und
die Stripe/Shopify-Webhooks konnten einen Mandanten anlegen. Das widersprach
der Store-FAQ (`store/sections/faq.liquid`: "Free-Tarif dauerhaft kostenlos,
keine Kreditkarte nötig"). Beides behoben:

- **`POST /v1/auth/signup`** `{name, email, password}` — legt einen
  **eigenen** Free-Tarif-Mandanten an (`provision_tenant(plan_code="free",
  password=...)`), setzt das Passwort (bcrypt) und meldet direkt per
  Session-Cookie an. Es gibt keinen API-Key mehr, der hier ausgeliefert
  werden könnte. Rate-limited pro IP (`app/ratelimit.py::signup_limiter`,
  5/Std.) gegen Massen-Registrierung.
- **`POST /v1/auth/login`** `{email, password}` — sucht den Nutzer per
  E-Mail (siehe Architektur unten), prüft mit `bcrypt.checkpw` (timing-sicher
  von Haus aus + zusätzlicher Dummy-Hash-Vergleich bei unbekannter E-Mail,
  siehe `app/auth.py::DUMMY_PASSWORD_HASH`), setzt bei Erfolg ein neues
  Session-Cookie. Bei Fehlschlag **immer** dieselbe generische Meldung
  ("E-Mail oder Passwort falsch") — ob die E-Mail existiert, ist von außen
  nicht unterscheidbar. Rate-limited in **zwei** Richtungen
  (`login_limiter_ip`, `login_limiter_email`, je 300s-Fenster): schützt
  sowohl gegen Credential Stuffing (viele E-Mails von einer IP) als auch
  gegen verteilten Brute-Force gegen EIN Konto (viele IPs, eine E-Mail).
- **`POST /v1/auth/logout`** — löscht die Session serverseitig und das
  Cookie.
- **Cookie**: `HttpOnly` (kein JS-Zugriff, kein XSS-Diebstahl), `Secure`
  (nur über HTTPS), `SameSite=Lax`. Das ist eine **bewusste,
  dokumentierte CSRF-Haltung** für diese Runde — schützt gegen die
  meisten Cross-Site-Fälle (kein Cookie bei einfachen Cross-Site-Requests
  wie `<img>`/`<form>`), aber **kein** zusätzliches CSRF-Token. Reicht für
  eine Same-Origin-App ohne Cross-Site-Formulare.

**Architektur des E-Mail-Lookups** (dasselbe Henne-Ei-Problem, das früher
`api_keys` löste: der Mandant ist beim Login noch unbekannt, RLS kann für
diesen einen Schritt nicht greifen): `user_directory` (Migration
`012_password_auth.sql`) bildet GLOBAL eindeutig E-Mail → (`tenant_id`,
`user_id`) ab, speichert aber **bewusst kein Geheimnis** — bei einer
E-Mail-Adresse (niedrige Entropie, oft bekannt) wäre das auch nicht
vertretbar. Der eigentliche `password_hash` bleibt in `users`, weiterhin voll
RLS-gebunden — `app/billing.py::resolve_metadata_tenant` verlässt sich beim
Stripe-Metadaten-Härten (Security-Review HOCH-1) genau darauf, dass `users`
RLS-gefiltert ist; das durfte diese Migration nicht antasten. Der Login
läuft daher zweistufig: `user_directory` per `admin_tx()` nach E-Mail
durchsuchen (liefert nur `tenant_id`/`user_id`), dann mit bekanntem
`tenant_id` ganz normal `tenant_tx()` den `password_hash` aus `users` lesen.

`app/auth.py::require_principal()` akzeptiert **ausschließlich** das
Session-Cookie (`sessions`-Tabelle, gleiche Hash-nur-Speicherung wie früher
bei `api_keys`) — es gibt keinen Bearer-Zweig mehr, der Authorization-Header
wird von der Funktionssignatur her gar nicht mehr entgegengenommen. Fehlt das
Cookie oder ist es ungültig/abgelaufen: 401, ohne Unterscheidung nach außen.

`app/auth.py::create_session()` erzeugt eine Session in einer übergebenen
Transaktion und wird an **drei** Stellen genutzt: `/v1/auth/signup`,
`/v1/auth/login` (beide in `app/routes/auth.py`) und dem Stripe-Checkout-
Autologin (`app/routes/billing.py`, s.u.) — an einer Stelle definiert, damit
Session-Erzeugung nicht dupliziert ist.

**Frontend** (`static/index.html`, `static/dashboard.html`): der Setup-Bereich
zeigt ein E-Mail+Passwort-Formular mit Umschalter Anmelden/Registrieren. Alle
`fetch()`-Aufrufe senden `credentials:"include"`, damit das Cookie
mitgeschickt wird. Der frühere `localStorage.pk`-Fallback für einen in einer
Legacy-Sitzung gespeicherten rohen Key ist entfernt — es gibt keinen API-Key
mehr, den er lesen könnte.

**Getestet** gegen eine echte Postgres-DB (`tests/test_auth_integration.py`):
Signup→Login mit denselben Daten, generische Fehlermeldung bei
falschem Passwort **und** unbekannter E-Mail (identischer Text), zwei
unabhängige Sessions (zwei Konten, zwei `TestClient`-Instanzen) sehen jeweils
nur ihren eigenen Mandanten, abgelaufene/unbekannte Session → 401,
Rate-Limits greifen, doppelte Signup-E-Mail → 409 ohne verwaisten Mandanten,
und explizit: ein frei erfundener `Authorization: Bearer`-Header wird
ignoriert und bleibt 401 (`test_bearer_token_path_is_completely_gone`) — der
Beweis, dass der alte Pfad wirklich weg ist, nicht nur zusätzlich zum Cookie
"auch noch" akzeptiert wird. **Regressionstests für den Sicherheits-Fund**
(`tests/test_account_claim_integration.py`): ein passwortlos provisionierter
(Stripe-artiger) Nutzer hat sofort einen `user_directory`-Eintrag; ein
Angreifer kann NICHT mehr per `/v1/auth/signup` mit derselben E-Mail einen
konkurrierenden Mandanten anlegen (kein Übernahme-Fenster mehr); der echte
Eigentümer kann sich per Signup mit seiner eigenen E-Mail erfolgreich ein
Passwort setzen und anschließend per `/v1/auth/login` damit anmelden
("Konto beanspruchen" funktioniert Ende-zu-Ende).

**Bewusst offen / nicht in dieser Runde** — seit der API-Key-Entfernung
**wichtiger** als vorher, weil es jetzt keinen Bearer-Fallback mehr gibt,
der eine Luecke hier ueberbruecken koennte:
- **Kein Passwort-Reset per E-Mail** — es gibt keine echte SMTP-/
  E-Mail-Versand-Infrastruktur in dieser Umgebung. Ein Nutzer, der sein
  Passwort vergisst, hat aktuell keinen Selbstbedienungsweg zurück (nur
  `/admin/provision` — legt aber einen NEUEN Mandanten an, kein Passwort-
  Reset fuer den bestehenden — bzw. direkter DB-Zugriff durch den
  Betreiber).
- **Kein OAuth/"Login mit Google"** — bräuchte eine echte OAuth-App-
  Registrierung, die es hier nicht gibt.
- **Über Stripe/Shopify provisionierte Mandanten ohne Passwort**: der Kunde
  vergibt im Checkout kein Passwort. `/admin/provision` verlangt zwingend ein
  Passwort (Pflichtfeld). Die beiden Webhook-Pfade (Stripe, Shopify) legen
  weiterhin ohne Passwort an — **aber** (Sicherheits-Fix, siehe Kasten unten)
  `provision_tenant()` reserviert die E-Mail seit diesem Review in JEDEM Fall
  sofort in `user_directory`, auch ohne Passwort:
  - **Stripe**: bekommt sofort eine Session per Auto-Login
    (`/v1/checkout/{id}/claim`, s.u.). Läuft diese Session nach
    `SESSION_TTL_DAYS` (30 Tage) ab oder geht das Cookie verloren, kann sich
    der Kunde jetzt trotzdem wieder Zugriff verschaffen: `/v1/auth/signup`
    mit genau seiner eigenen E-Mail setzt sein erstes Passwort auf dem
    BESTEHENDEN Konto ("Konto beanspruchen", s.u.) — kein Passwort-Reset-
    Flow auf `checkout-success.html` mehr nötig, auch wenn der wie bisher
    eine bequemere Alternative wäre (nicht in dieser Runde umgesetzt).
  - **Shopify**: noch kein Auto-Login (kein Live-Redirect auf eine eigene
    Erfolgsseite wie bei Stripe) — siehe eigener Abschnitt unten. Der Kunde
    beansprucht sein Konto stattdessen direkt über `/v1/auth/signup`.

> ### Sicherheits-Fund (behoben): E-Mail-Übernahme bei passwortlosen Konten
>
> **Fund**: `provision_tenant()` legte bei Stripe-/Shopify-Käufen einen
> `users`-Eintrag an, aber **keinen** `user_directory`-Eintrag (der wurde nur
> gesetzt, wenn `password` übergeben wurde). Der 409-Doppelregistrierungs-
> Schutz in `/v1/auth/signup` griff deshalb **nicht** für diese E-Mail, bis
> jemand sie über `user_directory` reservierte.
>
> **Angriff**: Ein Angreifer, der nur die E-Mail-Adresse eines zahlenden
> Stripe-Kunden kennt, registriert sich selbst per `POST /v1/auth/signup`
> mit genau dieser E-Mail (kein Passwort des Opfers nötig — es ist sein
> eigenes neues Signup) und bekommt einen `user_directory`-Eintrag, der die
> E-Mail auf seinen eigenen, neuen Free-Mandanten zeigt. Läuft die 30-Tage-
> Session des echten Kunden ab, kann sich dieser nie mehr mit seiner eigenen
> E-Mail registrieren (409 — die E-Mail "gehört" jetzt dem Angreifer-
> Mandanten) — **dauerhafter Verlust des Zugriffs auf das eigene, bezahlte
> Konto**. Kein Zeitfenster-Zufall: vom Angreifer jederzeit aktiv auslösbar,
> sobald er die E-Mail kennt.
>
> **Fix** (`app/provisioning.py`, `app/routes/auth.py`):
> 1. `provision_tenant()` reserviert die E-Mail jetzt **immer sofort** in
>    `user_directory` — auch ohne Passwort. Schließt das Zeitfenster
>    vollständig: die E-Mail gehört ab dem ersten Kauf/Anlegen "ihrem"
>    Mandanten, ein Angreifer kann sie nicht mehr für einen eigenen Mandanten
>    kapern.
> 2. `POST /v1/auth/signup` unterscheidet jetzt zwei Fälle für eine bereits
>    in `user_directory` stehende E-Mail (`_claim_existing_account` in
>    `app/routes/auth.py`): ist `users.password_hash` **NULL** (passwortlos
>    angelegt, z. B. per Stripe/Shopify), ist das der **echte Eigentümer**,
>    der jetzt sein erstes Passwort setzt ("Konto beanspruchen") — Passwort
>    wird auf dem **bestehenden** Nutzer gesetzt, Session für den
>    **bestehenden** Mandanten erzeugt, **kein** neuer Mandant. Existiert
>    bereits ein Passwort, bleibt es beim bisherigen 409 (echter
>    Doppel-Versuch).
>
> **Verbleibendes Restrisiko (ehrlich benannt, keine SMTP-Infrastruktur in
> dieser Umgebung)**: `_claim_existing_account` verifiziert nicht, dass die
> Person, die das Passwort setzt, wirklich die E-Mail-Adresse kontrolliert —
> wer zuerst mit einer bekannten Kunden-E-Mail bei `/v1/auth/signup`
> ankommt, "beansprucht" das Konto. Strukturell dasselbe Problem wie der
> ursprüngliche Fund, aber zeitlich **vor** statt **nach** dem ersten
> Kauf-Ereignis: der Angreifer müsste schneller sein als der zahlende Kunde
> selbst (der direkt nach dem Kauf per Auto-Login bereits eingeloggt ist),
> nicht nur irgendwann innerhalb der 30-Tage-Session zuschlagen — ein deutlich
> kleineres Fenster, aber **nicht null**. Echte Behebung bräuchte einen
> Bestätigungslink (E-Mail-Verifikation vor dem Setzen des Passworts) —
> **nicht umgesetzt**, da keine echte SMTP-Infrastruktur in dieser Umgebung
> existiert. Nächster Schritt, sobald SMTP verfügbar ist: `/v1/auth/signup`
> verschickt bei einer bereits reservierten, passwortlosen E-Mail einen
> zeitlich begrenzten Bestätigungslink statt das Passwort sofort zu setzen;
> erst der Klick darauf schaltet das neue Passwort scharf.

## Onboarding nach Stripe-Kauf (zahlende Kunden)

Ergänzt den Web-Login oben: unmittelbar nach einem Stripe-Kauf ist die
Checkout-Session-ID (noch) kein Login-Cookie — dafür gibt es einen
eigenen, einmaligen Abholweg direkt im Anschluss an den Kauf. Der Kunde
vergibt im Stripe-Checkout-Formular kein Passwort — statt eines API-Keys
(frueher) erzeugt der Webhook deshalb direkt eine Session
(`app/auth.py::create_session`, dieselbe Logik wie beim Web-Login) und
liefert sie per `Set-Cookie` aus. Anders als bei ChatGPT/Claude/Kimi (Abo
kaufen → direkt loslegen) hätte der Kunde sonst seine eigenen
Zugangsdaten irgendwo suchen müssen. Behoben, ohne neue externe
Abhängigkeit:

1. `checkout.session.completed` legt beim Neukauf wie bisher Mandant an,
   erzeugt zusätzlich eine Session und hinterlegt deren Klartext-Token unter
   der Stripe-Checkout-Session-ID (`checkout_handoffs.session_token_clear`,
   Migration 010 + `013_drop_api_keys.sql` für die Umbenennung von
   `api_key_clear`) — ein einmalig abrufbarer, zeitlich begrenzter
   (60 Min.) Abholschein.
2. Stripes `success_url` mit `?session_id={CHECKOUT_SESSION_ID}` (Stripe-
   eigene Konvention) zeigt auf `/checkout-success.html`.
3. Die Seite pollt `GET /v1/checkout/{session_id}/claim` (kurz, mit
   wachsendem Abstand — der Webhook kann etwas nach dem Redirect ankommen)
   mit `credentials:"include"`. Bei Erfolg setzt die Antwort das
   HttpOnly-Session-Cookie per `Set-Cookie` — der Browser übernimmt es
   automatisch, die Seite selbst sieht nie ein Klartext-Geheimnis — und
   leitet zum Chat weiter — **kein Kopieren, kein Einfügen, kein Suchen**
   durch den Kunden.

Der Abholschein ist nach dem ersten Abruf sofort gelöscht (single-use) —
ein zweiter Versuch mit derselben Session-ID liefert 404, genau wie eine
unbekannte oder abgelaufene ID. Getestet gegen eine echte Postgres-DB
inkl. Beweis, dass die abgeholte Session wirklich funktioniert (Folgeanfrage
auf demselben Client ist authentifiziert): `tests/test_checkout_handoff.py`.
Im Stripe-Dashboard muss die `success_url` des Checkout-Links auf
`https://<domain>/checkout-success.html?session_id={CHECKOUT_SESSION_ID}`
gesetzt werden, damit das greift.

**Ehrliche Einschränkung** (siehe auch Abschnitt "Web-Login" oben, Kasten
"Sicherheits-Fund"): dieser Kunde hat nie ein Passwort gesetzt. Läuft die
per Auto-Login erzeugte Session ab (30 Tage) oder geht das Cookie verloren,
kann sich der Kunde seit dem Sicherheits-Fix trotzdem wieder Zugriff
verschaffen — `POST /v1/auth/signup` mit genau seiner eigenen E-Mail setzt
sein erstes Passwort auf dem bestehenden Konto ("Konto beanspruchen"), statt
mit 409 abgelehnt zu werden oder (der ursprüngliche Fund) einem Angreifer
einen neuen, konkurrierenden Mandanten für dieselbe E-Mail zu erlauben. Ein
dedizierter Passwort-Setzen-Schritt direkt auf `checkout-success.html` wäre
komfortabler (kein Umweg über das Signup-Formular), ist aber nicht Teil
dieser Runde — funktional deckt `/v1/auth/signup` denselben Fall bereits ab.
Verbleibende, bewusst nicht geschlossene Lücke ohne echte SMTP-
Infrastruktur: kein Nachweis, dass wer das Passwort setzt, auch wirklich die
E-Mail-Adresse kontrolliert (Details im Kasten oben).

## Abrechnung (Phase 4)

Der Stripe-Webhook hält Tarif und Zugang synchron mit dem Abo:

| Ereignis | Wirkung |
|---|---|
| `checkout.session.completed` | Mandant freischalten (oder verknüpfen), Tarif setzen |
| `customer.subscription.updated` | Tarifwechsel (Up-/Downgrade) übernehmen |
| `invoice.payment_failed` | Mandant auf `suspended` → Zugang gesperrt (401/403) |
| `invoice.paid` | Mandant wieder `active` |
| `customer.subscription.deleted` | Kündigung → gesperrt |

- **Signatur**: HMAC-SHA256 über `{timestamp}.{body}` inkl. 300-s-Zeitfenster
  (Replay-Schutz), konstant-Zeit verglichen. Ohne Stripe-SDK (Stdlib).
- **Idempotenz**: `processed_webhooks` (Provider + Event-ID). **Jedes** Ereignis
  — nicht nur Neuanlagen — belegt seine Kennung und ändert Zustand in **einer**
  Transaktion; bricht ein Schritt ab, greift die Wiederzustellung korrekt statt
  den Zustand dauerhaft falsch stehen zu lassen. Ein `400` (ungültiger Auftrag)
  verbraucht die Kennung nicht; eine **fehlende** Kennung wird fail-closed mit
  `400` abgelehnt (nie fail-open verarbeitet).
- **Tarif-Zuordnung**: `metadata.plan_code` am Stripe-Objekt, sonst
  `STRIPE_PRICE_MAP` (Preis-ID → Tarif).
- **`metadata.tenant_id`-Härtung**: wird nur akzeptiert, wenn es eine gültige
  UUID ist **und** die zahlende E-Mail nachweislich zu einem Nutzer genau
  dieses Mandanten gehört (RLS-geprüft) — verhindert die Übernahme eines
  fremden Mandanten über frei wählbare Checkout-Metadaten. Zweite
  Verteidigungslinie: `stripe_customer_id` wird nie überschrieben, wenn
  bereits ein *anderer* Kunde verknüpft ist.
- **Admin- vs. billing-Sperre**: `tenants.suspended_reason` unterscheidet
  `'admin'` (manuell durch den Betreiber) von `'billing'` (Abo inaktiv). Ein
  reguläres `invoice.paid` hebt eine administrative Sperre **nicht** auf.
- **Body-Limit**: Webhook-Bodies werden gestreamt und ab 1 MiB mit `413`
  abgebrochen (`app/http_limits.py`) — schützt auch gegen fehlenden/falschen
  `Content-Length`-Header (Chunked Transfer-Encoding).

## Datei-/Bild-Anhänge im Chat (Vision + Dokument-Kontext)

Backend-Teil dieser Runde (Frontend-UI für Anhänge folgt in einer
**separaten, späteren Runde** — bewusst nicht in dieser, siehe unten und
CLAUDE.md: `static/index.html`/`static/dashboard.html` standen wegen
paralleler Arbeit eines anderen Agenten nicht zur Disposition).

### Was geht

- **Bilder an Vision-fähige Modelle**: `POST /v1/chat` akzeptiert `content`
  jetzt entweder als einfachen String (wie bisher, unverändert) **oder** als
  Liste OpenAI-kompatibler Content-Blöcke:
  ```json
  {"role": "user", "content": [
    {"type": "text", "text": "Was zeigt dieses Bild?"},
    {"type": "image_url", "image_url": {"url": "data:image/png;base64,iVBOR..."}}
  ]}
  ```
  `GET /v1/models` liefert pro Modell zusätzlich ein `"vision": true/false`
  -Feld (`app/models_catalog.py::KNOWN_MODELS`), damit das (spätere)
  Frontend die Anhang-Funktion nur bei passenden Modellen anbieten kann.
- **Dokument-Text-Extraktion**: `POST /v1/attachments/extract` (multipart,
  Feld `file`) nimmt ein PDF, eine Text- oder Markdown-Datei entgegen und
  gibt den extrahierten, auf `MAX_DOCUMENT_CHARS` (20 000 Zeichen, analog
  `MAX_RESULT_CHARS` in `web_fetch_tool.py`) gekürzten Text direkt zurück —
  **kein** persistenter Datei-Storage, die Datei existiert nur für die Dauer
  dieser einen Anfrage im Speicher. Funktioniert mit **jedem** registrierten
  Modell (kein Vision nötig) — der Text ist reiner Chat-Kontext.

### Endpunkt-Design-Entscheidung (und Begründung)

Zwei unterschiedliche Wege für zwei unterschiedliche Anhang-Arten, bewusst
**nicht** einheitlich über einen Upload-Endpunkt:

- **Bilder → direkt im JSON-Body von `POST /v1/chat`** (Base64-Data-URI im
  Content-Block, kein separater Upload-Endpunkt). Ein Bild ist typischerweise
  klein genug, dass der ~33 % Base64-Overhead gegenüber Storage-Management
  (Upload, Referenz-ID, Aufräumen) die einfachere Wahl ist — und ein Bild ist
  ohnehin nur für **diese eine** Chat-Anfrage relevant, es gibt nichts zu
  persistieren.
- **Dokumente → eigener `POST /v1/attachments/extract`-Endpunkt** (multipart,
  gibt den extrahierten Text direkt zurück). Dokumente (v.a. PDFs) können
  deutlich größer als ein Chat-Bild sein UND nur der (kurze, gekürzte)
  extrahierte **Text** soll in den Chat-Kontext einfließen, nicht die
  Rohdatei — ein eigener Extraktions-Roundtrip vermeidet, dass potenziell
  mehrere MB Rohdatei durch den ohnehin schon Base64-kodierten Chat-Request
  geschleust werden müssten. Kein persistenter Storage nötig (Text wird vom
  Frontend als zusätzliche `role: "system"`-Nachricht vor die eigentliche
  User-Nachricht in `messages` gehängt, siehe
  `app/attachments.py::build_document_context_message`) — kein
  Aufräum-Problem, weil nichts gespeichert wird.

### Sicherheit / Validierung (`app/attachments.py`, `app/routes/chat.py`)

- **Vision-Pflicht**: Bild-Content wird nur akzeptiert, wenn das gewählte
  Modell `"vision": true` hat (`models_catalog.supports_vision`) — sonst
  klare `400` ("Modell '…' unterstützt keine Bild-Eingabe"), nie
  stillschweigend ignoriert oder ungeprüft an ein Modell weitergereicht, das
  damit nicht umgehen kann. Gilt **sowohl** für `/v1/chat` **als auch** für
  `/v1/agents/{id}/chat` (`AgentChatRequest` nutzt dieselbe multimodale
  `ChatMessage`-Klasse — ohne die gemeinsame `validate_attachments()`-Prüfung
  hätte der Agenten-Pfad Bild-Anhänge komplett unvalidiert durchgereicht,
  siehe `tests/test_agents_integration.py::test_agent_chat_rejects_image_for_non_vision_model`).
- **MIME-Type wird wirklich geprüft** — nicht nur der behauptete
  `data:image/…`-Präfix. Nach dem Base64-Decode werden die ECHTEN
  Magic-Bytes/Signaturen (PNG/JPEG/GIF/WebP) geprüft; stimmen sie nicht mit
  dem behaupteten Typ überein oder passt gar keine bekannte Signatur, wird
  abgelehnt (`400`) — eine Datei, die sich als Bild ausgibt, aber etwas
  anderes ist, kommt nie durch. Dieselbe Grundregel für PDFs (Signatur
  `%PDF-`): ein als PDF deklarierter Upload ohne diese Signatur wird
  abgelehnt statt als Text durchgereicht zu werden.
- **Größenlimits (DoS-Schutz)**: `MAX_IMAGE_BYTES` = 5 MB pro Bild (nach
  Base64-Decode geprüft), `MAX_IMAGES_PER_MESSAGE` = 4 Bilder pro Nachricht,
  `MAX_DOCUMENT_RAW_BYTES` = 10 MB Rohdatei — **vor** dem (potenziell teuren)
  PDF-Parsing geprüft, per gestreamtem Read (`app/http_limits.py::read_bounded_upload`,
  gleiches Prinzip wie bei Webhook-Bodies: ein `Content-Length`-Header allein
  reicht nicht). Ungültiges Base64 oder kaputte/korrupte Bild-/PDF-Daten
  geben eine klare `400` zurück, nie einen Crash.
- **Token-Reservierung**: Bild-Anhänge tragen 0 Zeichen zur
  zeichenbasierten `_estimate_tokens`-Schätzung bei, verursachen bei den
  meisten Anbietern aber realen Tokenverbrauch. `app/completions.py`
  reserviert deshalb zusätzlich `_IMAGE_TOKEN_RESERVE_PER_IMAGE` (grobe,
  dokumentierte Pauschale, analog `_WEB_TOOL_RESERVE_TOKENS`) pro Bild — nur
  als Rückfallebene relevant, wenn das Gateway kein `usage`-Objekt liefert;
  der Normalfall liefert echte Nutzungsdaten und ersetzt die Schätzung
  sofort danach.
- **Persistenz**: `messages.content` in der DB ist `text NOT NULL` und
  speichert keine Bild-Binärdaten (wäre unnötiges Aufblähen der Tabelle) —
  `app/completions.py::_stringify_content` extrahiert nur den Text-Anteil
  plus einen Platzhalter (`"[N Bild(er) angehängt]"`).

### Vision-Recherche: welche Modelle unterstützen Bild-Eingabe?

Jedes `"vision"`-Feld in `app/models_catalog.py::KNOWN_MODELS` ist gegen die
tatsächliche Anbieter-Dokumentation der jeweiligen Modell-**Familie**
recherchiert (nicht geraten) — volle Begründung je Eintrag im Moduldoc von
`models_catalog.py`. Kurzfassung:

| Vision = True | Quelle/Begründung |
|---|---|
| Anthropic Claude (Opus/Sonnet/Haiku, direkt + über OpenRouter) | Durchgehend multimodal seit Claude 3 — https://docs.claude.com/en/docs/build-with-claude/vision |
| OpenAI GPT-4o (direkt + über OpenRouter-Familie) | https://platform.openai.com/docs/guides/vision |
| Google Gemini (OpenRouter) | Nativ multimodal seit Gemini 1.5 |
| xAI Grok (OpenRouter) | Bild-Eingabe seit Grok-1.5V/Grok-2 |
| Meta Llama 4 Maverick (OpenRouter) | Meta hat Llama 4 (Scout/Maverick) explizit als nativ multimodal veröffentlicht — anders als Llama 3.x |

| Vision = False | Begründung |
|---|---|
| `ollama/llama3.2` (lokal) | Reine Text-Variante — **nicht** mit dem separaten `llama3.2-vision` verwechseln, das hier nicht registriert ist |
| Moonshot Kimi-K-Reihe, DeepSeek-V-Reihe, Qwen "-Max"-Reihe, Mistral "Large"-Reihe, Zhipu GLM-Chat-Flaggschiff, Microsoft "Phi-4" (ohne "-multimodal"), Cohere Command A, NVIDIA Nemotron | Bei allen ist Bild-Eingabe dokumentiert eine **separate** Modell-Linie (DeepSeek-VL, Qwen-VL, Pixtral, GLM-4V, Phi-4-multimodal, Aya Vision) — das hier registrierte Flaggschiff-Chatmodell selbst ist text-only. Bewusst `False` statt einer optimistischen Vermutung. |

### Was bewusst NICHT geht (kein Bug, kein Scope dieser Runde)

- **Kein Video, keine Audio-Anhänge** — nur Bilder (Vision) und
  Text-Dokumente (PDF/Text/Markdown).
- **Kein Frontend-UI** für Anhänge — weder `static/index.html` noch
  `static/dashboard.html` wurden in dieser Runde angefasst (parallele Arbeit
  eines anderen, sicherheitskritischen Agenten an genau diesen Dateien).
  Beide Endpunkte (`POST /v1/chat` mit Bild-Content-Blöcken, `POST
  /v1/attachments/extract`) sind vollständig funktionsfähig und getestet,
  aber nur per direktem API-Aufruf (curl/Client) nutzbar, bis das Frontend
  in einer Folge-Runde ergänzt wird.
- **Kein OCR für gescannte PDFs** — `pypdf` extrahiert nur eingebetteten
  Text; ein reiner Bildscan ohne Textebene liefert eine klare `400`
  ("PDF enthält keinen extrahierbaren Text"), keinen leeren Erfolg.
- **Keine Persistenz von Bild-Binärdaten** — weder in der DB noch als
  Datei-Storage (siehe oben, bewusste Design-Entscheidung).

Getestet gegen eine echte Postgres-DB: `tests/test_attachments.py` (reine
Validierungslogik, ohne DB), `tests/test_chat_vision_integration.py`
(Vision-Pflicht, Größenlimit, gefälschte MIME-Signatur, Rückwärts-
Kompatibilität des String-`content`-Pfads, jeweils End-to-End über
`/v1/chat`), `tests/test_attachments_integration.py` (`/v1/attachments/extract`
End-to-End inkl. Auth-Pflicht und Größenlimit vor dem Parsen),
`tests/test_agents_integration.py` (Regression: dieselbe Validierung greift
auch im Agenten-Chat-Pfad).

## Tests

```bash
pip install -r requirements.txt pytest
pytest -q                                  # Unit-Tests (ohne DB)

# Zusätzlich der echte RLS-Laufzeitbeweis gegen eine Postgres-Testdatenbank:
PLATFORM_TEST_DATABASE_URL=postgresql://postgres:...@localhost:5432/platform pytest -q
```

Abgedeckt: Tarif-Logik, Passwort-/Session-Token-Hashing, Schema-Struktur
(RLS/FORCE, Idempotenz) sowie — mit gesetzter Test-DB — der Laufzeit-Nachweis,
dass `app_rw` nur die Zeilen des gesetzten Mandanten sieht und ohne Kontext
gar keine. Der Web-Login-Pfad (Signup/Login/Session-Cookie/Rate-Limits, der
EINZIGE Auth-Weg) hat einen eigenen Laufzeit-Nachweis in
`tests/test_auth_integration.py` — inklusive des expliziten Beweises, dass
ein erfundener `Authorization: Bearer`-Header wirkungslos bleibt (401). Die
`prov()`-Test-Fixture (`tests/conftest.py`) provisioniert über
`/admin/provision` (jetzt mit Pflicht-Passwort) und meldet den `TestClient`
per `/v1/auth/login` an, statt einen API-Key als Header zu reichen; Tests,
die zwei GLEICHZEITIG gültige Mandanten-Sitzungen brauchen (RLS-Isolation),
nutzen dafür zwei unabhängige `TestClient`-Instanzen (`client2`/`prov2`) —
eine einzelne Instanz hält immer nur eine Session in ihrem Cookie-Jar. Die
CI (`platform-backend-ci.yml`) fährt dafür einen Postgres-Service hoch.

## Sicherheit

- **RLS real erzwungen** über die eingeschränkte Rolle `app_rw` (nicht Owner,
  kein BYPASSRLS); Migrationen laufen getrennt über eine privilegierte Rolle.
- Keine Secrets im Code — alles aus `.env` (in `.gitignore`); Compose ist
  fail-closed (`${VAR:?}`), keine bekannten Default-Passwörter.
- **Kein API-Key mehr** — das gesamte Konzept ist entfernt (Migration
  `013_drop_api_keys.sql`, `app/auth.py`). Der einzige Authentifizierungsweg
  ist das Session-Cookie, auch für Entwickler-/Programmzugriff.
- **Passwörter** (Web-Login) werden mit **bcrypt** gehasht (nicht SHA-256 —
  Passwörter haben niedrige Entropie und brauchen einen absichtlich
  langsamen, Brute-Force-resistenten Hash). Login-Fehlschläge liefern immer
  dieselbe generische Meldung, inkl. eines Dummy-Hash-Vergleichs bei
  unbekannter E-Mail gegen einen Timing-Seitenkanal. **Timing-Konstanz
  zwischen "E-Mail unbekannt" und "E-Mail bekannt, Passwort falsch"
  (Security-Review, behoben)**: der "bekannt"-Zweig macht neben dem
  `admin_tx()`-Lookup zusätzlich eine zweite `tenant_tx()`-DB-Rundreise vor
  dem bcrypt-Vergleich — ohne eine äquivalente Rundreise im "unbekannt"-Zweig
  wäre dieser messbar schneller gewesen (eine DB-Rundreise weniger), ein
  Timing-Seitenkanal, der verraten hätte, ob eine E-Mail existiert. Fix:
  `app/routes/auth.py::login()` führt im "unbekannt"-Zweig jetzt dieselbe Art
  Rundreise gegen eine feste, garantiert nie existierende Sentinel-
  Tenant/User-Kombination aus.
- **Session-Cookies** (Web-Login) nur als SHA-256-Hash gespeichert
  (hochentropischer Zufallstoken, kein Passwort), `HttpOnly` + `Secure` +
  `SameSite=Lax`. Kein CSRF-Token über `SameSite=Lax` hinaus (siehe
  Abschnitt "Web-Login") — bewusste, dokumentierte Einschränkung dieser
  Runde, kein Ersatz sollte Cross-Site-Einbettung gebraucht werden.
- `/admin/provision` per konstant-Zeit-Vergleich gegen `ADMIN_TOKEN`; verlangt
  jetzt zwingend ein initiales Passwort (Pflichtfeld, gleiche Länge/Grenzen
  wie `/v1/auth/signup`).
- Chat: Payload-Grenzen (Länge/Anzahl Messages), Konversations-Eigentumsprüfung,
  generische Upstream-Fehler (kein Info-Leak). Docker-Image als Nicht-root
  mit Healthcheck.
- **Rate-Limiting** pro Mandant auf `/v1/chat` und `/v1/agents/{id}/chat`
  (30 Aufrufe/60s, Sliding Window), pro IP **und** E-Mail auf
  `/v1/auth/signup` (je 5/Std. — die E-Mail-Komponente ist neu, Security-
  Review Punkt C: bremst verteilte Masse-Enumeration derselben Ziel-E-Mail
  über viele IPs, die ein reines IP-Limit nicht abdeckt) und pro IP **und**
  E-Mail auf `/v1/auth/login` (je 8-20/5min, siehe Abschnitt "Web-Login").
  Zusätzlich pro IP auf `GET /v1/checkout/{session_id}/claim` (20/5min,
  Security-Review Punkt B — dieser unauthentifizierte, schreibende Endpunkt
  hatte bisher **kein** Rate-Limiting, obwohl er wie Login/Signup öffentlich
  erreichbar ist und eine DB-Schreiboperation auslöst). In-Process per
  Default (ein Prozess genuegt fuer lokale Entwicklung); `REDIS_URL` setzen
  fuer horizontale Skalierung (mehrere Prozesse/Pods teilen sich dann EIN
  Kontingent statt je eines) — atomar per Lua-Script, siehe
  `app/ratelimit.py` und `tests/test_ratelimit_redis.py` (Test gegen echten
  lokalen redis-server).
- **E-Mail-Enumeration über `/v1/auth/signup`** (409 "bereits registriert"
  verrät, ob eine E-Mail schon existiert): akzeptierter, bei Self-Service-
  Signup üblicher Trade-off (anders als Login wird dieser Zweig nicht auf
  Nicht-Unterscheidbarkeit gehärtet) — durch den neuen E-Mail-Rate-Limiter
  (s.o.) zumindest gegen Masse-Enumeration gebremst, aber nicht grundsätzlich
  beseitigt.

## Status / bewusst offen (Phase 3+)

Aus den Reviews dokumentiert, nicht vergessen:
- ~~Harte Token-Limit-Durchsetzung (TOCTOU zwischen Check und Persistenz)~~
  — **behoben**: `app/completions.py` reserviert das Token-Kontingent jetzt
  ATOMAR (`_reserve_tokens`, ein einzelnes `UPDATE ... WHERE ...`) BEVOR das
  Gateway kontaktiert wird, statt nur vorab zu pruefen. Postgres serialisiert
  konkurrierende Reservierungen auf derselben `tenants`-Zeile automatisch —
  zwei gleichzeitige Anfragen koennen das Limit nicht mehr gemeinsam
  ueberschreiten. Die Reservierung wird NICHT waehrend des (langsamen)
  Gateway-Aufrufs gehalten (eigener kurzer Commit davor/danach), um den
  kleinen DB-Verbindungspool (`max_size=10`) nicht zu blockieren. Mit
  echter Nebenlaeufigkeit getestet (zwei Threads, zwei DB-Verbindungen,
  nicht nur sequenziell — der alte Bug zeigte sich nur bei echtem Race):
  `tests/test_token_reservation.py`. Bekannte Restluecke: reservierte
  Tokens bleiben "haengen", falls der Prozess mitten im Request abstuerzt
  (kein periodischer Aufraeum-Job); bei normalem Fehlerpfad (Gateway-Fehler,
  Timeout, Exception) wird immer freigegeben.
- ~~Nutzungsbasierte Abrechnung: usage_events ist die Datengrundlage, aber
  der Verbrauch wird nicht an Stripe gemeldet~~ — **umgesetzt, mit echter
  Einschraenkung**: `app/stripe_usage.py` meldet nach jedem abgeschlossenen
  Chat-Aufruf (streamend wie nicht-streamend) den Token-Verbrauch als
  Stripe-Meter-Event (`event_name="platform_tokens"`), sofern
  `STRIPE_SECRET_KEY` gesetzt UND der Mandant einen verknuepften
  `stripe_customer_id` hat (aus `link_stripe_customer`, siehe `billing.py`).
  Ohne den Key: no-op, kein Fehler — Verbrauch bleibt wie bisher nur lokal
  in `usage_events`/`GET /v1/usage` sichtbar. Meldung ist Best-Effort: ein
  Stripe-Ausfall wird geloggt, laesst aber nie einen Chat-Request scheitern.
  **Ehrliche Grenze**: in dieser Umgebung existiert kein echter Stripe-
  Account, daher ist nur die Aufrufstruktur (Endpoint, Feldnamen, Auth)
  gegen die oeffentliche Stripe-Dokumentation gebaut und mit einem
  gefaelschten HTTP-Client getestet (`tests/test_stripe_usage.py`) — nicht
  gegen die echte Stripe-API verifiziert. In Stripe muss vorher ein Billing-
  Meter mit exakt diesem `event_name` angelegt werden.
- ~~Token-Undercount, wenn das Gateway kein `usage`-Objekt liefert~~ —
  **behoben**: `app/completions.py` schaetzt Tokens (~4 Zeichen/Token) wenn
  `usage` fehlt, statt still 0 zu zaehlen — sonst haette ein Mandant ueber
  ein Modell ohne `usage`-Feld effektiv unbegrenzt und unverrechnet chatten
  koennen. Kein echter Tokenizer (ungenau), aber verhindert den
  Total-Blindspot. Getestet inkl. Beweis, dass der geschaetzte Verbrauch
  wirklich gegen `GET /v1/usage` und das Monats-Limit zaehlt:
  `tests/test_completions_token_estimate.py`.
- **Verbrauchsverlust bei Persistenz-Fehlern: teilweise behoben.**
  `_persist_and_release_with_retry` in `app/completions.py` wiederholt die
  Persistenz-Transaktion bis zu 3× (kurzer Backoff dazwischen), wenn sie
  nach einem bereits erfolgreichen (kostenpflichtigen) Gateway-Aufruf
  fehlschlägt — deckt den häufigeren Fall ab: einen kurzen transienten
  DB-Fehler (Verbindungsabbruch, Pool-Spitze) innerhalb derselben Anfrage.
  **Nicht behoben:** ein voller Outbox mit Wiederaufnahme über
  Prozessneustarts hinweg bleibt Phase 4 (braucht eine Queue) — stirbt der
  Prozess mitten in allen 3 Versuchen, ist die Antwort trotzdem weg, nur
  vollständig geloggt statt still verschwunden. Getestet (Retry-Logik
  isoliert, nicht die DB-Schicht selbst): `tests/test_persist_retry.py`.
- ~~Streaming (`stream`-Param) noch nicht unterstützt~~ — **umgesetzt**:
  `POST /v1/chat` und `POST /v1/agents/{id}/chat` mit `"stream": true`
  liefern Server-Sent-Events (OpenAI-kompatibles Chunk-Format), direkt vom
  LiteLLM-Gateway durchgereicht. Modellvalidierung, Konversationspruefung
  und Token-Reservierung laufen VOR dem ersten gesendeten Byte (danach ist
  der HTTP-Statuscode fest auf 200). Bittet das Gateway per
  `stream_options.include_usage` um echte Nutzungsdaten im letzten Chunk;
  fehlen sie, greift dieselbe Schaetzung wie im nicht-streamenden Pfad.
  Reservierung wird nach Streamende (Erfolg wie Fehler) zuverlaessig
  freigegeben. Getestet mit einem gefaelschten SSE-Gateway gegen eine echte
  Postgres-DB: `tests/test_chat_streaming.py`.
- ~~Enterprise-`"*"` laesst jedes Modell zu; unbekannte enden als 502 statt
  403~~ — **stimmt nicht (mehr)**: `is_registered()` in `models_catalog.py`
  prueft unabhaengig vom Tarif-Wildcard gegen die registrierte Gateway-Liste,
  bevor ueberhaupt an das Gateway weitergeleitet wird. Empirisch bestaetigt
  (26.07., echte Postgres-DB) und als Regressionstest festgehalten:
  `tests/test_model_validation_integration.py`.
- ~~Modellwechsel-UI + Agenten-Ebene (Phase 3); Store-Webhook `orders/paid` →
  `/admin/provision` (Phase 5)~~ — **umgesetzt**: Modellauswahl in
  `static/index.html` (`#model`-Select, befüllt aus `GET /v1/models`),
  Agenten-Endpunkte in `app/routes/agents.py` (`GET/POST /v1/agents`,
  `POST /v1/agents/{id}/chat`), Store-Webhook in `app/routes/webhooks.py`
  (`POST /webhooks/shopify/orders-paid`, HMAC-verifiziert, idempotent über
  `claim_event`, ruft `provision_tenant` in derselben Transaktion auf).
- **`/v1/integrations`** hat jetzt einen echten OAuth-Weg über Composio
  (`app/composio_client.py`), statt selbst Client-IDs/Secrets pro Provider zu
  verwalten: `COMPOSIO_API_KEY` gesetzt → `POST /v1/integrations` initiiert
  eine echte Verbindung und liefert eine echte Login-URL (`connect_url`)
  zurück; `POST /v1/integrations/{id}/refresh` fragt den echten
  Verbindungsstatus ab und setzt `status` auf `connected`, sobald Composio
  das bestätigt. Mandantentrennung (RLS) und Tarif-Limit
  (`plans.max_integrations`) bleiben unabhängig davon durchgesetzt und
  getestet. **Ohne** `COMPOSIO_API_KEY` (kein Composio-Account in dieser
  Umgebung) bleibt exakt das bisherige Gerüst-Verhalten: `status` bleibt
  beim Anlegen immer `disconnected`, keine externe Anfrage, kein Fehler.
  Noch offen: verschlüsselte Token-Speicherung, falls Composio in `config`
  mehr als die Connected-Account-ID zurückgibt.
- **`/v1/integrations`: „github“ und „shopify“ als weitere Provider** —
  `KNOWN_PROVIDERS` in `app/routes/integrations.py` umfasst jetzt
  `slack`/`notion`/`google`/`github`/`shopify`. Anders als „google“ (das bei
  Composio in einzelne Produkte wie „gmail“ aufgeteilt ist) sind „github“ und
  „shopify“ Composios eigene, öffentlich dokumentierte App-Slugs und werden
  unverändert durchgereicht (`composio_app_slug()` gibt unbekannte Provider
  wörtlich zurück). Wie beim „google“→„gmail“-Mapping gilt: aus Composios
  öffentlicher Doku entnommen, in dieser Umgebung **nicht** gegen einen
  echten Composio-Account verifiziert — vor dem ersten echten Einsatz im
  Composio-Dashboard nachschlagen. Migration `011_integrations_more_providers.sql`
  erweitert die DB-seitige CHECK-Constraint entsprechend. Getestet:
  `tests/test_integrations_composio.py::test_github_and_shopify_are_accepted_and_passed_through_unchanged`.
- **Web-Lese-Werkzeug im Chat (`web_fetch`), streng begrenzt** — die KI kann
  im nicht-streamenden `/v1/chat`-Pfad optional den Text einer öffentlichen
  Webseite lesen, um eine Frage besser zu beantworten (z.B. „was steht auf
  https://…“). Implementiert in `app/web_fetch_tool.py`
  (SSRF-Absicherung + Extraktion) und `app/completions.py::run_chat`
  (Tool-Call-Orchestrierung).
  - **Opt-in, nicht global**: nur wenn die Anfrage `"enable_web_tool": true`
    setzt, wird das Tool überhaupt an das Gateway gereicht
    (`tools=[web_fetch-Schema]`, `tool_choice: "auto"`). Ohne das Flag ist
    das Verhalten exakt wie zuvor — kein bestehender Test/Chat-Aufruf
    ändert sich.
  - **Nur der nicht-streamende Pfad** (`run_chat`) bekommt das Tool. Der
    SSE-Streaming-Pfad (`stream_chat`/`_stream_events`) ignoriert
    `enable_web_tool` bewusst — Tool-Calls im SSE-Chunk-Format zu parsen ist
    deutlich komplexer und ist eine bewusste, dokumentierte Einschränkung
    dieser ersten Runde, kein Bug.
  - **Ablauf**: antwortet das Gateway mit `tool_calls`, führt der Server
    `web_fetch` selbst aus, hängt das Ergebnis als `role: tool`-Nachricht an
    und ruft das Gateway ein zweites (und letztes) Mal auf, diesmal ohne
    `tools`, um eine endgültige Antwort zu erzwingen. Harte Obergrenzen im
    Code (nicht nur Kommentar): höchstens 3 Tool-Calls pro Anfrage
    (`MAX_TOOL_CALLS_PER_REQUEST`), höchstens 2 Gateway-Rundgänge insgesamt
    (`MAX_GATEWAY_ROUNDS`, strukturell erzwungen — es gibt im Code schlicht
    keinen dritten `_post_gateway`-Aufruf).
  - **Was es kann**: HTTP-GET auf eine vom Modell/Nutzer genannte
    `http(s)://`-URL, Text grob aus dem HTML extrahiert, auf ~6000 Zeichen
    gekürzt, als Tool-Ergebnis an das Modell zurückgegeben.
  - **Was es bewusst NICHT kann** (kein Bug, kein Scope): kein Login, keine
    Formulare, keine Cookies/Sessions, kein Klicken, keine Browser-
    Automation, keine Aktionen mit Nebeneffekten auf fremden Seiten — nur
    Lesen von öffentlich erreichbarem Text. Kein Einsatz im SSE-Streaming-
    Pfad.
  - **SSRF-Absicherung** (das Kernstück, siehe `app/web_fetch_tool.py`):
    nur `http`/`https` erlaubt; Hostname wird per DNS aufgelöst und JEDE
    aufgelöste Adresse gegen `ipaddress` geprüft (`is_private`,
    `is_loopback`, `is_link_local`, `is_multicast`, `is_reserved`,
    `is_unspecified`) — blockt u.a. `127.0.0.1` (auch als IPv4-mapped-IPv6
    `::ffff:127.0.0.1`, Dezimal `2130706433`, Hex `0x7f000001` oder verkürzt
    `127.1`), den Cloud-Metadata-Endpunkt `169.254.169.254` (auch via
    Userinfo-Verwirrung `user@169.254.169.254`), `10.x`/`172.16-31.x`/
    `192.168.x`, `::1`; Redirects werden manuell verfolgt
    (`follow_redirects=False`, max. 3 Hops) und bei JEDEM Hop erneut geprüft,
    damit ein Redirect die Sperre nicht umgehen kann; Timeout 8s;
    Antwortgröße per gestreamtem Read auf 2 MB begrenzt; jeder Fehler
    (Sicherheits-Ablehnung, DNS-Fehler, Timeout, HTTP-Fehler) liefert ein
    klares Fehler-Tool-Ergebnis statt die Chat-Anfrage abstürzen zu lassen.
    - **DNS-Aufloesung non-blocking** (Sicherheitsreview, Finding 1,
      behoben): `check_url_is_safe`/`_ensure_public_host` sind `async def`;
      der `socket.getaddrinfo`-Call läuft per
      `loop.run_in_executor(None, socket.getaddrinfo, ...)` in einem Thread
      und ist mit `asyncio.wait_for(timeout=3.0)` begrenzt. Vorher blockierte
      ein absichtlich nicht antwortender Nameserver den GESAMTEN
      Event-Loop des Worker-Prozesses (alle Mandanten, nicht nur den
      auslösenden) für die volle Resolver-Timeout-Dauer. Dokumentiertes
      Restrisiko: der ausgelagerte Thread selbst lässt sich nicht hart
      abbrechen und läuft im Hintergrund bis der Resolver aufgibt — bei
      sehr vielen gleichzeitigen, absichtlich hängenden Lookups kann das
      den Default-Executor-Threadpool auf Dauer belegen; das eigentliche
      HOCH-Risiko (Event-Loop-Blockade, alle Mandanten betroffen) ist damit
      aber gelöst.
    - **DNS-Rebinding strukturell ausgeschlossen** (Sicherheitsreview,
      Finding 2, behoben): früher löste die Prüfung den Hostnamen auf und
      httpx danach — beim eigentlichen Request — ein ZWEITES, unabhängiges
      Mal; ein Angreifer mit eigenem autoritativem Nameserver konnte der
      Prüfung eine öffentliche IP zeigen und dem echten Connect
      Sekunden später `169.254.169.254`/`127.0.0.1`. Jetzt löst
      `check_url_is_safe` den Hostnamen GENAU EINMAL pro Hop auf und gibt
      `(host, pinned_ip)` zurück; der tatsächliche Request verbindet sich
      per `httpx.URL.copy_with(host=pinned_ip)` DIREKT zu dieser IP — httpx
      bekommt dadurch keine Gelegenheit mehr für eine eigene Auflösung.
      Damit HTTPS (SNI + Zertifikatsprüfung) und namensbasiertes virtuelles
      Hosting trotzdem korrekt bleiben, tragen `Host`-Header und die
      httpx/httpcore-Request-Extension `extensions={"sni_hostname": host}`
      weiterhin den Original-Hostnamen (httpcore ≥ 0.28 reicht
      `sni_hostname` als `server_hostname` an den TLS-Handshake durch, dort
      wird auch die Zertifikatsprüfung dagegen validiert — praktisch
      verifiziert gegen einen lokalen HTTPS-Server mit selbstsigniertem
      Zertifikat: Connect per IP gelingt mit korrektem Host/SNI, dieselbe
      Verbindung OHNE die Überschreibung schlägt nachweislich mit
      `CERTIFICATE_VERIFY_FAILED: … IP address mismatch` fehl).
  - Getestet gegen eine echte Postgres-DB (Orchestrierung, Tool-Call-Cap,
    Rundgang-Cap, unverändertes Default-Verhalten):
    `tests/test_chat_web_tool.py`. **Pflicht-Tests für die SSRF-Absicherung**
    (isolierte Prüf-Funktion, kein echter Netzwerk-Request nötig):
    `tests/test_web_fetch_tool.py` — deckt u.a. `http://127.0.0.1/`,
    `http://169.254.169.254/latest/meta-data/`, `http://10.0.0.1/`,
    `http://[::1]/`, `file:///etc/passwd` sowie die o.g. Bypass-Schreibweisen
    ab; zusätzlich strukturelle Tests, die beweisen, dass `getaddrinfo` pro
    Hostname nur EINMAL pro `web_fetch()`-Durchlauf aufgerufen wird und der
    tatsächliche Connect gegen die zuerst validierte IP geht (Finding 2),
    sowie dass eine hängende DNS-Auflösung den Event-Loop nicht blockiert
    und nach `DNS_RESOLVE_TIMEOUT_S` klar fehlschlägt (Finding 1).
  - **Token-Reservierung** (Sicherheitsreview, Punkt 4, behoben): mit
    `enable_web_tool=True` reserviert `_reserve_or_429` zusätzlich zum
    üblichen `_RESPONSE_RESERVE_TOKENS`-Puffer noch
    `_WEB_TOOL_RESERVE_TOKENS = MAX_TOOL_CALLS_PER_REQUEST * MAX_RESULT_CHARS // 4`
    Tokens (grobe ~4-Zeichen/Token-Schätzung), weil bis zu 3 Tool-Ergebnisse
    (je bis zu 6000 Zeichen) zusätzlich in den zweiten Gateway-Rundgang
    einfließen können — vorher war die Vorab-Reservierung dafür pauschal zu
    knapp.
- **`dashboard.html`** ist noch nicht mit `index.html` verlinkt (nur ein
  „← Chat"-Link zurück) — beide UIs bewusst als getrennte, unabhängig
  ladbare Seiten gehalten.
- ~~Konversations-Fortsetzung faktisch kaputt: der Stream-Pfad gab die
  `conversation_id` nirgends an den Client zurück, jede Nachricht legte
  serverseitig eine neue Konversation an~~ — **behoben** (gefunden von
  `ultra-architect` beim Weiterentwicklungs-Audit, 27.07.): `stream_chat`
  löst die `conversation_id` jetzt VOR dem Gateway-Aufruf auf
  (`_resolve_conversation_id`) und `_stream_events` sendet sie als ersten
  SSE-Chunk. `static/index.html` liest sie aus dem Stream, speichert sie
  pro Mandant (Namensraum: `tenant_id`, seit der API-Key-Entfernung nicht
  mehr pro Schlüssel) in `localStorage` und hängt Folgenachrichten wirklich
  an dieselbe Konversation an; ein „+ Neu"-Button startet bewusst eine neue.
  Eine veraltete gespeicherte ID (404 vom Server) wird clientseitig einmalig
  automatisch verworfen und als neue Konversation fortgesetzt statt den Chat
  tot enden zu lassen. Echter Regressionstest gegen eine echte Postgres-DB
  (zwei Nachrichten landen nachweislich in derselben Konversation, nicht in
  zwei getrennten): `tests/test_chat_streaming.py::test_stream_returns_conversation_id_for_continuation`.
  Zusätzlich: mobiler mit Zeilenumbruch (`header{flex-wrap}` +
  `@media (max-width:640px)`) in `index.html` und `dashboard.html`, da der
  Header vorher auf schmalen Bildschirmen überlaufen konnte (keine
  Breakpoints trotz Viewport-Meta-Tag).

### Vom Weiterentwicklungs-Audit noch offen (nicht in dieser Runde umgesetzt)

- **Agenten-Chat im UI**: `POST /v1/agents/{id}/chat` ist voll funktionsfähig
  (inkl. Streaming), aber `dashboard.html` kann Agenten nur anlegen/löschen,
  nicht mit ihnen chatten — nur per eigenem curl-Aufruf nutzbar.
- **`/v1/integrations` ohne UI**: Composio-OAuth-Fluss ist serverseitig
  fertig und getestet, aber im Dashboard nicht bedienbar (kein Widget in der
  `WIDGETS`-Registry).
- **Kein Passwort-Reset** (Web-Login): keine SMTP-/E-Mail-Infrastruktur in
  dieser Umgebung — siehe Abschnitt "Web-Login" für die volle Einschränkung.
- **Kein CSRF-Token** neben `SameSite=Lax`: bewusste Entscheidung für diese
  Runde (Same-Origin-App ohne Cross-Site-Formulare), dokumentiert im
  Abschnitt "Web-Login" — kein Ersatz, sollte Cross-Site-Einbettung
  gebraucht werden.
