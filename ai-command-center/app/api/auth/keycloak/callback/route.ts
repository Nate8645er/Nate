/**
 * GET /api/auth/keycloak/callback  (Cutover, additiv, hinter Flag)
 *
 * Nimmt Keycloaks Redirect (code + state) entgegen, prüft den state gegen das
 * Cookie (CSRF), tauscht den Code per PKCE gegen Tokens und legt das
 * Access-Token als HttpOnly-Cookie ab. Nur aktiv bei gesetztem Flag +
 * konfiguriertem Keycloak — sonst ehrlich 404.
 *
 * Ehrlich: Der Live-Pfad braucht eine laufende Keycloak-Instanz. Die reine
 * Logik (PKCE, URL, Token-Tausch) ist in lib/keycloak.ts unit-getestet.
 */

import { exchangeCode, keycloakConfig } from "@/lib/keycloak";
import { flagFromEnv } from "@/lib/flags";

export const runtime = "nodejs";

function parseCookies(header: string | null): Record<string, string> {
  const out: Record<string, string> = {};
  if (!header) return out;
  for (const part of header.split(";")) {
    const i = part.indexOf("=");
    if (i > 0) out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  }
  return out;
}

const CLEAR = "; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0";

export async function GET(request: Request): Promise<Response> {
  const cfg = keycloakConfig();
  if (!flagFromEnv("keycloak_auth") || !cfg.configured) {
    return Response.json({ error: "keycloak-nicht-aktiv" }, { status: 404 });
  }
  const url = new URL(request.url);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const cookies = parseCookies(request.headers.get("cookie"));

  // CSRF: state MUSS mit dem beim Start gesetzten Cookie übereinstimmen.
  if (!code || !state || !cookies.kc_state || state !== cookies.kc_state) {
    return Response.json({ error: "ungueltiger-state" }, { status: 400 });
  }
  const verifier = cookies.kc_verifier;
  if (!verifier) {
    return Response.json({ error: "verifier-fehlt" }, { status: 400 });
  }

  const tokens = await exchangeCode(cfg, { code, verifier });
  if (!tokens) {
    return Response.json({ error: "token-tausch-fehlgeschlagen" }, { status: 502 });
  }

  // Access-Token als HttpOnly-Cookie; temporäre Flow-Cookies löschen.
  const headers = new Headers({ Location: "/" });
  const maxAge = Math.max(60, Math.min(tokens.expires_in ?? 300, 3600));
  headers.append("Set-Cookie", `kc_access=${tokens.access_token}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`);
  headers.append("Set-Cookie", `kc_verifier=${CLEAR}`);
  headers.append("Set-Cookie", `kc_state=${CLEAR}`);
  return new Response(null, { status: 302, headers });
}
