import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
  {
    // Die neuen, strengeren React-19-/Next-16-Regeln sind fuer dieses Projekt
    // bewusst als Warnung statt Fehler eingestuft:
    // - set-state-in-effect: hier das korrekte SSR-Muster (localStorage/Client-
    //   Only-State ist erst NACH dem Mount lesbar, muss also im Effect gesetzt
    //   werden; ein Umbau auf Initial-State wuerde die Server-Darstellung brechen).
    // - refs/purity: betreffen die Live-HUD-Anzeige im Dashboard (Ref-Werte fuer
    //   Echtzeit-Telemetrie). Als Warnung sichtbar; gezielter Refactor geplant.
    // - no-unescaped-entities: deutsche Typografie (Guillemets, Apostrophe) ist
    //   Absicht und wird nicht escaped.
    rules: {
      "react-hooks/set-state-in-effect": "warn",
      "react-hooks/refs": "warn",
      "react-hooks/purity": "warn",
      "react/no-unescaped-entities": "warn",
    },
  },
]);

export default eslintConfig;
