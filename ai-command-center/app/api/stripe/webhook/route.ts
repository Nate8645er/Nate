/**
 * POST /api/stripe/webhook
 *
 * Empfängt Stripe-Ereignisse und verifiziert die Signatur gegen
 * STRIPE_WEBHOOK_SECRET, bevor irgendetwas freigeschaltet wird. Ohne Secret
 * ehrlich 501; bei ungültiger Signatur 400. So kann niemand per gefälschtem
 * Webhook ein Abo aktivieren.
 *
 * Nach erfolgreicher Verifikation wird der Plan aus dem Ereignis gelesen und –
 * sofern der Kunden-Store konfiguriert ist – das Abo freigeschaltet/aktualisiert.
 * Der Empfang wird immer mit 200 quittiert, damit Stripe nicht erneut zustellt.
 */

import { stripeWebhookVerifizieren, webhookEreignisDeuten } from "@/lib/stripe";
import { aboFreischalten, kundenStoreKonfiguriert } from "@/lib/kunden";

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

  const abo = webhookEreignisDeuten(event);
  if (abo) {
    if (kundenStoreKonfiguriert()) {
      const r = await aboFreischalten({
        customer_id: abo.customerId,
        email: abo.email,
        plan_id: abo.planId,
        status: abo.status,
      });
      if (!r.ok) {
        // 500 → Stripe stellt später erneut zu (Idempotenz via Upsert).
        console.error("[stripe/webhook] Freischaltung fehlgeschlagen:", r.error, abo.customerId);
        return Response.json({ error: "freischaltung-fehlgeschlagen" }, { status: 500 });
      }
    } else {
      // Verifiziert empfangen, aber Kunden-Store noch nicht angebunden.
      console.warn("[stripe/webhook] Abo-Event ohne Kunden-Store (kein Store konfiguriert):", abo.planId);
    }
  }

  return Response.json({ received: true });
}
