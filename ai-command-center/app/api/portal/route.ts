/**
 * POST /api/portal
 *
 * Öffnet das Stripe-Billing-Portal (Rechnungen, Zahlungsmittel, Kündigung).
 *
 * Sicherheit: Die Stripe-`customerId` kommt NIE aus dem Request-Body, sondern
 * wird serverseitig aus der authentifizierten Sitzung abgeleitet:
 *   acc_rt-Cookie → Supabase-User (verifiziert) → E-Mail → gespeicherte customerId.
 * So kann niemand über eine fremde `cus_…`-ID ein fremdes Portal öffnen (IDOR).
 *
 * Ehrlich „nicht-konfiguriert" (501), solange Login (Supabase) oder Kunden-Store
 * fehlen. Kein Abo hinterlegt → 404.
 */

import { billingPortalSessionErstellen } from "@/lib/stripe";
import { sitzungBenutzer, supabaseKonfiguriert } from "@/lib/supabase";
import { customerIdFuerEmail, kundenStoreKonfiguriert } from "@/lib/kunden";

export const runtime = "nodejs";

function refreshTokenAusCookie(cookieHeader: string | null): string | undefined {
  if (!cookieHeader) return undefined;
  for (const teil of cookieHeader.split(";")) {
    const [k, ...rest] = teil.trim().split("=");
    if (k === "acc_rt") return rest.join("=");
  }
  return undefined;
}

export async function POST(request: Request): Promise<Response> {
  if (!supabaseKonfiguriert() || !kundenStoreKonfiguriert()) {
    return Response.json({ error: "nicht-konfiguriert" }, { status: 501 });
  }

  const rt = refreshTokenAusCookie(request.headers.get("cookie"));
  const user = await sitzungBenutzer(rt);
  if (!user?.email) return Response.json({ error: "nicht-angemeldet" }, { status: 401 });

  const customerId = await customerIdFuerEmail(user.email);
  if (!customerId) return Response.json({ error: "kein-abo" }, { status: 404 });

  // Return-URL aus konfigurierter App-URL (Allowlist) statt aus dem Origin-Header.
  const origin =
    process.env.APP_URL ||
    process.env.NEXT_PUBLIC_APP_URL ||
    new URL(request.url).origin ||
    "";

  const result = await billingPortalSessionErstellen(customerId, origin);
  if ("url" in result) return Response.json({ url: result.url });

  const status = result.error === "nicht-konfiguriert" ? 501 : 400;
  return Response.json({ error: result.error }, { status });
}
