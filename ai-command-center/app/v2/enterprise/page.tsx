import { Badge, Button, Surface } from "../ui/primitives";

/**
 * Enterprise-Landing-Section (v2, Vorschau) — verkauft die On-Premise/Private-
 * KI anhand der 5 real getesteten Beweispunkte. Token-only, theme-aware.
 * Additiv; ändert die bestehende /preise-Seite nicht.
 */

const BEWEISE = [
  {
    titel: "Ihre Daten verlassen das Haus nicht",
    text: "Datenklasse «nur lokal» bindet die Verarbeitung hart an Ihre Infrastruktur — kein Dokument geht in eine fremde Cloud.",
    marke: "local_only-Routing",
  },
  {
    titel: "Kunde A sieht nie Daten von Kunde B",
    text: "Mandantentrennung auf Datenbank-Ebene (Postgres Row-Level-Security) — selbst bei einem Code-Fehler liefert die DB keine fremden Zeilen.",
    marke: "RLS · DB-Ebene",
  },
  {
    titel: "Echte KI im eigenen Rechenzentrum",
    text: "Eigene, lokale Modelle (Ollama/vLLM) über einen Modell-Router — Cloud nur, wenn Sie es erlauben. Kein Anbieter-Lock-in.",
    marke: "Lokale Inferenz",
  },
  {
    titel: "Sicherer Zugang, klare Rechte",
    text: "Anbindung an Ihr Firmen-Login (Keycloak/SSO), Rollen mit Default-Deny und ein lückenloses, unveränderliches Audit-Log.",
    marke: "Auth · RBAC · Audit",
  },
  {
    titel: "Betreibbar und nachvollziehbar",
    text: "Metriken (Prometheus), Health-/Readiness-Prüfungen, Backup/Restore und fertige Kubernetes-Manifeste — für den 24/7-Betrieb.",
    marke: "Observability",
  },
];

export default function V2EnterprisePage() {
  return (
    <main style={{ maxWidth: 1080, margin: "0 auto", padding: "var(--space-8) var(--space-5)" }}>
      <div style={{ display: "flex", justifyContent: "center", marginBottom: "var(--space-4)" }}>
        <Badge tone="success">Enterprise · On-Premise</Badge>
      </div>
      <h1 style={{ fontSize: "var(--text-2xl)", fontWeight: 800, lineHeight: "var(--leading-tight)", textAlign: "center", margin: 0 }}>
        Ihre KI-Abteilung — im eigenen Haus.
      </h1>
      <p style={{ color: "var(--text-muted)", fontSize: "var(--text-md)", textAlign: "center", maxWidth: 680, margin: "var(--space-4) auto 0", lineHeight: "var(--leading-normal)" }}>
        Datenhoheit, Mandantentrennung und Nachvollziehbarkeit — ohne dass ein
        einziges Dokument Ihr Netz verlässt. Für Gesundheit, Recht, Finanzen,
        Industrie und die öffentliche Hand.
      </p>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "var(--space-4)",
          marginTop: "var(--space-8)",
        }}
      >
        {BEWEISE.map((b) => (
          <Surface key={b.titel}>
            <Badge tone="muted">{b.marke}</Badge>
            <h2 style={{ fontSize: "var(--text-lg)", fontWeight: 800, margin: "var(--space-3) 0 var(--space-2)" }}>{b.titel}</h2>
            <p style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)", lineHeight: "var(--leading-normal)", margin: 0 }}>{b.text}</p>
          </Surface>
        ))}
      </section>

      <Surface elevated style={{ marginTop: "var(--space-8)", textAlign: "center" }}>
        <h2 style={{ fontSize: "var(--text-xl)", fontWeight: 800, margin: 0 }}>Pilot in Ihrer Abteilung — in Tagen, nicht Monaten</h2>
        <p style={{ color: "var(--text-muted)", fontSize: "var(--text-sm)", maxWidth: 560, margin: "var(--space-3) auto 0" }}>
          Demo mit echten Live-Kennzahlen → Pilot im Kundennetz → stufenweiser,
          jederzeit umkehrbarer Rollout. Installation, Schulung und SLA inklusive.
        </p>
        <div style={{ marginTop: "var(--space-5)", display: "flex", gap: "var(--space-2)", justifyContent: "center", flexWrap: "wrap" }}>
          <Button>Kontakt aufnehmen</Button>
          <Button variant="ghost">Demo ansehen</Button>
        </div>
      </Surface>

      <p style={{ color: "var(--text-muted)", fontSize: "var(--text-xs)", textAlign: "center", marginTop: "var(--space-5)" }}>
        Jedes Leistungsversprechen ist durch ausführbare Tests gedeckt — nicht bloss behauptet.
      </p>
    </main>
  );
}
