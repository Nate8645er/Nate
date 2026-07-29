/**
 * Keycloak / OIDC-Login (Cutover, Phase-9-Fortsetzung) — reine, testbare
 * Bausteine für den Authorization-Code-Flow mit PKCE.
 *
 * Additiv und hinter dem Flag `keycloak_auth` (NEXT_PUBLIC_KEYCLOAK_AUTH). Das
 * bestehende Supabase-Login bleibt unverändert; dieser Pfad ist die §3-konforme
 * Alternative, auf die per Flag umgeschaltet werden kann.
 *
 * Ehrlich: Diese Funktionen sind vollständig unit-getestet. Der eigentliche
 * Browser-Redirect + Callback-Austausch braucht eine laufende Keycloak-Instanz
 * (Env unten); ohne sie meldet `keycloakConfig()` `configured: false`.
 */

export interface KeycloakConfig {
  issuer: string; // https://auth.example.com/realms/kunden
  clientId: string;
  redirectUri: string;
  configured: boolean;
}

/** Liest die (öffentliche) Keycloak-Konfiguration aus der Umgebung. */
export function keycloakConfig(env: Record<string, string | undefined> = process.env): KeycloakConfig {
  const issuer = (env.NEXT_PUBLIC_KEYCLOAK_ISSUER ?? "").trim().replace(/\/$/, "");
  const clientId = (env.NEXT_PUBLIC_KEYCLOAK_CLIENT_ID ?? "").trim();
  const redirectUri = (env.NEXT_PUBLIC_KEYCLOAK_REDIRECT_URI ?? "").trim();
  return { issuer, clientId, redirectUri, configured: Boolean(issuer && clientId && redirectUri) };
}

export function authorizationEndpoint(cfg: KeycloakConfig): string {
  return `${cfg.issuer}/protocol/openid-connect/auth`;
}

export function tokenEndpoint(cfg: KeycloakConfig): string {
  return `${cfg.issuer}/protocol/openid-connect/token`;
}

/** Base64URL-Kodierung eines ArrayBuffers (ohne Padding). */
export function base64UrlEncode(bytes: ArrayBuffer | Uint8Array): string {
  const arr = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let bin = "";
  for (const b of arr) bin += String.fromCharCode(b);
  const b64 = typeof btoa === "function" ? btoa(bin) : Buffer.from(bin, "binary").toString("base64");
  return b64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function randomBytes(n: number): Uint8Array {
  const arr = new Uint8Array(n);
  globalThis.crypto.getRandomValues(arr);
  return arr;
}

export interface Pkce {
  verifier: string;
  challenge: string;
}

/** Erzeugt ein PKCE-Paar (S256): zufälliger Verifier + SHA-256-Challenge. */
export async function generatePkce(): Promise<Pkce> {
  const verifier = base64UrlEncode(randomBytes(32));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
  return { verifier, challenge: base64UrlEncode(digest) };
}

/** Zufälliger state/nonce-Wert (CSRF-Schutz des Redirects). */
export function randomState(): string {
  return base64UrlEncode(randomBytes(16));
}

/** Baut die Authorize-URL für den Redirect zum Keycloak-Login. */
export function buildAuthorizeUrl(
  cfg: KeycloakConfig,
  params: { state: string; codeChallenge: string; scope?: string },
): string {
  const q = new URLSearchParams({
    response_type: "code",
    client_id: cfg.clientId,
    redirect_uri: cfg.redirectUri,
    scope: params.scope ?? "openid profile email",
    state: params.state,
    code_challenge: params.codeChallenge,
    code_challenge_method: "S256",
  });
  return `${authorizationEndpoint(cfg)}?${q.toString()}`;
}

export interface TokenResponse {
  access_token: string;
  refresh_token?: string;
  id_token?: string;
  expires_in?: number;
  token_type?: string;
}

/**
 * Tauscht den Authorization-Code gegen Tokens (PKCE, public client). Gibt bei
 * Fehler/Netzproblem `null` zurück — nie werfen (der Aufrufer zeigt dann eine
 * ehrliche Fehlermeldung statt eines halb-eingeloggten Zustands).
 */
export async function exchangeCode(
  cfg: KeycloakConfig,
  args: { code: string; verifier: string },
  opts: { fetchImpl?: typeof fetch; timeoutMs?: number } = {},
): Promise<TokenResponse | null> {
  if (!cfg.configured) return null;
  const f = opts.fetchImpl ?? fetch;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), opts.timeoutMs ?? 8000);
  try {
    const res = await f(tokenEndpoint(cfg), {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "authorization_code",
        client_id: cfg.clientId,
        redirect_uri: cfg.redirectUri,
        code: args.code,
        code_verifier: args.verifier,
      }).toString(),
      signal: ctrl.signal,
      cache: "no-store",
    });
    if (!res.ok) return null;
    const data = (await res.json()) as TokenResponse;
    return data?.access_token ? data : null;
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}
