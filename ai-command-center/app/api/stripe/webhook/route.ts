/**
 * POST /api/stripe/webhook
 *
 * Empfängt Stripe-Ereignisse (z. B. checkout.session.completed) und verifiziert
 * die Signatur gegen STRIPE_WEBHOOK_SECRET, bevor irgendetwas freigeschaltet wird.
 * Ohne Secret antwortet die Route ehrlich 501 „nicht-konfiguriert"; bei ungültiger
 * Signatur 400. So kann niemand per gefälschtem Webhook ein Abo aktivieren.
 *
 * Die eigentliche Freischaltung (Plan aus metadata.planId → Lizenz/Datensatz)
 * hängt von der gewählten Kundendatenbank ab und wird hier bewusst als klar
 * markierter Anschlusspunkt gehalten – kein stiller Platzhalter in der Logik.
 */

import { stripeWebhookVerifizieren } from "@/lib/stripe";

export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret) return Response.json({ error: "nicht-konfiguriert" }, { status: 501 });

  // Rohen Body unverändert lesen – die Signatur gilt für die exakten Bytes.
  const payload = await request.text();
  const sig = request.headers.get("stripe-signature");

  const pruef = stripeWebhookVerifizieren(payload, sig, secret);
  if (!pruef.ok) {
    // Konkreten Grund nur serverseitig loggen; nach aussen generisch, damit ein
    // Fälscher keine Rückmeldung zur Feinjustierung (Timestamp vs. HMAC) erhält.
    console.warn("[stripe/webhook] Signatur abgelehnt:", pruef.grund);
    return Response.json({ error: "signatur-ungueltig" }, { status: 400 });
  }

  let event: { type?: string; data?: { object?: Record<string, unknown> } };
  try {
    event = JSON.parse(payload) as typeof event;
  } catch {
    return Response.json({ error: "ungueltiger-body" }, { status: 400 });
  }

  // Verifizierte Ereignisse: hier wird nach Anbindung der Kundendatenbank der
  // Plan freigeschaltet. Bis dahin bestätigen wir den Empfang (200), damit
  // Stripe nicht erneut zustellt.
  switch (event.type) {
    case "checkout.session.completed":
    case "customer.subscription.updated":
    case "customer.subscription.deleted":
      // planId liegt in event.data.object.metadata.planId bzw. subscription.metadata.
      break;
    default:
      break;
  }

  return Response.json({ received: true });
}
