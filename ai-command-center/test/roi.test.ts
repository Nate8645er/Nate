/**
 * Tests der ROI-Schätzung: Determinismus, sinnvolle Monotonie, sichere
 * Defaults, offengelegte Annahmen.
 */
import { describe, expect, it } from "vitest";
import { roiSchaetzung, BRANCHEN, TEAMGROESSEN, ABDECKUNG_PRO_PLAN } from "../lib/roi";

describe("roiSchaetzung", () => {
  it("ist deterministisch und liefert positive Werte", () => {
    const a = roiSchaetzung({ branche: "handel", teamgroesse: "klein", plan: "PROFESSIONAL" });
    const b = roiSchaetzung({ branche: "handel", teamgroesse: "klein", plan: "PROFESSIONAL" });
    expect(a).toEqual(b);
    expect(a.stundenProMonat).toBeGreaterThan(0);
    expect(a.chfProMonat).toBeGreaterThan(0);
    expect(a.aufgabenProMonat).toBeGreaterThan(0);
    expect(a.annahmen).toMatch(/Schätzung/);
  });

  it("größeres Team => mehr Ersparnis", () => {
    const solo = roiSchaetzung({ branche: "marketing", teamgroesse: "solo", plan: "BUSINESS" });
    const gross = roiSchaetzung({ branche: "marketing", teamgroesse: "gross", plan: "BUSINESS" });
    expect(gross.chfProMonat).toBeGreaterThan(solo.chfProMonat);
  });

  it("höheres Abo => mehr Abdeckung => mehr Ersparnis", () => {
    const free = roiSchaetzung({ branche: "handel", teamgroesse: "mittel", plan: "FREE" });
    const ent = roiSchaetzung({ branche: "handel", teamgroesse: "mittel", plan: "ENTERPRISE" });
    expect(ent.stundenProMonat).toBeGreaterThan(free.stundenProMonat);
  });

  it("unbekannte IDs fallen auf sichere Defaults (wirft nicht)", () => {
    const r = roiSchaetzung({ branche: "gibtsnicht" as never, teamgroesse: "xxx", plan: "ZZZ" });
    expect(r.chfProMonat).toBeGreaterThan(0);
    // Default-Plan ist PROFESSIONAL.
    expect(r.annahmen).toMatch(/PROFESSIONAL/);
  });

  it("CHF ist auf 10 gerundet", () => {
    for (const b of BRANCHEN) {
      const r = roiSchaetzung({ branche: b.id, teamgroesse: "mittel", plan: "BUSINESS" });
      expect(r.chfProMonat % 10).toBe(0);
    }
  });

  it("Stammdaten sind konsistent", () => {
    expect(new Set(BRANCHEN.map((b) => b.id)).size).toBe(BRANCHEN.length);
    expect(new Set(TEAMGROESSEN.map((t) => t.id)).size).toBe(TEAMGROESSEN.length);
    // Abdeckung steigt monoton mit der Stufe.
    const stufen = ["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"];
    for (let i = 1; i < stufen.length; i++) {
      expect(ABDECKUNG_PRO_PLAN[stufen[i]]).toBeGreaterThan(ABDECKUNG_PRO_PLAN[stufen[i - 1]]);
    }
  });
});
