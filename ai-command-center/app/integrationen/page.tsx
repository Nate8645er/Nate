"use client";

/**
 * Integration-Center — Anbindungs-Katalog fuer Firmensysteme (JARVIS-HUD).
 *
 * Rein statischer Katalog aus lib/connectors.ts: Kategorie-Gruppen mit
 * Connector-Karten (Monogramm-Badge statt Markenlogo, Plan- und
 * Status-Badge). "Anbindung anfragen" oeffnet ein HUD-Modal, das den
 * ehrlichen 3-Schritte-Ablauf erklaert und per mailto eine Anfrage mit
 * vorbefuelltem Betreff startet. Keine Live-Verbindungen auf dieser Seite —
 * die werden pro Unternehmen als Enterprise-Projekt eingerichtet.
 */

import { memo, useEffect, useRef, useState } from "react";
import {
  CONNECTORS,
  KATEGORIEN,
  KATEGORIE_AKZENT,
  STATUS_LABEL,
  type Connector,
  type ConnectorKategorie,
} from "@/lib/connectors";

/** Ziel-Adresse fuer Anbindungs-Anfragen. */
const KONTAKT_EMAIL = "beamswiss@gmail.com";

/** Fokus-Ring fuer Tastaturbedienung (focus-visible) im HUD-Stil. */
const FOCUS_RING =
  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#ff8c2a]/70";

/** mailto-Link mit vorbefuelltem Betreff "Anbindung <Name>". */
function mailtoHref(connectorName: string): string {
  const subject = encodeURIComponent(`Anbindung ${connectorName}`);
  const body = encodeURIComponent(
    `Guten Tag\n\nWir moechten die Anbindung "${connectorName}" fuer unser Unternehmen anfragen.\n\nFirma:\nAnsprechperson:\nAktueller Plan (BUSINESS/ENTERPRISE):\n\nFreundliche Gruesse`,
  );
  return `mailto:${KONTAKT_EMAIL}?subject=${subject}&body=${body}`;
}

/** Monogramm-Badge (2 Buchstaben) im HUD-Stil — bewusst kein Markenlogo. */
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
      className="flex h-11 w-11 shrink-0 items-center justify-center rounded-sm border font-mono text-sm font-bold tracking-[0.08em]"
      style={{
        color: akzent,
        borderColor: `${akzent}59`,
        background: `${akzent}0f`,
        boxShadow: `0 0 12px ${akzent}26, inset 0 0 10px ${akzent}14`,
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
      className={`rounded-sm border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] ${
        enterprise
          ? "border-[#ffd257]/50 bg-[#ffd257]/10 text-[#ffd257]"
          : "border-[#ff8c2a]/40 bg-[#ff8c2a]/[0.08] text-[#ffb35c]"
      }`}
    >
      ab {planStufe}
    </span>
  );
});

/** Status-Badge: Verfuegbar auf Anfrage / In Entwicklung. */
const StatusBadge = memo(function StatusBadge({ status }: { status: Connector["status"] }) {
  const available = status === "verfuegbar-auf-anfrage";
  return (
    <span
      className={`flex items-center gap-1.5 rounded-sm border px-2 py-0.5 font-mono text-[9px] uppercase tracking-[0.16em] ${
        available
          ? "border-[#ffb35c]/35 bg-[#ffb35c]/[0.06] text-[#ffb35c]/90"
          : "border-[#8a7455]/50 bg-[#8a7455]/10 text-[#c9b391]"
      }`}
    >
      <span
        aria-hidden
        className={`h-1.5 w-1.5 rounded-full ${available ? "hud-pulse bg-[#ffb35c]" : "bg-[#8a7455]"}`}
      />
      {STATUS_LABEL[status]}
    </span>
  );
});

