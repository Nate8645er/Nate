/**
 * POST /api/portal
 *
 * Öffnet das Stripe-Billing-Portal (Rechnungen, Zahlungsmittel, Kündigung).
 *
 * WICHTIG (Sicherheit): Die Stripe-`customerId` DARF NICHT aus dem Request-Body
 * kommen – sonst könnte jemand mit einer fremden `cus_…`-ID das Portal eines
 * anderen Kontos öffnen (IDOR, Zugriff auf fremde Rechnungen/PII). Die ID muss
 * serverseitig aus der authentifizierten Sitzung (acc_rt-Cookie → Supabase-User
 * → gespeicherte customerId) nachgeschlagen werden. Diese Konto-Zuordnung
 * benötigt die Kundendatenbank (siehe docs/ZAHLUNG-UND-LOGIN.md).
 *
 * Solange diese sichere Zuordnung nicht existiert, bleibt die Route bewusst
 * deaktiviert (501) – ehrlich „nicht-konfiguriert" statt unsicher offen.
 */

export const runtime = "nodejs";

export async function POST(): Promise<Response> {
  return Response.json(
    {
      error: "nicht-konfiguriert",
      hinweis:
        "Das Kundenportal wird aktiv, sobald Login (Supabase) und die Konto→Stripe-" +
        "Zuordnung eingerichtet sind. Die customerId wird dann sicher aus der Sitzung " +
        "abgeleitet, nie aus der Anfrage übernommen.",
    },
    { status: 501 },
  );
}
