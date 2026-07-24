/**
 * Tests des Bildverständnis-Moduls: Konfig-Erkennung, data-URL-Parsing,
 * Request-Aufbau (Anthropic Vision) mit injiziertem fetch, ehrliche Fehlerpfade.
 */
import { describe, expect, it } from "vitest";
import { visionKonfiguriert, bildBeschreiben, dataUrlZerlegen } from "../lib/vision";

const CFG = { ANTHROPIC_API_KEY: "sk-ant-testxxxxxxxx" };
const B64 = "iVBORw0KGgoAAAANSUhEUg=="; // Dummy

describe("visionKonfiguriert", () => {
  it("nur mit gültigem sk-ant-Key", () => {
    expect(visionKonfiguriert({})).toBe(false);
    expect(visionKonfiguriert({ ANTHROPIC_API_KEY: "pk_x" })).toBe(false);
    expect(visionKonfiguriert(CFG)).toBe(true);
  });
});

describe("dataUrlZerlegen", () => {
  it("zerlegt gültige data-URL", () => {
    expect(dataUrlZerlegen(`data:image/jpeg;base64,${B64}`)).toEqual({ mediaType: "image/jpeg", base64: B64 });
  });
  it("null bei ungültig", () => {
    expect(dataUrlZerlegen("keine-url")).toBeNull();
  });
});

describe("bildBeschreiben", () => {
  it("ohne Key ehrlich nicht-konfiguriert", async () => {
    expect(await bildBeschreiben({ base64: B64, mediaType: "image/jpeg" }, {})).toEqual({ ok: false, error: "nicht-konfiguriert" });
  });
  it("ungültiger Bildtyp => ungueltige-daten", async () => {
    expect(await bildBeschreiben({ base64: B64, mediaType: "image/tiff" }, CFG)).toEqual({ ok: false, error: "ungueltige-daten" });
  });
  it("sendet Bild + Frage an Anthropic und liefert Text", async () => {
    let url = "", body = "";
    const fakeFetch = (async (u: string, init: RequestInit) => {
      url = u; body = String(init.body);
      return { ok: true, json: async () => ({ content: [{ type: "text", text: "Ein Beleg über 42 CHF." }] }) };
    }) as unknown as typeof fetch;
    const r = await bildBeschreiben({ base64: B64, mediaType: "image/jpeg", frage: "Was steht auf dem Beleg?" }, CFG, fakeFetch);
    expect(r).toEqual({ ok: true, text: "Ein Beleg über 42 CHF." });
    expect(url).toBe("https://api.anthropic.com/v1/messages");
    expect(body).toContain('"type":"image"');
    expect(body).toContain("Was steht auf dem Beleg?");
    expect(body).toContain(B64);
  });
  it("API-Fehler => vision-fehler", async () => {
    const fakeFetch = (async () => ({ ok: false, json: async () => ({}) })) as unknown as typeof fetch;
    expect(await bildBeschreiben({ base64: B64, mediaType: "image/png" }, CFG, fakeFetch)).toEqual({ ok: false, error: "vision-fehler" });
  });
});
