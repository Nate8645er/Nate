"use client";

/**
 * Integration-Center — Anbindungs-Katalog für Firmensysteme (heller acc-Look).
 *
 * Rein statischer Katalog aus lib/connectors.ts: Kategorie-Gruppen mit
 * Connector-Karten (Monogramm-Badge statt Markenlogo, Plan- und
 * Status-Badge). "Anbindung anfragen" öffnet ein Modal, das den
 * ehrlichen 3-Schritte-Ablauf erklärt und per mailto eine Anfrage mit
 * vorbefülltem Betreff startet. Keine Live-Verbindungen auf dieser Seite —
 * die werden pro Unternehmen als Enterprise-Projekt eingerichtet.
 */

import Link from "next/link";
import { memo, useEffect, useRef, useState } from "react";
import OnboardingWizard from "./OnboardingWizard";
import {
  CONNECTORS,
  KATEGORIEN,
  STATUS_LABEL,
  type Connector,
  type ConnectorKategorie,
} from "@/lib/connectors";

/** Ziel-Adresse für Anbindungs-Anfragen. */
const KONTAKT_EMAIL = "beamswiss@gmail.com";

/** Fokus-Ring für Tastaturbedienung (focus-visible), heller Look. */
const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ff8c2a]/60";

/**
 * Heller, WCAG-tauglicher Akzent je Kategorie (dezenter Farbakzent pro Dienst).
 * Ersetzt die für den dunklen HUD gedachten warmen Nuancen aus connectors.ts.
 */
const KATEGORIE_FARBE: Record<ConnectorKategorie, string> = {
  Produktivität: "#c25e0e",
  "CRM + Vertrieb": "#5b52d6",
  "ERP + Finanzen": "#0f766e",
  Kommunikation: "#be185d",
  "Cloud + Dateien": "#1d63c9",
  "E-Commerce": "#9a6b0f",
  "Eigene Systeme": "#7c3aed",
};

/** Kleines Akzent-Eyebrow (Label über einem Block). */
const EYEBROW = "text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]";

/** mailto-Link mit vorbefülltem Betreff "Anbindung <Name>". */
function mailtoHref(connectorName: string): string {
  const subject = encodeURIComponent(`Anbindung ${connectorName}`);
  const body = encodeURIComponent(
    `Guten Tag\n\nWir möchten die Anbindung "${connectorName}" für unser Unternehmen anfragen.\n\nFirma:\nAnsprechperson:\nAktueller Plan (BUSINESS/ENTERPRISE):\n\nFreundliche Grüsse`,
  );
  return `mailto:${KONTAKT_EMAIL}?subject=${subject}&body=${body}`;
}

/** Monogramm-Badge (2 Buchstaben) — bewusst kein Markenlogo. */
const MonogrammBadge = memo(function MonogrammBadge({
  monogramm,
  akzent,
}: {
  monogramm: string;
  akzent: string;
}) {
  return (
    <span
      aria-hidden
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border font-mono text-sm font-bold tracking-[0.08em]"
      style={{
        color: akzent,
        borderColor: `${akzent}33`,
        background: `${akzent}12`,
      }}
    >
      {monogramm}
    </span>
  );
});

/** Plan-Badge: ab welcher Stufe die Anbindung angefragt werden kann. */
const PlanBadge = memo(function PlanBadge({ planStufe }: { planStufe: Connector["planStufe"] }) {
  const enterprise = planStufe === "ENTERPRISE";
  return (
    <span
      className={`rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] ${
        enterprise
          ? "border-[#f0c674] bg-[#fdf6e3] text-[#9a6b0f]"
          : "border-[#ffb066]/50 bg-[#fff4e6] text-[#c25e0e]"
      }`}
    >
      ab {planStufe}
    </span>
  );
});

/** Status-Badge: Verfügbar auf Anfrage (grün) / In Entwicklung (gelb). */
const StatusBadge = memo(function StatusBadge({ status }: { status: Connector["status"] }) {
  const available = status === "verfügbar-auf-anfrage";
  return (
    <span
      className={`flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] ${
        available
          ? "border-[#a7d8bd] bg-[#e7f6ee] text-[#177245]"
          : "border-[#f0d68a] bg-[#fdf6e3] text-[#8a6d1f]"
      }`}
    >
      <span
        aria-hidden
        className={`h-1.5 w-1.5 rounded-full ${available ? "animate-pulse bg-[#22a06b]" : "bg-[#d9a91e]"}`}
      />
      {STATUS_LABEL[status]}
    </span>
  );
});

/**
 * Modal-Shell (Spiegel des Dashboard-Modals): role=dialog, Escape und
 * Klick auf den Hintergrund schliessen, Fokus springt hinein und zurück.
 */
