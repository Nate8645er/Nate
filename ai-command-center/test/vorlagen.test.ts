/**
 * Tests der Ein-Klick-Vorlagen: Konsistenz, branchengerechte Sortierung, Limit.
 */
import { describe, expect, it } from "vitest";
import { VORLAGEN, vorlagenFuer } from "../lib/vorlagen";

describe("Vorlagen", () => {
  it("Stammdaten sind konsistent und vollständig", () => {
    const ids = VORLAGEN.map((v) => v.id);
    expect(new Set(ids).size).toBe(ids.length);
    for (const v of VORLAGEN) {
      expect(v.titel.length).toBeGreaterThan(2);
      expect(v.kurz.length).toBeGreaterThan(5);
      expect(v.prompt.length).toBeGreaterThan(30);
      expect(v.icon).toBeTruthy();
    }
    // Es gibt allgemeine Vorlagen, die überall passen.
    expect(VORLAGEN.some((v) => v.branche === "alle")).toBe(true);
  });

  it("sortiert passende Branche nach vorne, dann allgemeine", () => {
    const liste = vorlagenFuer("handel");
    // Erste Einträge sollten Handel ODER allgemein sein, nie eine Fremdbranche vor Handel.
    const ersteHandelIdx = liste.findIndex((v) => v.branche === "handel");
    const ersteFremdIdx = liste.findIndex((v) => v.branche !== "handel" && v.branche !== "alle");
    expect(ersteHandelIdx).toBeGreaterThanOrEqual(0);
    expect(ersteHandelIdx).toBeLessThan(ersteFremdIdx);
  });

  it("ohne Branche kommen die allgemeinen zuerst", () => {
    const liste = vorlagenFuer(null);
    expect(liste[0].branche).toBe("alle");
  });

  it("respektiert das Limit und enthält keine Duplikate", () => {
    const liste = vorlagenFuer("marketing", 6);
    expect(liste.length).toBe(6);
    expect(new Set(liste.map((v) => v.id)).size).toBe(6);
  });

  it("gibt immer alle Vorlagen zurück (nichts geht verloren)", () => {
    expect(vorlagenFuer("gastro").length).toBe(VORLAGEN.length);
    expect(vorlagenFuer(null).length).toBe(VORLAGEN.length);
  });
});
