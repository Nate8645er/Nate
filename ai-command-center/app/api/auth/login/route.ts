/**
 * POST /api/auth/login
 *
 * Meldet eine Kundin/einen Kunden per E-Mail + Passwort über Supabase an.
 * Body: { email, passwort }. Antwort: { user } bei Erfolg – oder ehrlich
 * 501 „nicht-konfiguriert", solange Supabase nicht angebunden ist.
 * Das Refresh-Token wird als HttpOnly-Cookie gesetzt (nicht im JSON).
 */

import { anmelden } from "@/lib/supabase";
import { authLimitPruefen } from "@/lib/ratelimit";

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

  // Brute-Force-/Enumeration-Bremse (pro IP+E-Mail).
  const limit = await authLimitPruefen(request, "login", email);
  if (!limit.erlaubt) {
    return Response.json(
      { error: "zu-viele-versuche", meldung: "Zu viele Versuche. Bitte später erneut versuchen." },
      { status: 429, headers: { "Retry-After": String(limit.resetSek) } },
    );
  }

  const r = await anmelden(email, passwort);
  if (!r.ok) {
    const status = r.error === "nicht-konfiguriert" ? 501 : r.error === "ungueltige-daten" ? 400 : 401;
    // Rohmeldung nur serverseitig loggen (verhindert User-Enumeration); an den
    // Client geht eine generische Meldung.
    if (r.meldung) console.warn("[auth/login] Supabase:", r.meldung);
    const meldung = status === 401 ? "E-Mail oder Passwort ist nicht korrekt." : undefined;
    return Response.json({ error: r.error, meldung }, { status });
  }

  const res = Response.json({ user: r.sitzung.user });
  if (r.sitzung.refresh_token) {
    res.headers.append(
      "Set-Cookie",
      `acc_rt=${r.sitzung.refresh_token}; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=2592000`,
    );
  }
  return res;
}
