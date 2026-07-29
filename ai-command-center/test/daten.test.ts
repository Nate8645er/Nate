/**
 * Daten-Integritäts-Tests: prüfen die statischen Kataloge (Connectors, Skills,
 * Onboarding-Tutorials) auf konsistente, vollständige Einträge – fängt
 * Tippfehler/Lücken beim Pflegen der Daten früh ab.
 */
import { describe, expect, it } from "vitest";
import {
  CONNECTORS,
  KATEGORIEN,
  KATEGORIE_AKZENT,
  STATUS_LABEL,
  connectorsByKategorie,
} from "../lib/connectors";
import {
  SKILLS,
  SKILL_ANZAHL,
  SKILL_KATEGORIEN,
  SKILL_AB_STUFE,
  STUFEN_REIHENFOLGE,
  skillVerfuegbar,
  skillAnzahlFuer,
  skillSuche,
} from "../lib/skills";
import { TUTORIALS, tutorialFuer } from "../lib/onboarding";

describe("Connectors-Katalog", () => {
  it("jeder Connector hat vollständige, gültige Felder", () => {
    for (const c of CONNECTORS) {
      expect(c.id).toBeTruthy();
      expect(c.name).toBeTruthy();
      expect(c.monogramm.length).toBeGreaterThanOrEqual(1);
      expect(KATEGORIEN).toContain(c.kategorie);
      expect(c.beschreibung.length).toBeGreaterThan(5);
      expect(Object.keys(STATUS_LABEL)).toContain(c.status);
      expect(["BUSINESS", "ENTERPRISE"]).toContain(c.planStufe);
    }
  });
  it("hat eindeutige IDs", () => {
    const ids = CONNECTORS.map((c) => c.id);
    expect(new Set(ids).size).toBe(ids.length);
  });
  it("jede Kategorie hat eine Akzentfarbe und connectorsByKategorie filtert korrekt", () => {
    for (const k of KATEGORIEN) {
      expect(KATEGORIE_AKZENT[k]).toMatch(/^#[0-9a-fA-F]{6}$/);
      const gefiltert = connectorsByKategorie(k);
      expect(gefiltert.every((c) => c.kategorie === k)).toBe(true);
      expect(gefiltert.length).toBe(CONNECTORS.filter((c) => c.kategorie === k).length);
    }
  });
});

describe("Skills-Katalog", () => {
  it("Befehle sind eindeutig und beginnen mit /", () => {
    const befehle = SKILLS.map((s) => s.befehl);
    expect(new Set(befehle).size).toBe(befehle.length);
    for (const b of befehle) expect(b.startsWith("/")).toBe(true);
    expect(SKILL_ANZAHL).toBe(SKILLS.length);
  });
  it("jede Kategorie/Ab-Stufe verweist auf reale Skills", () => {
    for (const s of SKILLS) expect(SKILL_KATEGORIEN).toContain(s.kategorie);
    const befehle = new Set(SKILLS.map((s) => s.befehl));
    for (const b of Object.keys(SKILL_AB_STUFE)) expect(befehle.has(b)).toBe(true);
  });
  it("skillVerfuegbar respektiert die Stufen-Hierarchie", () => {
    const freierSkill = SKILLS.find((s) => (SKILL_AB_STUFE[s.befehl] ?? "FREE") === "FREE");
    expect(freierSkill && skillVerfuegbar(freierSkill.befehl, "FREE")).toBe(true);
    const hoherSkill = SKILLS.find((s) => SKILL_AB_STUFE[s.befehl] === "ENTERPRISE");
    if (hoherSkill) {
      expect(skillVerfuegbar(hoherSkill.befehl, "FREE")).toBe(false);
      expect(skillVerfuegbar(hoherSkill.befehl, "ENTERPRISE")).toBe(true);
    }
  });
  it("skillAnzahlFuer wächst monoton und ENTERPRISE enthält alle", () => {
    const zahlen = STUFEN_REIHENFOLGE.map((st) => skillAnzahlFuer(st));
    for (let i = 1; i < zahlen.length; i++) expect(zahlen[i]).toBeGreaterThanOrEqual(zahlen[i - 1]);
    expect(skillAnzahlFuer("ENTERPRISE")).toBe(SKILLS.length);
  });
  it("skillSuche braucht / und findet per Befehls-Präfix (max 8)", () => {
    expect(skillSuche("website")).toEqual([]); // ohne / kein Ergebnis
    const treffer = skillSuche(SKILLS[0].befehl);
    expect(treffer.length).toBeGreaterThan(0);
    expect(treffer.length).toBeLessThanOrEqual(8);
  });
});

describe("Onboarding-Tutorials", () => {
  it("jedes Tutorial hat konsistente Schritte und Inhalte", () => {
    for (const t of TUTORIALS) {
      expect(t.name).toBeTruthy();
      expect(t.enthalten.length).toBeGreaterThan(0);
      expect(t.schritte.length).toBeGreaterThan(0);
      const ids = t.schritte.map((s) => s.id);
      expect(new Set(ids).size).toBe(ids.length); // Schritt-IDs eindeutig
      for (const s of t.schritte) {
        expect(s.titel).toBeTruthy();
        expect(s.text.length).toBeGreaterThan(5);
      }
    }
  });
  it("tutorialFuer liefert den passenden Tarif (Fallback Starter)", () => {
    expect(tutorialFuer("BUSINESS").plan).toBe("BUSINESS");
    expect(tutorialFuer("FREE").plan).toBe("FREE");
    // @ts-expect-error – unbekannte Stufe fällt auf Starter zurück
    expect(tutorialFuer("UNBEKANNT").plan).toBe("STARTER");
  });
});
