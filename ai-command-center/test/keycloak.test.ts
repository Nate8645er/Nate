import { describe, it, expect } from "vitest";
import {
  authorizationEndpoint,
  base64UrlEncode,
  buildAuthorizeUrl,
  exchangeCode,
  generatePkce,
  keycloakConfig,
  randomState,
  tokenEndpoint,
  type KeycloakConfig,
} from "@/lib/keycloak";

const CFG: KeycloakConfig = {
  issuer: "https://auth.example.com/realms/kunden",
  clientId: "acc-web",
  redirectUri: "https://app.example.com/api/auth/keycloak/callback",
  configured: true,
};

describe("Keycloak-OIDC-Bausteine (Cutover, additiv, hinter Flag)", () => {
  it("keycloakConfig: ehrlich not-configured ohne Env", () => {
    expect(keycloakConfig({}).configured).toBe(false);
    const full = keycloakConfig({
      NEXT_PUBLIC_KEYCLOAK_ISSUER: "https://x/realms/y/",
      NEXT_PUBLIC_KEYCLOAK_CLIENT_ID: "c",
      NEXT_PUBLIC_KEYCLOAK_REDIRECT_URI: "https://a/cb",
    });
    expect(full.configured).toBe(true);
    expect(full.issuer).toBe("https://x/realms/y"); // Slash getrimmt
  });

  it("Endpunkte werden korrekt abgeleitet", () => {
    expect(authorizationEndpoint(CFG)).toBe(`${CFG.issuer}/protocol/openid-connect/auth`);
    expect(tokenEndpoint(CFG)).toBe(`${CFG.issuer}/protocol/openid-connect/token`);
  });

  it("base64UrlEncode ist URL-sicher und ohne Padding", () => {
    const enc = base64UrlEncode(new Uint8Array([255, 224, 63]));
    expect(enc).not.toMatch(/[+/=]/);
  });

  it("generatePkce: Challenge = base64url(SHA-256(verifier))", async () => {
    const { verifier, challenge } = await generatePkce();
    expect(verifier.length).toBeGreaterThanOrEqual(43); // 32 Bytes base64url
    expect(challenge).not.toMatch(/[+/=]/);
    // Reproduzierbar: gleiche Verifier → gleiche Challenge.
    const digest = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(verifier));
    expect(challenge).toBe(base64UrlEncode(digest));
    expect(randomState()).not.toBe(randomState()); // zufällig
  });

  it("buildAuthorizeUrl enthält PKCE-S256 und alle Pflichtparameter", () => {
    const url = new URL(buildAuthorizeUrl(CFG, { state: "st1", codeChallenge: "ch1" }));
    expect(url.searchParams.get("response_type")).toBe("code");
    expect(url.searchParams.get("client_id")).toBe("acc-web");
    expect(url.searchParams.get("redirect_uri")).toBe(CFG.redirectUri);
    expect(url.searchParams.get("code_challenge")).toBe("ch1");
    expect(url.searchParams.get("code_challenge_method")).toBe("S256");
    expect(url.searchParams.get("state")).toBe("st1");
    expect(url.searchParams.get("scope")).toContain("openid");
  });

  it("exchangeCode: erfolgreicher Token-Tausch", async () => {
    let body = "";
    const fake = (async (_url: string, init: RequestInit) => {
      body = String(init.body);
      return new Response(JSON.stringify({ access_token: "AT", refresh_token: "RT" }), { status: 200 });
    }) as unknown as typeof fetch;
    const tok = await exchangeCode(CFG, { code: "c1", verifier: "v1" }, { fetchImpl: fake });
    expect(tok?.access_token).toBe("AT");
    expect(body).toContain("grant_type=authorization_code");
    expect(body).toContain("code_verifier=v1");
  });

  it("exchangeCode: HTTP-Fehler/nicht konfiguriert → null (nie werfen)", async () => {
    const bad = (async () => new Response("no", { status: 400 })) as unknown as typeof fetch;
    expect(await exchangeCode(CFG, { code: "c", verifier: "v" }, { fetchImpl: bad })).toBeNull();
    // Nicht konfiguriert → gar kein Request.
    const off = { ...CFG, configured: false };
    let called = false;
    const spy = (async () => {
      called = true;
      return new Response("{}");
    }) as unknown as typeof fetch;
    expect(await exchangeCode(off, { code: "c", verifier: "v" }, { fetchImpl: spy })).toBeNull();
    expect(called).toBe(false);
  });
});
