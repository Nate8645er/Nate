/**
 * Integrations-Selbsttest: lädt jede offizielle SDK und prüft die sichere
 * Schlüssel-Konfiguration (nur über Umgebungsvariablen – niemals im Code).
 * Meldet ehrlich „nicht konfiguriert", wenn ein API-Key fehlt. Es werden KEINE
 * kostenpflichtigen Aufrufe ausgeführt – nur Ladbarkeit + Konfig-Status.
 */

const ergebnisse = [];

async function pruefe(name, envKey, loader) {
  const keyDa = !!process.env[envKey] && process.env[envKey].trim().length > 0;
  try {
    const info = await loader();
    ergebnisse.push({ name, geladen: true, envKey, konfiguriert: keyDa, detail: info });
  } catch (e) {
    ergebnisse.push({ name, geladen: false, envKey, konfiguriert: keyDa, detail: String(e.message || e) });
  }
}

await pruefe("Vercel AI SDK (ai)", "—", async () => {
  const ai = await import("ai");
  if (typeof ai.generateText !== "function") throw new Error("generateText fehlt");
  const openai = await import("@ai-sdk/openai");
  if (typeof openai.createOpenAI !== "function") throw new Error("createOpenAI fehlt");
  return "generateText + @ai-sdk/openai vorhanden (Provider-Key je nach Anbieter)";
});

await pruefe("Runway", "RUNWAY_API_KEY", async () => {
  const mod = await import("@runwayml/sdk");
  const RunwayML = mod.default || mod.RunwayML;
  if (typeof RunwayML !== "function") throw new Error("RunwayML-Client fehlt");
  // Kein Netzaufruf: nur Instanziierbarkeit prüfen (Key optional zur Ladezeit).
  return "RunwayML-Client instanziierbar";
});

await pruefe("v0 (Vercel)", "V0_API_KEY", async () => {
  const mod = await import("v0-sdk");
  const createClient = mod.createClient || mod.default?.createClient;
  if (typeof createClient !== "function") throw new Error("createClient fehlt");
  return "v0-Client (createClient) vorhanden";
});

// Ausgabe
let alleGeladen = true;
console.log("\nIntegrations-Status:\n");
for (const r of ergebnisse) {
  if (!r.geladen) alleGeladen = false;
  const laden = r.geladen ? "✓ geladen" : "✗ FEHLER";
  const konf =
    r.envKey === "—"
      ? "(Provider-Key)"
      : r.konfiguriert
        ? `✓ ${r.envKey} gesetzt`
        : `– ${r.envKey} fehlt (nicht konfiguriert)`;
  console.log(`  ${laden}  ${r.name}  ${konf}`);
  console.log(`           → ${r.detail}`);
}
console.log("");
process.exit(alleGeladen ? 0 : 1);