/**
 * HUD-Modal-Shell (Spiegel des Dashboard-Modals): role=dialog, Escape und
 * Klick auf den Hintergrund schliessen, Fokus springt hinein und zurueck.
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
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelId}
        tabIndex={-1}
        className="hud-panel hud-corners hud-modal-in relative w-full max-w-lg rounded-sm border border-[#ff8c2a]/30 bg-[#0b0a08] p-6 outline-none"
      >
        <button
          onClick={onClose}
          aria-label="Schliessen"
          className={`absolute right-3 top-3 rounded-sm px-2 py-1 font-mono text-xs text-[#ffb35c]/70 transition hover:text-[#fff3e2] ${FOCUS_RING}`}
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
    text: "Sie geben der KI in IHREM System per OAuth oder API-Schluessel Zugriff frei — ohne diese Freigabe kommt niemand an Ihre Firmendaten.",
  },
  {
    titel: "Connector einrichten",
    text: "Wir richten den Connector fuer Ihre Firma ein: Rechte-Umfang, Datenfelder und Sicherheitsregeln nach Ihren Vorgaben.",
  },
  {
    titel: "Agenten arbeiten",
    text: "Ihre KI-Agenten koennen im angebundenen System lesen und schreiben und liefern Ergebnisse direkt in Ihre Ablaeufe.",
  },
];

/** Anfrage-Modal: ehrlicher 3-Schritte-Ablauf + mailto-Anfrage. */
function AnfrageModal({ connector, onClose }: { connector: Connector; onClose: () => void }) {
  const akzent = KATEGORIE_AKZENT[connector.kategorie];
  return (
    <HudModal labelId="anfrage-title" onClose={onClose}>
      <div className="hud-label mb-1">Integration // Anfrage</div>
      <div className="flex items-center gap-3">
        <MonogrammBadge monogramm={connector.monogramm} akzent={akzent} />
        <h2 id="anfrage-title" className="text-xl font-bold text-[#fff3e2]">
          Anbindung {connector.name}
        </h2>
      </div>
      <p className="mt-3 text-sm text-[#c9b391]">
        So laeuft eine Live-Anbindung ehrlich ab — sie wird pro Unternehmen eingerichtet:
      </p>

      <ol className="mt-4 space-y-3">
        {ABLAUF_SCHRITTE.map((s, i) => (
          <li key={s.titel} className="flex gap-3">
            <span
              aria-hidden
              className="flex h-7 w-7 shrink-0 items-center justify-center rounded-sm border border-[#ff8c2a]/40 bg-[#ff8c2a]/[0.06] font-mono text-xs font-bold text-[#ff8c2a]"
            >
              {i + 1}
            </span>
            <div>
              <div className="text-sm font-semibold text-[#fff3e2]">{s.titel}</div>
              <p className="mt-0.5 text-sm leading-relaxed text-[#c9b391]">{s.text}</p>
            </div>
          </li>
        ))}
      </ol>

      <a
        href={mailtoHref(connector.name)}
        className={`mt-6 block w-full rounded-sm bg-[#ff8c2a] px-6 py-3 text-center font-semibold text-[#1a0f04] transition hover:bg-[#ffb35c] active:scale-[0.98] ${FOCUS_RING}`}
      >
        Anfrage per E-Mail senden
      </a>
      <p className="mt-2 text-center font-mono text-[10px] uppercase tracking-[0.14em] text-[#8a7455]">
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
  const akzent = KATEGORIE_AKZENT[connector.kategorie];
  return (
    <div className="hud-panel hud-corners flex flex-col rounded-sm p-4">
      <div className="flex items-start gap-3">
        <MonogrammBadge monogramm={connector.monogramm} akzent={akzent} />
        <div className="min-w-0">
          <h3 className="font-semibold text-[#fff3e2]">{connector.name}</h3>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
            <PlanBadge planStufe={connector.planStufe} />
            <StatusBadge status={connector.status} />
          </div>
        </div>
      </div>
      <p className="mt-3 flex-1 text-sm leading-relaxed text-[#c9b391]">{connector.beschreibung}</p>
      <button
        onClick={() => onRequest(connector)}
        className={`mt-4 w-full rounded-sm border border-[#ff8c2a]/40 bg-[#ff8c2a]/[0.06] px-4 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ff8c2a] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
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
  const akzent = KATEGORIE_AKZENT[kategorie];
  return (
    <section aria-label={kategorie} className="mt-8">
      <div className="mb-3 flex items-center gap-3">
        <span aria-hidden className="h-2 w-2 rounded-full" style={{ background: akzent, boxShadow: `0 0 8px ${akzent}` }} />
        <h2 className="hud-label !text-[11px]">
          {kategorie} // {connectors.length} System{connectors.length === 1 ? "" : "e"}
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
    <main className="relative min-h-screen bg-[#0b0a08] text-[#e8dcc8]">
      <div className="hud-texture" aria-hidden />

      {/* Header im Dashboard-Stil mit Link zurueck */}
      <header className="sticky top-0 z-20 border-b border-[#ff8c2a]/15 bg-[#0b0a08]/85 backdrop-blur">
        <div className="mx-auto flex min-h-16 max-w-7xl flex-wrap items-center justify-between gap-3 px-5 py-2">
          <div>
            <a href="/" className="text-lg font-bold tracking-tight text-[#fff3e2]">
              AI <span className="text-[#ff8c2a]">Command Center</span>
            </a>
            <div className="hud-label">Integration-Center // Katalog</div>
          </div>
          <a
            href="/dashboard"
            className={`rounded-sm border border-[#ff8c2a]/40 bg-[#ff8c2a]/[0.06] px-3 py-1.5 font-mono text-[10px] uppercase tracking-[0.14em] text-[#ff8c2a] transition-colors hover:bg-[#ff8c2a]/15 ${FOCUS_RING}`}
          >
            ← Zurueck zum Dashboard
          </a>
        </div>
      </header>

      <div className="relative z-10 mx-auto max-w-7xl px-5 py-8">
        {/* Hero */}
        <section aria-label="Integration-Center" className="hud-panel hud-corners rounded-sm p-5">
          <div className="hud-label mb-2">Anbindungen // Firmensysteme</div>
          <h1 className="text-2xl font-bold text-[#fff3e2]">
            Integration-Center: Verbinden Sie Ihre KI-Abteilung mit Ihren Systemen
          </h1>
          <p className="mt-1 max-w-3xl text-sm text-[#c9b391]">
            Jede Anbindung wird pro Unternehmen eingerichtet: Sie geben der KI in Ihrem
            System Zugriff frei, wir bauen den Connector — danach koennen Ihre Agenten
            dort lesen und schreiben.
          </p>
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
          <div className="hud-panel hud-corners rounded-sm p-5">
            <div className="hud-label mb-2">Eigene Systeme // REST + Webhooks</div>
            <h2 className="text-xl font-bold text-[#fff3e2]">
              Ihre Firmensoftware ist nicht dabei?
            </h2>
            <p className="mt-1 max-w-3xl text-sm text-[#c9b391]">
              Ueber den generischen REST/Webhook-Connector binden wir jede eigene
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
        <footer className="mt-10 border-t border-[#ff8c2a]/15 pt-4 pb-8">
          <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-[#8a7455]">
            Live-Anbindungen werden pro Unternehmen eingerichtet (Enterprise).
            Prototypen und Datei-Ausgabe funktionieren sofort.
          </p>
        </footer>
      </div>

      {anfrage && <AnfrageModal connector={anfrage} onClose={() => setAnfrage(null)} />}
    </main>
  );
}
