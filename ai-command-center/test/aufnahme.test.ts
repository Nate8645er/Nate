/**
 * Tests der Aufnahme-Helfer: MIME-Auswahl, Dauer-Format, Endung.
 */
import { describe, expect, it } from "vitest";
import {
  waehleMimeTyp,
  dauerFormatieren,
  endungFuer,
  VIDEO_MIME_KANDIDATEN,
  AUDIO_MIME_KANDIDATEN,
} from "../lib/aufnahme";

describe("waehleMimeTyp", () => {
  it("nimmt den ersten unterstützten Typ", () => {
    const support = (t: string) => t === "video/webm";
    expect(waehleMimeTyp(VIDEO_MIME_KANDIDATEN, support)).toBe("video/webm");
  });
  it("respektiert die Priorität", () => {
    const support = () => true;
    expect(waehleMimeTyp(AUDIO_MIME_KANDIDATEN, support)).toBe("audio/webm;codecs=opus");
  });
  it("gibt leer zurück, wenn nichts unterstützt", () => {
    expect(waehleMimeTyp(VIDEO_MIME_KANDIDATEN, () => false)).toBe("");
  });
  it("überspringt Prüf-Funktion, die wirft", () => {
    const support = (t: string) => { if (t.includes("vp9")) throw new Error("x"); return t === "video/webm"; };
    expect(waehleMimeTyp(VIDEO_MIME_KANDIDATEN, support)).toBe("video/webm");
  });
});

describe("dauerFormatieren", () => {
  it("formatiert mm:ss", () => {
    expect(dauerFormatieren(0)).toBe("0:00");
    expect(dauerFormatieren(5)).toBe("0:05");
    expect(dauerFormatieren(65)).toBe("1:05");
    expect(dauerFormatieren(-3)).toBe("0:00");
  });
});

describe("endungFuer", () => {
  it("leitet die Endung ab", () => {
    expect(endungFuer("video/webm;codecs=vp9,opus")).toBe("webm");
    expect(endungFuer("video/mp4")).toBe("mp4");
    expect(endungFuer("audio/ogg;codecs=opus")).toBe("ogg");
    expect(endungFuer("audio/webm")).toBe("webm");
  });
});
