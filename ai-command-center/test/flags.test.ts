import { describe, it, expect } from "vitest";
import { flagFromEnv, flagFromValue } from "@/lib/flags";

describe("Feature-Flags", () => {
  it("ist ohne Env aus (ehrlicher Default)", () => {
    expect(flagFromEnv("ui_v2", {})).toBe(false);
  });

  it("erkennt wahre Werte", () => {
    for (const v of ["1", "true", "on", "YES", " True "]) {
      expect(flagFromValue(v)).toBe(true);
    }
  });

  it("erkennt falsche/leere Werte", () => {
    for (const v of ["0", "false", "off", "", null, undefined, "nope"]) {
      expect(flagFromValue(v as string)).toBe(false);
    }
  });

  it("liest die richtige Env-Variable", () => {
    expect(flagFromEnv("ui_v2", { NEXT_PUBLIC_UI_V2: "1" })).toBe(true);
    expect(flagFromEnv("ui_v2", { NEXT_PUBLIC_UI_V2: "0" })).toBe(false);
  });
});
