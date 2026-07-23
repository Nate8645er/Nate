/**
 * Tests der Freigabe/Ausgang-Logik: Id, Status, Umschalten, Filtern, Kennzahlen.
 */
import { describe, expect, it } from "vitest";
import {
  eintragId,
  statusVon,
  umschalten,
  setzeStatus,
  filtere,
  zusammenfassung,
  type ErgebnisEintrag,
  type StatusMap,
} from "../lib/freigabe";

const E: ErgebnisEintrag[] = [
  { goal: "A", final: "Ergebnis A", score: 90, at: "2026-07-23T10:00:00.000Z" },
  { goal: "B", final: "Ergebnis B", score: 80, at: "2026-07-23T11:00:00.000Z" },
  { goal: "C", final: "Ergebnis C", score: null, at: "2026-07-23T12:00:00.000Z" },
];

describe("freigabe", () => {
  it("eintragId nutzt den Zeitstempel, Fallback aufs Ziel", () => {
    expect(eintragId(E[0])).toBe("2026-07-23T10:00:00.000Z");
    expect(eintragId({ goal: "X", final: "", score: null, at: "" })).toMatch(/^goal:X/);
  });

  it("Standardstatus ist offen; Umschalten wechselt", () => {
    let map: StatusMap = {};
    const id = eintragId(E[0]);
    expect(statusVon(map, id)).toBe("offen");
    map = umschalten(map, id);
    expect(statusVon(map, id)).toBe("freigegeben");
    map = umschalten(map, id);
    expect(statusVon(map, id)).toBe("offen");
  });

  it("Umschalten mutiert die alte Map nicht (immutabel)", () => {
    const map: StatusMap = {};
    const neu = umschalten(map, "x");
    expect(map).toEqual({});
    expect(neu.x).toBe("freigegeben");
  });

  it("setzeStatus setzt explizit", () => {
    const map = setzeStatus({}, "id1", "freigegeben");
    expect(statusVon(map, "id1")).toBe("freigegeben");
  });

  it("filtere nach Status", () => {
    const map = setzeStatus({}, eintragId(E[1]), "freigegeben");
    expect(filtere(E, map, "alle")).toHaveLength(3);
    expect(filtere(E, map, "freigegeben").map((e) => e.goal)).toEqual(["B"]);
    expect(filtere(E, map, "offen").map((e) => e.goal)).toEqual(["A", "C"]);
  });

  it("zusammenfassung zählt korrekt", () => {
    const map = setzeStatus(setzeStatus({}, eintragId(E[0]), "freigegeben"), eintragId(E[2]), "freigegeben");
    expect(zusammenfassung(E, map)).toEqual({ gesamt: 3, offen: 1, freigegeben: 2 });
  });
});
