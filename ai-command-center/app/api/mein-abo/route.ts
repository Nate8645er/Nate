/**
 * GET /api/mein-abo
 *
 * Liefert den echten Abo-Status der angemeldeten Kundin/des Kunden aus dem
 * Kunden-Store (nach dem Stripe-Kauf freigeschaltet). Identität kommt aus der
 * verifizierten Sitzung (acc_rt-Cookie), nie aus der Anfrage.
 *
 * Antwort: { planId, planName, status, aktiv } – oder ehrlich 501/401/404.
 */

import { sitzungBenutzer, supabaseKonfiguriert } from "@/lib/supabase";
import { aboFuerEmail, kundenStoreKonfiguriert } from "@/lib/kunden";
import { PAKETE } from "@/lib/preise";

export const runtime = "nodejs";

const AKTIVE_STATUS = new Set(["active", "trialing"]);

function refreshTokenAusCookie(cookieHeader: string | null): string | undefined {
  if (!cookieHeader) return undefined;
  for (const teil of cookieHeader.split(";")) {
    const [k, ...rest] = teil.trim().split("=");
    if (k === "acc_rt") return rest.join("=");
  }
  return undefined;
}

export async function GET(request: Request): Promise<Response> {
  if (!supabaseKonfiguriert() || !kundenStoreKonfiguriert()) {
    return Response.json({ error: "nicht-konfiguriert" }, { status: 501 });
  }

  const rt = refreshTokenAusCookie(request.headers.get("cookie"));
  const user = await sitzungBenutzer(rt);
  if (!user?.email) return Response.json({ error: "nicht-angemeldet" }, { status: 401 });

  const abo = await aboFuerEmail(user.email);
  if (!abo) return Response.json({ error: "kein-abo" }, { status: 404 });

  const paket = PAKETE.find((p) => p.planId === abo.plan_id);
  return Response.json({
    planId: abo.plan_id,
    planName: paket?.name ?? abo.plan_id,
    status: abo.status,
    aktiv: AKTIVE_STATUS.has(abo.status),
    // Nur an die eigene, verifizierte Sitzung – für die Selbstbedienung, falls
    // die E-Mail nicht ankam. customer_id/email werden bewusst NICHT geliefert.
    lizenzSchluessel: abo.license_key ?? null,
  });
}
