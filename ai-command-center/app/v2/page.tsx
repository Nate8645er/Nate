import { Badge, Button, StatTile, Surface } from "./ui/primitives";
import { fetchCompute, formatMemoryGb, primaryDevice } from "@/lib/platform-backend";

/**
 * Premium-Dashboard (Phase 7, Vorschau). Token-basiert, responsiv, klare
 * Hierarchie. Live-Kennzahlen (CPU/RAM/GPU) kommen ECHT vom platform-backend,
 * sobald `PLATFORM_BACKEND_URL` gesetzt und der Dienst erreichbar ist; sonst
 * ehrlich „—" („Backend nicht verbunden") — kein erfundener Status.
 */

const AGENTEN = [
  { name: "Kundensupport", rolle: "Support", status: "aktiv", tone: "success" as const },
  { name: "Recherche", rolle: "Research", status: "aktiv", tone: "success" as const },
  { name: "Dokumente", rolle: "Ingest", status: "wartet auf Freigabe", tone: "warning" as const },
];

export default async function V2Dashboard() {
  // Echte Hardware-Daten vom Backend (oder null, wenn nicht verbunden).
  const compute = await fetchCompute();
  const dev = primaryDevice(compute);
  const cpuDev = compute?.devices.find((d) => d.vendor === "cpu") ?? null;

  const ramValue = cpuDev ? formatMemoryGb(cpuDev.memory_total_mb) : "—";
  const ramHint = cpuDev ? `${cpuDev.arch ?? cpuDev.name}` : "Backend nicht verbunden";
  const cpuValue = cpuDev ? cpuDev.name : "—";
  const cpuHint = cpuDev ? cpuDev.backends.join(" · ") : "Backend nicht verbunden";
  const gpuValue = compute ? (compute.gpu_available && dev && dev.vendor !== "cpu" ? dev.name : "keine") : "—";
  const gpuHint = compute
    ? compute.gpu_available && dev && dev.vendor !== "cpu"
      ? `${formatMemoryGb(dev.memory_total_mb)} · ${dev.memory_model}`
      : "nur CPU erkannt"
    : "Backend nicht verbunden";

  return <V2DashboardView cpuValue={cpuValue} cpuHint={cpuHint} ramValue={ramValue} ramHint={ramHint} gpuValue={gpuValue} gpuHint={gpuHint} />;
}

function V2DashboardView({
  cpuValue,
  cpuHint,
  ramValue,
  ramHint,
  gpuValue,
  gpuHint,
}: {
  cpuValue: string;
  cpuHint: string;
  ramValue: string;
  ramHint: string;
  gpuValue: string;
  gpuHint: string;
}) {
  return (
    <main style={{ maxWidth: 1160, margin: "0 auto", padding: "var(--space-6) var(--space-5)" }}>
      {/* Kopf */}
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-4)", flexWrap: "wrap" }}>
        <div>
          <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.2em" }}>
            AI Command Center
          </div>
          <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 800, lineHeight: "var(--leading-tight)", margin: "var(--space-2) 0 0" }}>
            Kommandozentrale
          </h1>
        </div>
        <div style={{ display: "flex", gap: "var(--space-2)" }}>
          <Button variant="ghost">Einstellungen</Button>
          <Button>Neue Mission</Button>
        </div>
      </header>

      {/* Live-Kennzahlen */}
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
          gap: "var(--space-3)",
          marginTop: "var(--space-6)",
        }}
      >
        <StatTile label="Agenten aktiv" value="2 / 3" hint="1 wartet auf Freigabe" />
        <StatTile label="CPU" value={cpuValue} hint={cpuHint} />
        <StatTile label="RAM" value={ramValue} hint={ramHint} />
        <StatTile label="GPU" value={gpuValue} hint={gpuHint} />
        <StatTile label="Token heute" value="—" hint="Kontingent aktiv" />
      </section>

      {/* Auftrag + Agentenliste */}
      <section style={{ display: "grid", gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1fr)", gap: "var(--space-4)", marginTop: "var(--space-5)" }}>
        <Surface elevated>
          <h2 style={{ fontSize: "var(--text-lg)", fontWeight: 800, margin: 0 }}>Was soll erledigt werden?</h2>
          <p style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)", marginTop: "var(--space-2)" }}>
            Auftrag beschreiben — Commander plant, Spezialisten arbeiten, Qualität prüft.
          </p>
          <div
            style={{
              marginTop: "var(--space-4)",
              minHeight: 120,
              borderRadius: "var(--radius-md)",
              border: "1px solid var(--border)",
              background: "var(--surface-2)",
              padding: "var(--space-4)",
              color: "var(--text-muted)",
              fontSize: "var(--text-sm)",
            }}
          >
            z. B. „Erstelle eine Offerte für eine Badezimmer-Renovation …"
          </div>
          <div style={{ marginTop: "var(--space-4)", display: "flex", gap: "var(--space-2)" }}>
            <Button variant="ghost">Datei anhängen</Button>
            <Button type="submit">Mission starten</Button>
          </div>
        </Surface>

        <Surface>
          <h2 style={{ fontSize: "var(--text-md)", fontWeight: 800, margin: 0 }}>Ihre Agenten</h2>
          <ul style={{ listStyle: "none", padding: 0, margin: "var(--space-4) 0 0", display: "flex", flexDirection: "column", gap: "var(--space-3)" }}>
            {AGENTEN.map((a) => (
              <li key={a.name} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "var(--space-2)" }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{a.name}</div>
                  <div style={{ fontSize: "var(--text-xs)", color: "var(--text-muted)" }}>{a.rolle}</div>
                </div>
                <Badge tone={a.tone}>{a.status}</Badge>
              </li>
            ))}
          </ul>
        </Surface>
      </section>
    </main>
  );
}
