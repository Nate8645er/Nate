/**
 * POST /api/auth/register
 *
 * Registriert eine neue Kundin/einen neuen Kunden per E-Mail + Passwort über
 * Supabase. Body: { email, passwort }. Antwort: { user } bei Erfolg – oder
 * ehrlich 501 „nicht-konfiguriert", solange Supabase nicht angebunden ist.
 * Je nach Supabase-Einstellung ist danach eine E-Mail-Bestätigung nötig.
 */

import { registrieren } from "@/lib/supabase";

export const runtime = "nodejs";

export async function POST(request: Request): Promise<Response> {
  let body: { email?: unknown; passwort?: unknown };
  try {
    body = (await request.json()) as typeof body;
  } catch {
    return Response.json({ error: "ungueltiger-body" }, { status: 400 });
  }
  const email = typeof body.email === "string" ? body.email.trim() : "";
  const passwort = typeof body.passwort === "string" ? body.passwort : "";

  const r = await registrieren(email, passwort);
  if (!r.ok) {
    const status = r.error === "nicht-konfiguriert" ? 501 : r.error === "ungueltige-daten" ? 400 : 422;
    // Rohmeldung nur serverseitig loggen: „User already registered" o.ä. würde
    // sonst verraten, welche E-Mails bereits Kunden sind (User-Enumeration).
    if (r.meldung) console.warn("[auth/register] Supabase:", r.meldung);
    const meldung =
      status === 422 ? "Registrierung nicht möglich. Bitte prüfen Sie Ihre Angaben oder melden Sie sich an." : undefined;
    return Response.json({ error: r.error, meldung }, { status });
  }
  return Response.json({ user: r.sitzung.user });
}
