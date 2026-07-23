/**
 * POST /api/checkout
 *
 * Startet einen Stripe-Checkout (Abo) für ein Paket. Body: { paket, jahr? }.
 * Antwort: { url } zum Weiterleiten – oder 501 { error: "nicht-konfiguriert" },
 * wenn STRIPE_SECRET_KEY fehlt. So bleibt die Verkaufsseite ehrlich, auch bevor
 * die Zahlung angebunden ist.
 */

import { checkoutSessionErstellen } from "@/lib/stripe";

export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  let body: { paket?: unknown; jahr?: unknown };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return Response.json({ error: "ungueltiger-body" }, { status: 400 });
  }
  const paket = typeof body.paket === "string" ? body.paket : "";
  const jahr = body.jahr === true;
  if (!paket) return Response.json({ error: "paket-fehlt" }, { status: 400 });

  const origin =
    request.headers.get("origin") ||
    new URL(request.url).origin ||
    "";

  const result = await checkoutSessionErstellen(paket, jahr, origin);
  if ("url" in result) return Response.json({ url: result.url });

  const status = result.error === "nicht-konfiguriert" ? 501 : 400;
  return Response.json({ error: result.error }, { status });
}
