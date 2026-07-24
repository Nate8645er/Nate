import { describe, it, expect } from "vitest";
import {
  alsMap,
  istProvider,
  kundenSchluesselAusHeaders,
  PROVIDER_LABEL,
  PROVIDER_LISTE,
  schluesselPlausibel,
} from "@/lib/agents/kundenschluessel";

function headerGetter(map: Record<string, string>) {
  return (n: string) => map[n.toLowerCase()] ?? null;
}

describe("Bring-your-own-key: Kundenschlüssel", () => {
  it("istProvider akzeptiert nur bekannte Provider", () => {
    expect(istProvider("anthropic")).toBe(true);
    expect(istProvider("openai")).toBe(true);
    expect(istProvider("gibtsnicht")).toBe(false);
    expect(istProvider(123)).toBe(false);
    expect(istProvider(null)).toBe(false);
  });

  it("jeder Provider hat ein Label", () => {
    for (const p of PROVIDER_LISTE) expect(PROVIDER_LABEL[p]).toBeTruthy();
  });

  it("schluesselPlausibel: Länge/Whitespace geprüft, kein Provider-Präfix erzwungen", () => {
    expect(schluesselPlausibel("sk-ant-abcdefghij12345")).toBe(true);
    expect(schluesselPlausibel("kurz")).toBe(false); // < 12
    expect(schluesselPlausibel("hat leerzeichen drin drin")).toBe(false);
    expect(schluesselPlausibel("mit\nzeilenumbruch1234")).toBe(false);
    expect(schluesselPlausibel(12345)).toBe(false);
    expect(schluesselPlausibel("x".repeat(401))).toBe(false); // zu lang
  });

  it("kundenSchluesselAusHeaders: gültig → {provider,key}", () => {
    const r = kundenSchluesselAusHeaders(headerGetter({
      "x-acc-llm-provider": "anthropic",
      "x-acc-llm-key": "  sk-ant-abcdefghij12345  ",
    }));
    expect(r).toEqual({ provider: "anthropic", key: "sk-ant-abcdefghij12345" });
  });

  it("kundenSchluesselAusHeaders: fehlend/ungültig → null (Fallback greift)", () => {
    expect(kundenSchluesselAusHeaders(headerGetter({}))).toBeNull();
    expect(kundenSchluesselAusHeaders(headerGetter({ "x-acc-llm-provider": "anthropic" }))).toBeNull();
    expect(kundenSchluesselAusHeaders(headerGetter({
      "x-acc-llm-provider": "boese", "x-acc-llm-key": "sk-ant-abcdefghij12345",
    }))).toBeNull();
    expect(kundenSchluesselAusHeaders(headerGetter({
      "x-acc-llm-provider": "openai", "x-acc-llm-key": "kurz",
    }))).toBeNull();
  });

  it("alsMap: baut Provider→Key-Map bzw. leeres Objekt", () => {
    expect(alsMap({ provider: "openai", key: "sk-openai-1234567890" })).toEqual({ openai: "sk-openai-1234567890" });
    expect(alsMap(null)).toEqual({});
  });
});