function HudModal({
  labelId,
  onClose,
  children,
}: {
  labelId: string;
  onClose: () => void;
  children: React.ReactNode;
}) {
  const dialogRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const previous = document.activeElement;
    dialogRef.current?.focus();
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      if (previous instanceof HTMLElement) previous.focus();
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-[#1c1917]/40 p-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        tabIndex={-1}
        className="acc-card acc-in relative w-full max-w-lg rounded-2xl border border-[#e8e1d2] bg-white p-6 outline-none"
      >
        <button
          onClick={onClose}
          aria-label="Schliessen"
          className={`absolute right-3 top-3 rounded-xl px-2 py-1 font-mono text-xs text-[#8d8172] transition hover:text-[#1c1917] ${FOCUS_RING}`}
        >
          ✕
        </button>
        {children}
      </div>
    </div>
  );
}

/** Die 3 ehrlichen Schritte einer Live-Anbindung. */
const ABLAUF_SCHRITTE: readonly { titel: string; text: string }[] = [
  {
    titel: "Zugriff freigeben",
    text: "Sie geben der KI in IHREM System per OAuth oder API-Schlüssel Zugriff frei — ohne diese Freigabe kommt niemand an Ihre Firmendaten.",
  },
  {
    titel: "Connector einrichten",
    text: "Wir richten den Connector für Ihre Firma ein: Rechte-Umfang, Datenfelder und Sicherheitsregeln nach Ihren Vorgaben.",
  },
  {
    titel: "Agenten arbeiten",
    text: "Ihre KI-Agenten können im angebundenen System lesen und schreiben und liefern Ergebnisse direkt in Ihre Abläufe.",
  },
];

