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

import { createHmac, timingSafeEqual } from "node:crypto";
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

/**
 * Erstellt eine Stripe-Billing-Portal-Session, damit Kund:innen Rechnungen,
 * Zahlungsmittel und Kündigung selbst verwalten. Benötigt die Stripe-Customer-ID
 * (aus dem Checkout/Webhook). Ohne Key ehrlich „nicht-konfiguriert".
 */
export async function billingPortalSessionErstellen(
  customerId: string,
  origin: string,
  env: Record<string, string | undefined> = process.env,
  fetchImpl: typeof fetch = fetch,
): Promise<{ url: string } | { error: "nicht-konfiguriert" | "customer-fehlt" | "stripe-fehler" }> {
  if (!stripeKonfiguriert(env)) return { error: "nicht-konfiguriert" };
  if (!customerId) return { error: "customer-fehlt" };
  try {
    const res = await fetchImpl("https://api.stripe.com/v1/billing_portal/sessions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${env.STRIPE_SECRET_KEY}`,
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formEncode({ customer: customerId, return_url: `${origin}/konto` }),
    });
    if (!res.ok) return { error: "stripe-fehler" };
    const data = (await res.json()) as { url?: string };
    if (!data.url) return { error: "stripe-fehler" };
    return { url: data.url };
  } catch {
    return { error: "stripe-fehler" };
  }
}

/**
 * Prüft die Signatur eines Stripe-Webhooks (Header `Stripe-Signature`) gegen das
 * Signing-Secret (`whsec_…`) – dependency-frei via HMAC-SHA256, wie in Stripes
 * offizieller Bibliothek. Verhindert gefälschte Freischaltungen.
 *
 * @param payload roher Request-Body (String, unverändert!)
 * @param sigHeader Wert des `Stripe-Signature`-Headers
 * @param secret   STRIPE_WEBHOOK_SECRET
 * @param toleranzSek erlaubte Zeitabweichung (Standard 5 Min gegen Replay)
 * @param jetztSek  aktuelle Zeit in Sekunden (injizierbar für Tests)
 */
export function stripeWebhookVerifizieren(
  payload: string,
  sigHeader: string | null,
  secret: string | undefined,
  toleranzSek = 300,
  jetztSek: number = Math.floor(Date.now() / 1000),
): { ok: true } | { ok: false; grund: "kein-secret" | "kein-header" | "format" | "veraltet" | "ungueltig" } {
  if (!secret) return { ok: false, grund: "kein-secret" };
  if (!sigHeader) return { ok: false, grund: "kein-header" };

  let t = "";
  const v1: string[] = [];
  for (const teil of sigHeader.split(",")) {
    const [k, val] = teil.split("=");
    if (k === "t") t = val ?? "";
    else if (k === "v1" && val) v1.push(val);
  }
  if (!t || v1.length === 0) return { ok: false, grund: "format" };

  const zeit = Number(t);
  if (!Number.isFinite(zeit)) return { ok: false, grund: "format" };
  if (Math.abs(jetztSek - zeit) > toleranzSek) return { ok: false, grund: "veraltet" };

  const erwartet = createHmac("sha256", secret).update(`${t}.${payload}`).digest("hex");
  const erwartetBuf = Buffer.from(erwartet, "utf8");
  // Konstante Zeit; mind. eine v1-Signatur muss passen.
  const treffer = v1.some((sig) => {
    const sigBuf = Buffer.from(sig, "utf8");
    return sigBuf.length === erwartetBuf.length && timingSafeEqual(sigBuf, erwartetBuf);
  });
  return treffer ? { ok: true } : { ok: false, grund: "ungueltig" };
}

export interface WebhookAbo {
  customerId: string;
  email: string | null;
  planId: string;
  status: string;
}

/**
 * Liest aus einem (bereits signatur-verifizierten) Stripe-Ereignis die für die
 * Freischaltung nötigen Felder – robust über die relevanten Event-Typen.
 * Gibt null zurück, wenn das Ereignis nicht abo-relevant ist oder Pflichtfelder
 * (customerId/planId) fehlen. Reine Funktion → gut testbar.
 */
export function webhookEreignisDeuten(event: {
  type?: string;
  data?: { object?: Record<string, unknown> };
}): WebhookAbo | null {
  const typ = event.type ?? "";
  const obj = event.data?.object;
  if (!obj) return null;

  const relevant =
    typ === "checkout.session.completed" ||
    typ === "customer.subscription.created" ||
    typ === "customer.subscription.updated" ||
    typ === "customer.subscription.deleted";
  if (!relevant) return null;

  const customerId = typeof obj.customer === "string" ? obj.customer : "";
  const metadata = (obj.metadata as Record<string, unknown> | undefined) ?? {};
  const planId = typeof metadata.planId === "string" ? metadata.planId : "";

  // E-Mail liegt je nach Event an unterschiedlicher Stelle.
  const details = obj.customer_details as { email?: unknown } | undefined;
  const email =
    typeof obj.customer_email === "string" ? obj.customer_email
      : typeof details?.email === "string" ? details.email
        : null;

  // Status: bei Kündigung "canceled", bei Checkout "active", sonst vom Objekt.
  const status =
    typ === "customer.subscription.deleted" ? "canceled"
      : typeof obj.status === "string" ? obj.status
        : "active";

  if (!customerId || !planId) return null;
  return { customerId, email, planId, status };
}
