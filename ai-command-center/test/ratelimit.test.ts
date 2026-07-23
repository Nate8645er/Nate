/**
 * Tests für den Rate-Limiter: In-Memory-Fixed-Window (mit injizierter Zeit) und
 * verteilter Upstash-Pfad (mit injiziertem fetch), inkl. Fail-open bei Störung.
 */
import { describe, expect, it } from "vitest";
import { pruefeRateLimit, rateLimitVerteilt, clientIp } from "../lib/ratelimit";

const UP = { UPSTASH_REDIS_REST_URL: "https://x.upstash.io", UPSTASH_REDIS_REST_TOKEN: "tok" };

describe("rateLimitVerteilt", () => {
  it("nur mit Upstash-URL + Token", () => {
    expect(rateLimitVerteilt({})).toBe(false);
    expect(rateLimitVerteilt(UP)).toBe(true);
  });
});

describe("In-Memory-Limiter (Fixed Window)", () => {
  it("erlaubt bis zum Limit, dann blockiert; Fenster reset", async () => {
    const key = "test:mem:a";
    let ok = 0;
    for (let i = 0; i < 3; i++) {
      const r = await pruefeRateLimit(key, 3, 60, {}, fetch, 1000);
      if (r.erlaubt) ok++;
    }
    expect(ok).toBe(3);
    const blocked = await pruefeRateLimit(key, 3, 60, {}, fetch, 1000);
    expect(blocked.erlaubt).toBe(false);
    expect(blocked.modus).toBe("speicher");
    // Nach Fensterablauf wieder erlaubt.
    const nachReset = await pruefeRateLimit(key, 3, 60, {}, fetch, 1000 + 61_000);
    expect(nachReset.erlaubt).toBe(true);
  });
});

describe("Upstash-Limiter", () => {
  it("erlaubt solange count <= limit", async () => {
    let gesendet: unknown;
    const fakeFetch = (async (_u: string, init: RequestInit) => {
      gesendet = JSON.parse(String(init.body));
      return { ok: true, json: async () => [{ result: 2 }, { result: 1 }] };
    }) as unknown as typeof fetch;
    const r = await pruefeRateLimit("k", 10, 600, UP, fakeFetch);
    expect(r).toMatchObject({ erlaubt: true, verbleibend: 8, modus: "upstash" });
    expect(gesendet).toEqual([["INCR", "k"], ["EXPIRE", "k", "600", "NX"]]);
  });
  it("blockiert wenn count > limit", async () => {
    const fakeFetch = (async () => ({ ok: true, json: async () => [{ result: 11 }, { result: 0 }] })) as unknown as typeof fetch;
    const r = await pruefeRateLimit("k", 10, 600, UP, fakeFetch);
    expect(r.erlaubt).toBe(false);
  });
  it("fail-open bei Upstash-Fehler", async () => {
    const fakeFetch = (async () => { throw new Error("down"); }) as unknown as typeof fetch;
    const r = await pruefeRateLimit("k", 10, 600, UP, fakeFetch);
    expect(r.erlaubt).toBe(true);
  });
});

describe("clientIp", () => {
  it("bevorzugt vertrauenswürdiges x-real-ip vor spoofbarem x-forwarded-for", () => {
    // Angreifer setzt x-forwarded-for; x-real-ip (Plattform) muss gewinnen.
    expect(clientIp(new Headers({ "x-real-ip": "9.9.9.9", "x-forwarded-for": "1.1.1.1" }))).toBe("9.9.9.9");
  });
  it("nutzt x-forwarded-for nur als Fallback ohne x-real-ip", () => {
    expect(clientIp(new Headers({ "x-forwarded-for": "1.2.3.4, 5.6.7.8" }))).toBe("1.2.3.4");
  });
  it("ohne Header: unbekannt", () => {
    expect(clientIp(new Headers())).toBe("unbekannt");
  });
});
