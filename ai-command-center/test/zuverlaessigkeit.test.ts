/**
 * Tests der Zuverlässigkeits-Schicht: JSON-Reparatur, Backoff, Retry, sichereZahl.
 */
import { describe, expect, it } from "vitest";
import {
  jsonReparieren,
  sichereZahl,
  backoffPlan,
  mitWiederholung,
} from "../lib/agents/zuverlaessigkeit";

describe("jsonReparieren", () => {
  it("liest sauberes JSON", () => {
    expect(jsonReparieren('{"a":1}')).toEqual({ a: 1 });
  });
  it("entfernt ```json-Zäune und umgebende Prosa", () => {
    const s = 'Hier ist der Plan:\n```json\n{"commander":"tue X"}\n```\nViel Erfolg!';
    expect(jsonReparieren(s)).toEqual({ commander: "tue X" });
  });
  it("schneidet die erste balancierte Struktur heraus", () => {
    expect(jsonReparieren('Text {"x":[1,2,3]} Rest {"y":9}')).toEqual({ x: [1, 2, 3] });
  });
  it("repariert abschliessende Kommas", () => {
    expect(jsonReparieren('{"a":1,"b":[1,2,],}')).toEqual({ a: 1, b: [1, 2] });
  });
  it("normalisiert typografische Anführungszeichen", () => {
    expect(jsonReparieren("{\u201Ca\u201D:\u201Cwert\u201D}")).toEqual({ a: "wert" });
  });
  it("respektiert Klammern innerhalb von Strings", () => {
    expect(jsonReparieren('{"t":"a } b ] c"}')).toEqual({ t: "a } b ] c" });
  });
  it("gibt null bei unrettbarem Input", () => {
    expect(jsonReparieren("kein json hier")).toBeNull();
    expect(jsonReparieren("")).toBeNull();
  });
});

describe("sichereZahl", () => {
  it("Zahl bleibt, String wird geparst, Rest → Fallback", () => {
    expect(sichereZahl(42)).toBe(42);
    expect(sichereZahl("1200")).toBe(1200);
    expect(sichereZahl("CHF 1'490", 0)).toBe(1490);
    expect(sichereZahl(undefined, 7)).toBe(7);
    expect(sichereZahl(NaN, 5)).toBe(5);
  });
});

describe("backoffPlan", () => {
  it("exponentiell und gedeckelt", () => {
    expect(backoffPlan(4, 300, 2, 8000)).toEqual([300, 600, 1200, 2400]);
    expect(backoffPlan(6, 300, 2, 1000)).toEqual([300, 600, 1000, 1000, 1000, 1000]);
    expect(backoffPlan(0)).toEqual([]);
  });
});

describe("mitWiederholung", () => {
  it("liefert beim ersten Erfolg sofort", async () => {
    let n = 0;
    const r = await mitWiederholung(async () => { n++; return "ok"; }, { sleep: async () => {} });
    expect(r).toBe("ok");
    expect(n).toBe(1);
  });
  it("wiederholt bei Fehler bis zum Erfolg", async () => {
    let n = 0;
    const r = await mitWiederholung(async () => {
      n++;
      if (n < 3) throw new Error("flüchtig");
      return n;
    }, { versuche: 5, sleep: async () => {} });
    expect(r).toBe(3);
    expect(n).toBe(3);
  });
  it("wirft nach erschöpften Versuchen den letzten Fehler", async () => {
    let n = 0;
    await expect(mitWiederholung(async () => { n++; throw new Error("dauerhaft"); },
      { versuche: 3, sleep: async () => {} })).rejects.toThrow("dauerhaft");
    expect(n).toBe(3);
  });
  it("stoppt sofort, wenn sollWiederholen false liefert", async () => {
    let n = 0;
    await expect(mitWiederholung(async () => { n++; throw new Error("permanent"); },
      { versuche: 5, sollWiederholen: () => false, sleep: async () => {} })).rejects.toThrow("permanent");
    expect(n).toBe(1);
  });
  it("behandelt ungültiges Ergebnis wie einen Fehler (gueltig-Validator)", async () => {
    let n = 0;
    const r = await mitWiederholung(async () => { n++; return n; },
      { versuche: 4, gueltig: (x) => x >= 2, sleep: async () => {} });
    expect(r).toBe(2);
  });
});
