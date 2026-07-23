/**
 * Erweiterungen – der Katalog optionaler, selbst gehosteter Module, die das
 * bestehende KI-System ergänzen (Multi-Agent-Engines, Workflows, lokale
 * Modelle, RAG/Vektor, Datei-Extraktion, Sprache, Geräte-/Anlagensteuerung …).
 *
 * Echte Technik, ehrlich dargestellt: Der Grundstatus wird SERVERSEITIG aus den
 * Umgebungsvariablen abgeleitet (grundStatus, rein lesend, kein Netzwerk).
 * Ohne Konfiguration steht ehrlich „nicht verbunden". Keine fremde Software
 * wird geladen oder gestartet – die Dienste hostet der Kunde selbst (Freigabe-
 * Prinzip). Setup-Details siehe INTEGRATIONEN.md.
 */

import type { Metadata } from "next";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import { INTEGRATIONS } from "@/lib/integrations/registry";
import { grundStatus } from "@/lib/integrations/status";
import type { IntegrationKind, IntegrationStatus } from "@/lib/integrations/types";

export const revalidate = 1800;

export const metadata: Metadata = {
  title: "Erweiterungen | AI Command Center",
  description:
    "Optionale, selbst gehostete Module, die das KI-System erweitern – ehrlich mit Verbindungsstatus. Ohne Konfiguration klar „nicht verbunden“.",
};

/** Deutsche Bezeichnung je Kategorie (Anzeige-Reihenfolge der Gruppen). */
const KIND_LABEL: Record<IntegrationKind, string> = {
  "multi-agent": "Multi-Agent-Engines",
  workflow: "Workflow-Automatisierung",
  "local-llm": "Lokale KI-Modelle",
  "computer-use": "Computersteuerung",
  automation: "Geräte- & Anlagensteuerung",
  browser: "Browser-Automatisierung",
  search: "Eigene Suche",
  rag: "Wissenssuche (RAG)",
  vector: "Vektor-Speicher",
  extract: "Datei-Extraktion",
  stt: "Sprache-zu-Text",
  voice: "Sprache & Stimme",
  storage: "Datei-/Objektspeicher",
  "token-opt": "Token-/Kontext-Optimierung",
};

/** Reihenfolge der Gruppen auf der Seite. */
const KIND_ORDER: IntegrationKind[] = [
  "multi-agent",
  "workflow",
  "automation",
  "computer-use",
  "local-llm",
  "search",
  "browser",
  "rag",
  "vector",
  "extract",
  "stt",
  "voice",
  "storage",
  "token-opt",
];

/** Farbe + Text je Status (heller Look, WCAG-tauglich). */
const STATUS_STYLE: Record<IntegrationStatus, { label: string; cls: string; dot: string }> = {
  aktiv: { label: "Verbunden", cls: "bg-[#e7f6ee] text-[#177245]", dot: "bg-[#177245]" },
  konfiguriert: { label: "Konfiguriert", cls: "bg-[#e7f6ee] text-[#177245]", dot: "bg-[#177245]" },
  bereit: { label: "Bereit (integriert)", cls: "bg-[#eef0ff] text-[#5b52d6]", dot: "bg-[#5b52d6]" },
  "nicht-konfiguriert": { label: "Nicht verbunden", cls: "bg-[#fff7ed] text-[#b45309]", dot: "bg-[#b45309]" },
};

/** Ab-Stufe menschenlesbar. */
const STUFE_LABEL: Record<string, string> = {
  FREE: "Gratis",
  PERSONAL: "Personal",
  STARTER: "Starter",
  PROFESSIONAL: "Professional",
  BUSINESS: "Business",
  ENTERPRISE: "Enterprise",
};

export default function ErweiterungenPage() {
  // Status rein serverseitig aus den ENV ableiten (kein Wert verlässt den Server).
  const mitStatus = INTEGRATIONS.map((i) => ({ i, status: grundStatus(i) }));
  const verbunden = mitStatus.filter(
    (x) => x.status === "konfiguriert" || x.status === "aktiv" || x.status === "bereit",
  ).length;

  // Nach Kategorie gruppieren (in definierter Reihenfolge).
  const gruppen = KIND_ORDER.map((kind) => ({
    kind,
    items: mitStatus.filter((x) => x.i.kind === kind),
  })).filter((g) => g.items.length > 0);

  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="erweiterungen" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Erweiterungen</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Das System <span className="acc-grad-text">wächst mit</span> – modular und ehrlich.
          </h1>
          <p className="mt-3 max-w-2xl text-sm text-[#6f6557]">
            Optionale Module ergänzen das bestehende KI-System, ohne es zu ersetzen. Jedes wird
            über eine Umgebungsvariable angebunden und selbst gehostet. Ist nichts hinterlegt,
            steht hier ehrlich „nicht verbunden“ – es wird nie ein Schein-Zustand angezeigt.
            Sicherheitskritische Module (Computersteuerung, Geräte-/Anlagensteuerung) laufen nur
            mit ausdrücklicher Freigabe je Aktion.
          </p>
          <div className="mt-4 inline-flex flex-wrap items-center gap-2 text-sm">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#177245]/30 bg-[#e7f6ee] px-3 py-1 font-semibold text-[#177245]">
              <span className="inline-block h-2 w-2 rounded-full bg-[#177245]" />
              {verbunden}/{INTEGRATIONS.length} verbunden oder bereit
            </span>
            <span className="text-[#6f6557]">Setup je Modul: siehe INTEGRATIONEN.md</span>
          </div>
        </div>

        {gruppen.map(({ kind, items }) => (
          <section key={kind} className="mt-9">
            <h2 className="text-lg font-semibold">{KIND_LABEL[kind]}</h2>
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {items.map(({ i, status }) => {
                const st = STATUS_STYLE[status];
                return (
                  <div key={i.id} className="acc-card acc-card-hover rounded-2xl p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-[#1c1917]">{i.name}</p>
                        <p className="mt-0.5 text-xs text-[#8a8172]">
                          ab {STUFE_LABEL[i.abStufe] ?? i.abStufe}
                          {i.selbstGehostet ? " · selbst gehostet" : " · integriert"}
                        </p>
                      </div>
                      <span className={`shrink-0 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${st.cls}`}>
                        <span className={`inline-block h-1.5 w-1.5 rounded-full ${st.dot}`} />
                        {st.label}
                      </span>
                    </div>
                    <p className="mt-2 text-sm text-[#4a4335]">{i.zweck}</p>
                    {i.hinweis && (
                      <p className="mt-2 rounded-lg border border-[#f0d9a8] bg-[#fdf8ee] px-3 py-2 text-xs text-[#8a6a2f]">
                        ⚠ {i.hinweis}
                      </p>
                    )}
                    <div className="mt-3 flex items-center justify-between gap-2">
                      {i.envKeys.length > 0 ? (
                        <code className="truncate rounded bg-[#f5efe4] px-2 py-0.5 font-mono text-[11px] text-[#6f6557]" title={i.envKeys.join(", ")}>
                          {i.envKeys.join(", ")}
                        </code>
                      ) : (
                        <span className="text-[11px] text-[#8a8172]">kein Setup nötig</span>
                      )}
                      <a
                        href={i.repo}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="shrink-0 text-xs font-semibold text-[#c25e0e] hover:underline"
                      >
                        Quelle ↗
                      </a>
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        ))}

        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
