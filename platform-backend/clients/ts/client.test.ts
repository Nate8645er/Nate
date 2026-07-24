import { describe, it, expect } from "vitest";
import { PlatformBackendClient, PlatformBackendNichtKonfiguriert } from "./client";

describe("PlatformBackendClient", () => {
  it("ist ohne baseUrl ehrlich nicht-konfiguriert", () => {
    const c = new PlatformBackendClient();
    expect(c.configured).toBe(false);
    expect(() => c.buildUrl("/health")).toThrow(PlatformBackendNichtKonfiguriert);
  });

  it("baut URLs korrekt und schneidet abschliessenden Slash ab", () => {
    const c = new PlatformBackendClient({ baseUrl: "https://backend.example.com/" });
    expect(c.configured).toBe(true);
    expect(c.buildUrl("/health")).toBe("https://backend.example.com/health");
    expect(c.buildUrl("health/compute")).toBe("https://backend.example.com/health/compute");
  });

  it("ruft /health mit Bearer-Token über injizierten fetch auf", async () => {
    let gesehen: { url: string; auth?: string } | null = null;
    const fakeFetch = (async (url: string, init?: RequestInit) => {
      gesehen = { url: String(url), auth: (init?.headers as Record<string, string>)?.authorization };
      return { ok: true, json: async () => ({ status: "ok", version: "0.1.0", env: "test", services: {} }) } as Response;
    }) as unknown as typeof fetch;

    const c = new PlatformBackendClient({ baseUrl: "https://b", token: "tok", fetchImpl: fakeFetch });
    const h = await c.health();
    expect(h.status).toBe("ok");
    expect(gesehen!.url).toBe("https://b/health");
    expect(gesehen!.auth).toBe("Bearer tok");
  });

  it("wirft bei HTTP-Fehler", async () => {
    const fakeFetch = (async () => ({ ok: false, status: 503 }) as Response) as unknown as typeof fetch;
    const c = new PlatformBackendClient({ baseUrl: "https://b", fetchImpl: fakeFetch });
    await expect(c.compute()).rejects.toThrow(/HTTP 503/);
  });
});
