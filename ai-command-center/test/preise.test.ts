/**
 * Tests der Verkaufs-/Preis-Logik: Paket-Daten-Konsistenz, Vergleichstabelle
 * und Stripe-Checkout (inkl. ehrlichem „nicht-konfiguriert" ohne Key).
 */
import { describe, expect, it } from "vitest";
import { PAKETE, VERGLEICH, chf } from "../lib/preise";
import { stripeKonfiguriert, checkoutSessionErstellen } from "../lib/stripe";

describe("Pakete & Vergleich", () => {
  it("jedes Paket hat gültige, vollständige Felder", () => {
    for (const p of PAKETE) {
      expect(p.id).toBeTruthy();
      expect(p.name).toBeTruthy();
      expect(["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"]).toContain(p.planId);
      expect(p.preisMonat).toBeGreaterThan(0);
      expect(p.preisJahr).toBeGreaterThan(0);
      expect(p.leistungen.length).toBeGreaterThan(0);
      expect(p.cta).toBeTruthy();
    }
  });
  it("hat eindeutige IDs und genau eine Hervorhebung", () => {
    const ids = PAKETE.map((p) => p.id);
    expect(new Set(ids).size).toBe(ids.length);
    expect(PAKETE.filter((p) => p.hervorgehoben).length).toBe(1);
  });
  it("Jahrespreis ist günstiger als 12 Monatspreise (Rabatt)", () => {
    for (const p of PAKETE) expect(p.preisJahr).toBeLessThan(p.preisMonat * 12);
  });
  it("Vergleichstabelle hat pro Zeile genau 3 Werte (je Paket)", () => {
    for (const g of VERGLEICH) for (const z of g.zeilen) expect(z.werte.length).toBe(3);
  });
  it("chf formatiert mit Währung und Tausender-Trennung", () => {
    expect(chf(1490)).toMatch(/^CHF 1.490$/); // Trenner je nach ICU (’, ' oder .)
    expect(chf(49)).toBe("CHF 49");
  });
});

describe("Stripe-Checkout", () => {
  it("erkennt Konfiguration nur bei gültigem sk_-Key", () => {
    expect(stripeKonfiguriert({})).toBe(false);
    expect(stripeKonfiguriert({ STRIPE_SECRET_KEY: "pk_test_x" })).toBe(false);
    expect(stripeKonfiguriert({ STRIPE_SECRET_KEY: "sk_test_x" })).toBe(true);
  });

  it("ohne Key ehrlich nicht-konfiguriert", async () => {
    const r = await checkoutSessionErstellen("basic", false, "https://x.ch", {});
    expect(r).toEqual({ error: "nicht-konfiguriert" });
  });

  it("Enterprise ist kein Self-Checkout", async () => {
    const r = await checkoutSessionErstellen("enterprise", false, "https://x.ch", { STRIPE_SECRET_KEY: "sk_test_x" });
    expect(r).toEqual({ error: "unbekanntes-paket" });
  });

  it("mit Key wird eine Checkout-Session mit korrekten Beträgen erstellt", async () => {
    let gesendet = "";
    const fakeFetch = (async (_url: string, init: RequestInit) => {
      gesendet = String(init.body);
      return { ok: true, json: async () => ({ url: "https://checkout.stripe.com/abc" }) };
    }) as unknown as typeof fetch;

    const r = await checkoutSessionErstellen("pro", true, "https://x.ch", { STRIPE_SECRET_KEY: "sk_test_x" }, fakeFetch);
    expect(r).toEqual({ url: "https://checkout.stripe.com/abc" });
    // Jahrespreis von Pro (149000 Rappen? -> preisJahr*100) und Intervall year.
    const pro = PAKETE.find((p) => p.id === "pro")!;
    expect(gesendet).toContain(`unit_amount%5D=${pro.preisJahr * 100}`);
    expect(gesendet).toContain("interval%5D=year");
    expect(gesendet).toContain(`planId%5D=${pro.planId}`);
  });
});
