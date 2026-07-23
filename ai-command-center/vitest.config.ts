import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Node-Umgebung: die getestete Logik nutzt node:crypto (HMAC), kein DOM nötig.
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
  },
  // Pfad-Alias wie in tsconfig ("@/*" -> Projektwurzel), damit Tests Module
  // importieren können, die intern "@/..." nutzen (z. B. der Orchestrator).
  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },
});
