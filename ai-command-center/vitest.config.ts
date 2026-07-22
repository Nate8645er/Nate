import { defineConfig } from "vitest/config";

// Node-Umgebung: die getestete Logik nutzt node:crypto (HMAC), kein DOM nötig.
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
  },
});
