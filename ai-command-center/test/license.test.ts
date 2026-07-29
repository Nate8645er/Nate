/**
 * Unit-Tests für das stateless Lizenz- & Usage-System (lib/license.ts).
 * Deckt die risikoreiche Kern-Logik ab: Schlüssel-Signatur, Token-Ablauf,
 * Plan-Ableitung, Ultra-Aktivierung und serverseitiges Tageslimit.
 *
 * Das Secret wird für die Tests deterministisch gesetzt (die Lizenz-Funktionen
 * lesen es zur Laufzeit über licenseSecret(), nicht beim Import).
 */
process.env.LICENSE_SECRET = "test-secret-fuer-unit-tests-nur-lokal";

import { afterEach, describe, expect, it, vi } from "vitest";
import {
  PAID_PLANS,
  PLAN_LIMITS,
  effektivesLimit,
  effektivesTokenBudget,
  generateLicenseKey,
  verifyLicenseKey,
  generateUltraKey,
  verifyUltraKey,
  createLicenseToken,
  planFromLicenseToken,
  createUltraToken,
  ultraAktiv,
  consumeUsage,
  ULTRA_FAKTOR,
} from "../lib/license";

afterEach(() => {
  vi.useRealTimers();
});

describe("Lizenzschlüssel", () => {
  it("erzeugt für jeden Bezahlplan einen gültigen, korrekt geprüften Schlüssel", () => {
    for (const plan of PAID_PLANS) {
      const key = generateLicenseKey(plan);
      expect(key).toMatch(/^ACC-[A-Z]+-[A-Z2-7]{16}-[0-9A-F]{8}$/);
      const res = verifyLicenseKey(key);
      expect(res).toEqual({ valid: true, plan });
    }
  });

  it("weist einen manipulierten Schlüssel ab", () => {
    const key = generateLicenseKey("STARTER");
    // letzte Signaturstelle kippen
    const tampered = key.slice(0, -1) + (key.endsWith("0") ? "1" : "0");
    expect(verifyLicenseKey(tampered).valid).toBe(false);
  });

  it("weist falsches Format und leere Eingabe ab", () => {
    expect(verifyLicenseKey("nonsense").valid).toBe(false);
    expect(verifyLicenseKey("").valid).toBe(false);
    expect(verifyLicenseKey("ACC-FREE-AAAAAAAAAAAAAAAA-00000000").valid).toBe(false);
  });

  it("akzeptiert Kleinschreibung/Whitespace (wird normalisiert)", () => {
    const key = generateLicenseKey("BUSINESS");
    expect(verifyLicenseKey(`  ${key.toLowerCase()}  `)).toEqual({ valid: true, plan: "BUSINESS" });
  });
});

describe("Ultra-Codes", () => {
  it("round-trip gültig, und Ultra-Code ist kein normaler Lizenzschlüssel", () => {
    const ultra = generateUltraKey("PROFESSIONAL");
    expect(verifyUltraKey(ultra)).toEqual({ valid: true, plan: "PROFESSIONAL" });
    // Ultra-Code darf nicht als normaler Lizenzschlüssel durchgehen
    expect(verifyLicenseKey(ultra).valid).toBe(false);
    // und umgekehrt
    const lizenz = generateLicenseKey("PROFESSIONAL");
    expect(verifyUltraKey(lizenz).valid).toBe(false);
  });
});

describe("Lizenz-Token", () => {
  it("liefert den Plan aus einem frischen Token", () => {
    const { token } = createLicenseToken("BUSINESS");
    expect(planFromLicenseToken(token)).toBe("BUSINESS");
  });

  it("fehlend/manipuliert/abgelaufen ergibt FREE", () => {
    expect(planFromLicenseToken(null)).toBe("FREE");
    const { token } = createLicenseToken("STARTER");
    expect(planFromLicenseToken(token.slice(0, -1) + "x")).toBe("FREE");

    // Ablauf: Token jetzt erzeugen, Systemzeit um 31 Tage vorstellen
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-01-01T00:00:00Z"));
    const { token: t2 } = createLicenseToken("STARTER");
    expect(planFromLicenseToken(t2)).toBe("STARTER");
    vi.setSystemTime(new Date("2026-02-05T00:00:00Z")); // > 30 Tage
    expect(planFromLicenseToken(t2)).toBe("FREE");
  });
});

describe("Ultra-Aktivierung", () => {
  it("gilt nur für die passende Stufe und nicht für FREE", () => {
    const { token } = createUltraToken("STARTER");
    expect(ultraAktiv(token, "STARTER")).toBe(true);
    expect(ultraAktiv(token, "PROFESSIONAL")).toBe(false); // Stufe passt nicht
    expect(ultraAktiv(token, "FREE")).toBe(false);
    expect(ultraAktiv(null, "STARTER")).toBe(false);
  });
});

describe("effektive Limits", () => {
  it("Ultra hebt Tageslimit um den Faktor, Token-Budget deckelt bei 4096", () => {
    expect(effektivesLimit("STARTER", false)).toBe(PLAN_LIMITS.STARTER);
    expect(effektivesLimit("STARTER", true)).toBe(Math.ceil(PLAN_LIMITS.STARTER * ULTRA_FAKTOR));
    expect(effektivesTokenBudget("ENTERPRISE", true)).toBeLessThanOrEqual(4096);
  });
});

describe("consumeUsage (serverseitiges Tageslimit)", () => {
  it("erste Mission ist erlaubt und zählt auf 1", () => {
    const d = consumeUsage(null, "FREE");
    expect(d.allowed).toBe(true);
    expect(d.used).toBe(1);
    expect(d.limit).toBe(PLAN_LIMITS.FREE);
  });

  it("blockt, sobald das Limit erreicht ist", () => {
    let token: string | null = null;
    let last = consumeUsage(token, "FREE");
    for (let i = 1; i < PLAN_LIMITS.FREE; i++) {
      token = last.token;
      last = consumeUsage(token, "FREE");
      expect(last.allowed).toBe(true);
    }
    // nächster Versuch überschreitet das Limit
    const blocked = consumeUsage(last.token, "FREE");
    expect(blocked.allowed).toBe(false);
    expect(blocked.message).toContain("Tageslimit erreicht");
  });

  it("manipuliertes Usage-Token zählt als 0 (neuer Tag)", () => {
    const good = consumeUsage(null, "STARTER");
    const tampered = good.token.slice(0, -1) + "x";
    const d = consumeUsage(tampered, "STARTER");
    expect(d.used).toBe(1); // Manipulation verworfen -> beginnt bei 0, +1
  });

  it("Ultra erhöht das erlaubte Limit", () => {
    const d = consumeUsage(null, "PERSONAL", true);
    expect(d.limit).toBe(Math.ceil(PLAN_LIMITS.PERSONAL * ULTRA_FAKTOR));
  });

  it("neuer Tag setzt den Zähler zurück", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-03-10T12:00:00Z"));
    const day1 = consumeUsage(null, "PERSONAL");
    expect(day1.used).toBe(1);
    vi.setSystemTime(new Date("2026-03-11T09:00:00Z")); // nächster UTC-Tag
    const day2 = consumeUsage(day1.token, "PERSONAL");
    expect(day2.used).toBe(1); // Zähler zurückgesetzt
  });
});
