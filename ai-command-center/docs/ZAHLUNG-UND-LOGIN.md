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
   Rechnungen/Kündigung. **Sicherheit:** Die Route ist bewusst deaktiviert (501),
   bis Login + Konto→Stripe-Zuordnung stehen. Die `customerId` wird dann
   serverseitig aus der Sitzung abgeleitet – **nie** aus dem Request-Body
   (sonst IDOR-Zugriff auf fremde Rechnungen). Die Portal-Funktion selbst
   (`billingPortalSessionErstellen` in `lib/stripe.ts`) ist fertig und getestet.

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
Aus dem Security-Review bereits umgesetzt: Webhook-Signatur konstante Zeit +
Replay-Schutz, Refresh-Token nur als HttpOnly/Secure-Cookie, Stripe-Key nie im
Client, generische Auth-/Webhook-Fehlermeldungen (keine User-Enumeration), Portal
gegen IDOR gesperrt. **Noch offen (mit der Kundendatenbank):**
- Konto→`customerId`-Zuordnung serverseitig, dann Portal aus der Sitzung freigeben.
- `origin`/Redirect-Basis gegen eine Allowlist (App-URL) prüfen statt Header trauen.
- Rate-Limit auf `/api/auth/*` (IP/Konto) gegen Brute-Force/Enumeration.

## Schnelltest ohne Live-Keys
`npm test` prüft beide Wege inkl. „nicht-konfiguriert", Webhook-Signatur
(gültig/veraltet/verändert) und Login-Flow mit injiziertem `fetch` –
komplett ohne echte Keys.
