/**
 * GET /api/auth/keycloak/start  (Cutover, additiv, hinter Flag)
 *
 * Startet den OIDC-Authorization-Code-Flow (PKCE) und leitet zum Keycloak-Login
 * um. Nur aktiv, wenn `NEXT_PUBLIC_KEYCLOAK_AUTH` gesetzt UND Keycloak
 * konfiguriert ist — sonst ehrlich 404 (das bestehende Supabase-Login bleibt
 * der Standardweg). Verifier + state werden als HttpOnly-Cookies hinterlegt und
 * im Callback geprüft (CSRF-Schutz).
 */

import { buildAuthorizeUrl, generatePkce, keycloakConfig, randomState } from "@/lib/keycloak";
import { flagFromEnv } from "@/lib/flags";

export const runtime = "nodejs";

function cookie(name: string, value: string, maxAge = 600): string {
  // HttpOnly + SameSite=Lax (Redirect-Flow) + Secure; kurzlebig (10 min).
  return `${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=${maxAge}`;
}

export async function GET(): Promise<Response> {
  const cfg = keycloakConfig();
  if (!flagFromEnv("keycloak_auth") || !cfg.configured) {
    return Response.json({ error: "keycloak-nicht-aktiv" }, { status: 404 });
  }
  const { verifier, challenge } = await generatePkce();
  const state = randomState();
  const url = buildAuthorizeUrl(cfg, { state, codeChallenge: challenge });
  const headers = new Headers({ Location: url });
  headers.append("Set-Cookie", cookie("kc_verifier", verifier));
  headers.append("Set-Cookie", cookie("kc_state", state));
  return new Response(null, { status: 302, headers });
}
