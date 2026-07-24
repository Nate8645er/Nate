import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

function read(rel: string): string {
  return readFileSync(join(root, rel), "utf8");
}

// Hex-Farben (#rgb / #rrggbb). Wir wollen sie NUR in der Token-Datei, nie in
// den Komponenten — so bleibt das Designsystem die einzige Quelle.
const HEX = /#[0-9a-fA-F]{3,8}\b/;

describe("v2 Design-System: keine Hex-Werte in Komponenten", () => {
  it("primitives.tsx nutzt nur Tokens (var(--…)), kein Hex", () => {
    const src = read("app/v2/ui/primitives.tsx");
    expect(HEX.test(src)).toBe(false);
    expect(src).toContain("var(--");
  });

  it("page.tsx nutzt nur Tokens, kein Hex", () => {
    const src = read("app/v2/page.tsx");
    expect(HEX.test(src)).toBe(false);
    expect(src).toContain("var(--");
  });

  it("tokens.css definiert die Kern-Variablen", () => {
    const css = read("app/v2/ui-tokens.css");
    for (const token of ["--accent", "--bg", "--surface", "--text", "--radius-lg", "--motion-base"]) {
      expect(css).toContain(token);
    }
  });

  it("tokens.css ist theme-aware (hell/dunkel)", () => {
    const css = read("app/v2/ui-tokens.css");
    expect(css).toContain("prefers-color-scheme: dark");
    expect(css).toContain('[data-theme="dark"]');
    expect(css).toContain("prefers-reduced-motion: reduce");
  });

  it("v2-Layout verlinkt die neuen Seiten (erreichbar)", () => {
    const src = read("app/v2/layout.tsx");
    for (const href of ["/v2", "/v2/mission", "/v2/enterprise"]) {
      expect(src).toContain(href);
    }
  });

  it("enterprise/page.tsx nutzt nur Tokens, kein Hex", () => {
    const src = read("app/v2/enterprise/page.tsx");
    expect(HEX.test(src)).toBe(false);
    expect(src).toContain("var(--");
  });
});
