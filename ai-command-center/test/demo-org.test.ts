/**
 * Sichert, dass der Demo-Org-Plan gross genug ist, damit sich die Org-Pläne
 * BUSINESS (max 12) und ENTERPRISE (max 24) auch im Demo-Modus unterscheiden.
 */
import { describe, expect, it } from "vitest";
import { demoOrgPlan } from "../lib/agents/demo";
import { MAX_DYN_AGENTS } from "../lib/agents/team";

describe("demoOrgPlan (Demo-Firma)", () => {
  const plan = demoOrgPlan("eine Bäckerei digitalisieren");
  const rollen = plan.departments.flatMap((d) => d.roles);

  it("liefert genug Rollen, um ENTERPRISE auszuschöpfen", () => {
    expect(rollen.length).toBeGreaterThanOrEqual(MAX_DYN_AGENTS.ENTERPRISE);
  });
  it("hat mehr Rollen als das BUSINESS-Limit (Differenzierung möglich)", () => {
    expect(rollen.length).toBeGreaterThan(MAX_DYN_AGENTS.BUSINESS);
    expect(MAX_DYN_AGENTS.ENTERPRISE).toBeGreaterThan(MAX_DYN_AGENTS.BUSINESS);
  });
  it("jede Rolle hat rolle, fachgebiet und eine konkrete Teilaufgabe", () => {
    for (const r of rollen) {
      expect(r.rolle).toBeTruthy();
      expect(r.fachgebiet).toBeTruthy();
      expect(r.teilaufgabe).toContain("Bäckerei");
    }
  });
});
