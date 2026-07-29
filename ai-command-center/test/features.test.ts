import { describe, it, expect } from "vitest";
import {
  hatZugriff,
  minPlanFuer,
  naechsterPlan,
  PLAN_RANG,
  BEREICH_MIN_PLAN,
} from "@/lib/features";

describe("Feature-Matrix je Abo", () => {
  it("FREE hat nur Basis-Bereiche", () => {
    expect(hatZugriff("FREE", "missionen")).toBe(true);
    expect(hatZugriff("FREE", "assistent")).toBe(true);
    expect(hatZugriff("FREE", "skills")).toBe(true);
    expect(hatZugriff("FREE", "freigabe")).toBe(true);
    // gesperrt für FREE:
    expect(hatZugriff("FREE", "email")).toBe(false);
    expect(hatZugriff("FREE", "autopilot")).toBe(false);
    expect(hatZugriff("FREE", "analysen")).toBe(false);
    expect(hatZugriff("FREE", "integrationen")).toBe(false);
    expect(hatZugriff("FREE", "erweiterungen")).toBe(false);
  });

  it("je teurer, desto mehr Zugriff (monoton)", () => {
    const reihe = ["FREE", "PERSONAL", "STARTER", "PROFESSIONAL", "BUSINESS", "ENTERPRISE"] as const;
    for (const bereich of Object.keys(BEREICH_MIN_PLAN) as (keyof typeof BEREICH_MIN_PLAN)[]) {
      let gesehen = false;
      for (const plan of reihe) {
        const zug = hatZugriff(plan, bereich);
        if (gesehen) expect(zug).toBe(true); // einmal frei, bleibt frei
        if (zug) gesehen = true;
      }
    }
  });

  it("Solo schaltet E-Mail frei, aber noch nicht Autopilot", () => {
    expect(hatZugriff("PERSONAL", "email")).toBe(true);
    expect(hatZugriff("PERSONAL", "autopilot")).toBe(false);
  });

  it("Start schaltet Autopilot & Integrationen frei", () => {
    expect(hatZugriff("STARTER", "autopilot")).toBe(true);
    expect(hatZugriff("STARTER", "integrationen")).toBe(true);
    expect(hatZugriff("STARTER", "analysen")).toBe(false);
  });

  it("Pro schaltet Analysen, Erweiterungen & Benutzer frei", () => {
    expect(hatZugriff("PROFESSIONAL", "analysen")).toBe(true);
    expect(hatZugriff("PROFESSIONAL", "erweiterungen")).toBe(true);
    expect(hatZugriff("PROFESSIONAL", "benutzer")).toBe(true);
  });

  it("Enterprise hat überall Zugriff", () => {
    for (const bereich of Object.keys(BEREICH_MIN_PLAN) as (keyof typeof BEREICH_MIN_PLAN)[]) {
      expect(hatZugriff("ENTERPRISE", bereich)).toBe(true);
    }
  });

  it("minPlanFuer & naechsterPlan", () => {
    expect(minPlanFuer("analysen")).toBe("PROFESSIONAL");
    expect(minPlanFuer("missionen")).toBe(null);
    expect(naechsterPlan("FREE")).toBe("PERSONAL");
    expect(naechsterPlan("ENTERPRISE")).toBe(null);
    expect(PLAN_RANG.FREE).toBeLessThan(PLAN_RANG.ENTERPRISE);
  });
});
