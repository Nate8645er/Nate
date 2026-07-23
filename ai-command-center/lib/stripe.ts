/**
 * Stripe-Checkout – dependency-frei über die Stripe-REST-API.
 *
 * Aktivierung: STRIPE_SECRET_KEY in der Umgebung setzen. Ohne Key meldet der
 * Checkout ehrlich „nicht konfiguriert" (kein Platzhalter, keine Fehlbuchung).
 *
 * Preise werden inline aus lib/preise.ts übergeben (price_data), damit kein
 * manuelles Anlegen von Stripe-Preisen nötig ist. Für Produktion können später
 * feste Price-IDs via STRIPE_PRICE_<PAKET> hinterlegt werden.
 */

import { PAKETE, type Paket } from "./preise";

export function stripeKonfiguriert(env: Record<string, string | undefined> = process.env): boolean {
  const k = env.STRIPE_SECRET_KEY;
  return typeof k === "string" && k.startsWith("sk_");
}

/** Form-URL-Encoding für die Stripe-API (verschachtelte Schlüssel). */
function formEncode(obj: Record<string, string | number>): string {
  return Object.entries(obj)
    .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
    .join("&");
}

/**
 * Erstellt eine Stripe-Checkout-Session (Abo) für ein Paket.
 * Gibt die Weiterleitungs-URL zurück – oder null, wenn nicht konfiguriert.
 */
export async function checkoutSessionErstellen(
  paketId: string,
  jahr: boolean,
  origin: string,
  env: Record<string, string | undefined> = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<{ url: string } | { error: "nicht-konfiguriert" | "unbekanntes-paket" | "stripe-fehler" }> {
  if (!stripeKonfiguriert(env)) return { error: "nicht-konfiguriert" };
  const paket = PAKETE.find((p: Paket) => p.id === paketId);
  // Enterprise läuft über Kontakt, die Gratis-Version über keinen Zahlungsweg.
  if (!paket || paket.id === "enterprise" || paket.preisMonat <= 0) {
    return { error: "unbekanntes-paket" };
  }

  const betrag = jahr ? paket.preisJahr : paket.preisMonat;
  const params: Record<string, string | number> = {
    mode: "subscription",
    "line_items[0][quantity]": 1,
    "line_items[0][price_data][currency]": "chf",
    "line_items[0][price_data][unit_amount]": Math.round(betrag * 100),
    "line_items[0][price_data][recurring][interval]": jahr ? "year" : "month",
    "line_items[0][price_data][product_data][name]": `AI Command Center – ${paket.name}`,
    // Plan-Zuordnung für die spätere Freischaltung nach dem Kauf.
    "metadata[planId]": paket.planId,
    "metadata[paket]": paket.id,
    "subscription_data[metadata][planId]": paket.planId,
    success_url: `${origin}/konto?kauf=erfolg&paket=${paket.id}`,
    cancel_url: `${origin}/preise?abgebrochen=1`,
    allow_promotion_codes: "true",
  };

  try {
    const res = await fetchImpl("https://api.stripe.com/v1/checkout/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formEncode(params),
    });
    if (!res.ok) return { error: "stripe-fehler" };
    const data = (await res.json()) as { url?: string };
    if (!data.url) return { error: "stripe-fehler" };
    return { url: data.url };
  } catch {
    return { error: "stripe-fehler" };
  }
}