/** Anfrage-Modal: ehrlicher 3-Schritte-Ablauf + mailto-Anfrage. */
function AnfrageModal({ connector, onClose }: { connector: Connector; onClose: () => void }) {
  const akzent = KATEGORIE_FARBE[connector.kategorie];
  return (
    <HudModal labelId="anfrage-title" onClose={onClose}>
      <div className={`${EYEBROW} mb-1`}>Integration // Anfrage</div>
      <div className="flex items-center gap-3">
        <MonogrammBadge monogramm={connector.monogramm} akzent={akzent} />
        <h2 id="anfrage-title" className="text-xl font-bold text-[#1c1917]">
          Anbindung {connector.name}
        </h2>
      </div>
      <p className="mt-3 text-sm text-[#8d8172]">
        So läuft eine Live-Anbindung ehrlich ab — sie wird pro Unternehmen eingerichtet:
      </p>

      <ol className="mt-4 space-y-3">
        {ABLAUF_SCHRITTE.map((s, i) => (
          <li key={s.titel} className="flex gap-3">
            <span
              aria-hidden
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-xl border border-[#ffb066]/50 bg-[#fff4e6] font-mono text-xs font-bold text-[#c25e0e]"
            >
              {i + 1}
            </span>
            <div>
              <div className="text-sm font-semibold text-[#1c1917]">{s.titel}</div>
              <p className="mt-0.5 text-sm leading-relaxed text-[#8d8172]">{s.text}</p>
            </div>
          </li>
        ))}
      </ol>

      <a
        href={mailtoHref(connector.name)}
        className={`mt-6 block w-full rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-6 py-3 text-center font-semibold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)] transition hover:brightness-105 active:scale-[0.98] ${FOCUS_RING}`}
      >
        Anfrage per E-Mail senden
      </a>
      <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-[#a89c8a]">
        Betreff: Anbindung {connector.name}
      </p>
    </HudModal>
  );
}

/** Connector-Karte: Monogramm, Name, Beschreibung, Badges, Anfrage-Button. */
const ConnectorCard = memo(function ConnectorCard({
  connector,
  onRequest,
}: {
  connector: Connector;
  onRequest: (c: Connector) => void;
}) {
  const akzent = KATEGORIE_FARBE[connector.kategorie];
  return (
    <div className="acc-card acc-card-hover flex flex-col rounded-2xl p-4">
      <div className="flex items-start gap-3">
        <MonogrammBadge monogramm={connector.monogramm} akzent={akzent} />
        <div className="min-w-0">
          <h3 className="font-semibold text-[#1c1917]">{connector.name}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <PlanBadge planStufe={connector.planStufe} />
            <StatusBadge status={connector.status} />
          </div>
        </div>
      </div>
      <p className="mt-3 flex-1 text-sm leading-relaxed text-[#8d8172]">{connector.beschreibung}</p>
      <button
        onClick={() => onRequest(connector)}
        className={`mt-4 w-full rounded-xl border border-[#e0d8c6] bg-white/70 px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#4a4335] transition-colors hover:border-[#ffb066] hover:text-[#c25e0e] ${FOCUS_RING}`}
      >
        Anbindung anfragen
      </button>
    </div>
  );
});

/** Eine Kategorie-Gruppe mit ihren Connector-Karten. */
const KategorieSektion = memo(function KategorieSektion({
  kategorie,
  connectors,
  onRequest,
}: {
  kategorie: ConnectorKategorie;
  connectors: Connector[];
  onRequest: (c: Connector) => void;
}) {
  const akzent = KATEGORIE_FARBE[kategorie];
  return (
    <section aria-label={kategorie} className="mt-8">
      <div className="mb-3 flex items-center gap-3">
        <span aria-hidden className="h-2 w-2 rounded-full" style={{ background: akzent }} />
        <h2 className="text-[11px] font-bold uppercase tracking-wider text-[#8d8172]">
          {kategorie}{" // "}{connectors.length} System{connectors.length === 1 ? "" : "e"}
        </h2>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {connectors.map((c) => (
          <ConnectorCard key={c.id} connector={c} onRequest={onRequest} />
        ))}
      </div>
    </section>
  );
});

/* --------------------------------- Seite ---------------------------------- */

export default function IntegrationenPage() {
  const [anfrage, setAnfrage] = useState<Connector | null>(null);

  const standardKategorien = KATEGORIEN.filter((k) => k !== "Eigene Systeme");
  const eigeneSysteme = CONNECTORS.filter((c) => c.kategorie === "Eigene Systeme");

  return (
    <main className="acc-page relative min-h-screen text-[#1c1917]">
      {/* Header im hellen Stil mit Link zurück */}
      <header className="sticky top-0 z-20 border-b border-[#e8e1d2] bg-white/80 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-2">
          <div>
            <Link href="/" className="text-lg font-bold tracking-tight text-[#1c1917]">
              AI <span className="acc-grad-text">Command Center</span>
            </Link>
            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#8d8172]">
              Integration-Center // Katalog
            </div>
          </div>
          <a
            href="/dashboard"
            className={`rounded-xl border border-[#e0d8c6] bg-white/70 px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#4a4335] transition-colors hover:border-[#ffb066] hover:text-[#c25e0e] ${FOCUS_RING}`}
          >
            ← Zurück zum Dashboard
          </a>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-7xl px-5 py-8">
        {/* Hero */}
        <section aria-label="Integration-Center" className="acc-card acc-in rounded-2xl p-5">
          <div className={`${EYEBROW} mb-2`}>Anbindungen // Firmensysteme</div>
          <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
            Integration-Center: Verbinden Sie Ihre KI-Abteilung mit Ihren{" "}
            <span className="acc-grad-text">Systemen</span>
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-[#8d8172]">
            Jede Anbindung wird pro Unternehmen eingerichtet: Sie geben der KI in Ihrem
            System Zugriff frei, wir bauen den Connector — danach können Ihre Agenten
            dort lesen und schreiben.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <OnboardingWizard />
            <span className="text-xs text-[#8d8172]">
              Schritt für Schritt: Systeme wählen, Firma hinterlegen, Anbindung anfragen.
            </span>
          </div>
        </section>

        {/* Kategorie-Gruppen */}
        {standardKategorien.map((k) => (
          <KategorieSektion
            key={k}
            kategorie={k}
            connectors={CONNECTORS.filter((c) => c.kategorie === k)}
            onRequest={setAnfrage}
          />
        ))}

        {/* Eigene Systeme: generischer REST/Webhook-Connector */}
        <section aria-label="Eigene Systeme" className="mt-10">
          <div className="acc-card rounded-2xl p-5">
            <div className={`${EYEBROW} mb-2`}>Eigene Systeme // REST + Webhooks</div>
            <h2 className="text-xl font-bold text-[#1c1917]">
              Ihre Firmensoftware ist nicht dabei?
            </h2>
            <p className="mt-1 max-w-3xl text-sm text-[#8d8172]">
              Über den generischen REST/Webhook-Connector binden wir jede eigene
              Firmen-API an — gleicher Ablauf: Zugriff freigeben, Connector einrichten,
              Agenten arbeiten.
            </p>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {eigeneSysteme.map((c) => (
                <ConnectorCard key={c.id} connector={c} onRequest={setAnfrage} />
              ))}
            </div>
          </div>
        </section>

        {/* Ehrlicher Footer-Hinweis */}
        <footer className="mt-10 border-t border-[#e8e1d2] pt-4 pb-8">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#a89c8a]">
            Live-Anbindungen werden pro Unternehmen eingerichtet (Enterprise).
            Prototypen und Datei-Ausgabe funktionieren sofort.
          </p>
        </footer>
      </div>

      {anfrage && <AnfrageModal connector={anfrage} onClose={() => setAnfrage(null)} />}
    </main>
  );
}
