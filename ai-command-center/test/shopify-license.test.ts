/**
 * Unit-Tests für die Shopify-Lizenz-Auslieferung (lib/shopify-license.ts):
 * Titel -> Bezahl-Stufe und Bestellung -> gültige Lizenzschlüssel.
 */
process.env.LICENSE_SECRET = "test-secret-fuer-unit-tests-nur-lokal";

import { describe, expect, it } from "vitest";
import { planFromTitle, licensesForOrder } from "../lib/shopify-license";
import { verifyLicenseKey } from "../lib/license";

describe("planFromTitle", () => {
  it("erkennt jede Bezahl-Stufe aus einem Produkttitel", () => {
    expect(planFromTitle("PERSONAL AI – Ihr persönlicher KI-Assistent (Monatsabo)")).toBe("PERSONAL");
    expect(planFromTitle("STARTER AI – Ihre KI-Abteilung")).toBe("STARTER");
    expect(planFromTitle("PROFESSIONAL AI – die komplette KI-Arbeitsumgebung")).toBe("PROFESSIONAL");
    expect(planFromTitle("BUSINESS AI – die digitale KI-Abteilung")).toBe("BUSINESS");
    expect(planFromTitle("ENTERPRISE AI – individuelle KI-Infrastruktur")).toBe("ENTERPRISE");
  });
  it("unterscheidet PROFESSIONAL und PERSONAL sauber (Wortgrenze)", () => {
    expect(planFromTitle("PROFESSIONAL AI")).toBe("PROFESSIONAL");
    expect(planFromTitle("PERSONAL AI")).toBe("PERSONAL");
  });
  it("liefert null für FREE, Ultra-Zusatz, Unbekanntes und leere Eingabe", () => {
    expect(planFromTitle("FREE Demo – KI-Team kostenlos testen")).toBeNull();
    expect(planFromTitle("ULTRA-Levelup für PERSONAL")).toBeNull(); // Ultra hat Vorrang -> kein Schlüssel
    expect(planFromTitle("Setup-Service")).toBeNull();
    expect(planFromTitle("")).toBeNull();
    expect(planFromTitle(null)).toBeNull();
    expect(planFromTitle(undefined)).toBeNull();
  });
});

describe("licensesForOrder", () => {
  it("erzeugt je Bezahl-Position gültige Schlüssel und berücksichtigt die Menge", () => {
    const lizenzen = licensesForOrder([
      { title: "STARTER AI", quantity: 2 },
      { title: "BUSINESS AI", quantity: 1 },
      { title: "FREE Demo", quantity: 5 }, // erzeugt keinen Schlüssel
      { title: "ULTRA-Levelup", quantity: 1 }, // erzeugt keinen Schlüssel
    ]);
    expect(lizenzen).toHaveLength(3); // 2x STARTER + 1x BUSINESS
    expect(lizenzen.filter((l) => l.plan === "STARTER")).toHaveLength(2);
    expect(lizenzen.filter((l) => l.plan === "BUSINESS")).toHaveLength(1);
    // Jeder ausgelieferte Schlüssel ist echt gültig und passt zur Stufe.
    for (const l of lizenzen) {
      expect(verifyLicenseKey(l.key)).toEqual({ valid: true, plan: l.plan });
    }
  });
  it("begrenzt die Menge (min 1, max 50) und ignoriert leere Bestellungen", () => {
    expect(licensesForOrder([{ title: "PERSONAL AI", quantity: 0 }])).toHaveLength(1);
    expect(licensesForOrder([{ title: "PERSONAL AI", quantity: 999 }])).toHaveLength(50);
    expect(licensesForOrder([])).toHaveLength(0);
  });
});
