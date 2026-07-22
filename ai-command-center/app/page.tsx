import type { Metadata } from "next";
import Link from "next/link";
import { RECHERCHE_QUELLEN } from "@/lib/agents/browser";

export const metadata: Metadata = {
  title: "AI Command Center | Die digitale KI-Belegschaft für Ihr Unternehmen",
  description:
    "Eine ganze KI-Belegschaft im Abo: plant, recherchiert, schreibt und programmiert – fertige Websites, Dokumente und Analysen in Minuten. Schweizer Anbieter, monatlich kündbar, Demo ohne Kreditkarte.",
};

/* Shop-Basis-URL zentral, per Env konfigurierbar (NEXT_PUBLIC_SHOP_BASE).
 * Ohne gesetzte Env zeigen die Abo-Buttons auf den Preis-Anker der Seite,
 * damit keine feste Fremd-Domain im Code steht. Für den Verkauf in Vercel
 * NEXT_PUBLIC_SHOP_BASE auf die eigene Shop-Produkt-URL setzen. */
const SHOP_BASE = process.env.NEXT_PUBLIC_SHOP_BASE || "#abos";

type Plan = {
  name: string;
  price: string;
  priceNote: string;
  /** Jahresabo-Anzeige, z. B. "199 CHF/Jahr" (2 Monate geschenkt). */
  priceYear?: string;
  team: string;
  badge?: string;
  highlight?: boolean;
  benefits: string[];
  handle: string;
};

const PLANS: Plan[] = [
  {
    name: "Free",
    price: "0",
    priceNote: "CHF, für immer",
    team: "Team: 4 Agenten",
    benefits: [
      "4 KI-Agenten zum Kennenlernen",
      "3 Missionen pro Tag",
      "Basis-Skills zum Kennenlernen",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.FREE} Quellen)`,
      "Ergebnis-Vorschau direkt im Browser",
      "Knappes Token-Budget – zum Kennenlernen",
      "Ohne Kreditkarte, ohne Risiko",
    ],
    handle: "free-demo-ki-team-kostenlos-testen",
  },
  {
    name: "Personal",
    price: "19.90",
    priceNote: "CHF pro Monat",
    priceYear: "199 CHF/Jahr",
    team: "Ihr Kern-Team",
    benefits: [
      "10 Missionen pro Tag",
      "Fertige Dateien mit Download",
      "Skills für den Alltag",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.PERSONAL} Quellen)`,
      "E-Mail-Zentrale, CRM & Autopilot",
      "Perfekt für Einzelpersonen",
      "⚡ Ultra-Levelup-Code erhältlich",
    ],
    handle: "personal-ai-ihr-personlicher-ki-assistent-monatsabo",
  },
  {
    name: "Starter",
    price: "199",
    priceNote: "CHF pro Monat",
    priceYear: "1'990 CHF/Jahr",
    team: "Team: 12 Agenten",
    badge: "Bestseller",
    highlight: true,
    benefits: [
      "12 spezialisierte KI-Agenten",
      "25 Missionen pro Tag",
      "Skills inkl. Verkauf & Marketing",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.STARTER} Quellen)`,
      "Echte Dateien und Code mit Download",
      "Quality-Score je Ergebnis",
      "E-Mail-Support",
      "⚡ Ultra-Levelup-Code erhältlich",
    ],
    handle: "starter-ai-ihre-personliche-ki-abteilung-monatsabo",
  },
  {
    name: "Professional",
    price: "799",
    priceNote: "CHF pro Monat",
    priceYear: "7'990 CHF/Jahr",
    team: "Team: 50 Agenten",
    benefits: [
      "50 Agenten in Fachteams organisiert",
      "Skills inkl. Finanzen & Analyse",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.PROFESSIONAL} Quellen)`,
      "Dokumente analysieren: PDF, Word, Excel",
      "5 Firmen-Integrationen inklusive",
      "Prioritäts-Verarbeitung",
      "Support innert 24 Stunden",
      "⚡ Ultra-Levelup-Code erhältlich",
    ],
    handle: "professional-ai-die-komplette-ki-arbeitsumgebung-monatsabo",
  },
  {
    name: "Business",
    price: "2'499",
    priceNote: "CHF pro Monat",
    priceYear: "24'990 CHF/Jahr",
    team: "Abteilung: 250 Agenten",
    badge: "Beliebt bei Firmen",
    highlight: true,
    benefits: [
      "250 Agenten als digitale Abteilung",
      "Skills inkl. Personal & Recht",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.BUSINESS} Quellen)`,
      "Alle Firmen-Integrationen",
      "Eigene Workflows und Freigaben",
      "Zugänge für Ihr ganzes Team",
      "Dedizierter Ansprechpartner",
      "⚡ Ultra-Levelup-Code erhältlich",
    ],
    handle: "business-ai-die-digitale-ki-abteilung-furs-unternehmen-monatsabo",
  },
  {
    name: "Enterprise",
    price: "ab 8'900",
    priceNote: "CHF pro Monat",
    priceYear: "ab 89'000 CHF/Jahr",
    team: "Belegschaft: 1000 Mitarbeitende",
    benefits: [
      "Bis 1000 virtuelle Mitarbeitende",
      "Alle Skills + KI-Strategie exklusiv",
      `KI-Browser: recherchiert im Web (${RECHERCHE_QUELLEN.ENTERPRISE} Quellen)`,
      "Individuelle KI-Infrastruktur",
      "Private Cloud oder On-Premise möglich",
      "SLA und Sicherheit nach Mass",
      "Persönliche Begleitung beim Aufbau",
      "⚡ Ultra-Levelup-Code erhältlich",
    ],
    handle: "enterprise-ai-individuelle-ki-infrastruktur-ab-10000-monat",
  },
];

/** Akzentfarbe je Funktions-Kachel – bewusst bunt (Indigo/Orange/Teal/Pink). */
const FEATURE_ACCENTS = [
  "bg-[#eef0ff] text-[#5b52d6]",
  "bg-[#e6faf6] text-[#0f766e]",
  "bg-[#fff4e6] text-[#c25e0e]",
  "bg-[#fdeef7] text-[#be185d]",
];

const FEATURES = [
  {
    title: "Echte Dateien und Code",
    text: "Ihr KI-Team liefert fertige Resultate: Dokumente, Tabellen, Quellcode. Mit Vorschau im Browser und Download mit einem Klick.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M6 2.5h8l4 4V21a.5.5 0 0 1-.5.5h-11A.5.5 0 0 1 6 21V3a.5.5 0 0 1 .5-.5Z" />
        <path d="M14 2.5v4h4" />
        <path d="m10 12-2 2.5 2 2.5M14 12l2 2.5-2 2.5" />
      </svg>
    ),
  },
  {
    title: "Dokumente analysieren",
    text: "PDFs, Verträge, Berichte und Tabellen hochladen. Ihr Team liest, fasst zusammen, prüft und beantwortet Ihre Fragen dazu.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <circle cx="10.5" cy="10.5" r="6" />
        <path d="m15 15 5.5 5.5" />
        <path d="M8 10.5h5M10.5 8v5" />
      </svg>
    ),
  },
  {
    title: "Virtuelle Organisation",
    text: "Vom 4er-Team bis zur Belegschaft mit 1000 virtuellen Mitarbeitenden: Abteilungen, Rollen und Freigaben wie in einer echten Firma.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <rect x="9" y="2.5" width="6" height="5" rx="1" />
        <rect x="2.5" y="16.5" width="6" height="5" rx="1" />
        <rect x="15.5" y="16.5" width="6" height="5" rx="1" />
        <path d="M12 7.5v4m0 0H5.5v5m6.5-5h6.5v5" />
      </svg>
    ),
  },
  {
    title: "Firmen-Integrationen",
    text: "E-Mail, Kalender, Cloud-Speicher, Shop und mehr: Ihr KI-Team arbeitet direkt mit den Werkzeugen, die Sie schon nutzen.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M9 7V3.5M15 7V3.5" />
        <path d="M7 7h10v4a5 5 0 0 1-10 0V7Z" />
        <path d="M12 16v4.5" />
      </svg>
    ),
    href: "/integrationen",
    linkLabel: "Alle Integrationen ansehen",
  },
  {
    title: "Marketing und Kampagnen",
    text: "Kampagnenpläne, Werbetexte und ganze Content-Serien: Ihr Team plant, schreibt und liefert fertige Entwürfe zur Freigabe.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M3.5 10.5v3a1 1 0 0 0 1 1H7l7.5 4V5.5L7 9.5H4.5a1 1 0 0 0-1 1Z" />
        <path d="M14.5 9.5a3 3 0 0 1 0 5" />
        <path d="M7 14.5v4a1 1 0 0 0 1 1h1.5" />
      </svg>
    ),
  },
  {
    title: "Strategie und Zahlen",
    text: "Businesspläne, Finanz-Einordnung und Entscheidungsvorlagen: fundierte Grundlagen, bevor Sie den nächsten Schritt gehen.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M3.5 3.5v16a1 1 0 0 0 1 1h16" />
        <path d="m7 14 4-4 3 3 5.5-5.5" />
        <path d="M15.5 7.5h4v4" />
      </svg>
    ),
  },
  {
    title: "Quality-Score 0-100",
    text: "Jedes Ergebnis wird geprüft, bevor Sie es sehen. Der Score von 0 bis 100 zeigt sofort, wie belastbar ein Resultat ist.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M12 2.5 5 5.5v5c0 4.5 3 8.5 7 10.5 4-2 7-6 7-10.5v-5l-7-3Z" />
        <path d="m8.8 11.8 2.2 2.2 4.2-4.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
  },
  {
    title: "Passt sich Ihrer Branche an",
    text: "Das Onboarding stellt Ihr Team auf Ihre Firma ein: Branche, Tonalität und Ziele fliessen in jede Mission ein.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M4 6.5h16M4 12h16M4 17.5h16" />
        <circle cx="9" cy="6.5" r="2" fill="currentColor" />
        <circle cx="15" cy="12" r="2" fill="currentColor" />
        <circle cx="7" cy="17.5" r="2" fill="currentColor" />
      </svg>
    ),
  },
  {
    title: "Kommandozentrale für den Chef",
    text: "Kein Chatbot: Sie geben Befehle – «Erstelle», «Kontrolliere», «Analysiere» – und Ihre Belegschaft führt aus, bis das fertige Ergebnis mit Dateien vorliegt.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M4 5h16v12H4z" strokeLinejoin="round" />
        <path d="m7 9 3 2.5L7 14M12.5 14H17" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M9 20.5h6" strokeLinecap="round" />
      </svg>
    ),
    href: "/chat",
    linkLabel: "Kommandozentrale öffnen",
  },
  {
    title: "E-Mail-Arbeit erledigt die KI",
    text: "Eingehende Mail einfügen, fertige Antwort erhalten – oder ganze Offerten schreiben lassen. Ein Klick öffnet Gmail, Sie drücken nur noch Senden.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M3.5 6h17v12h-17z" strokeLinejoin="round" />
        <path d="m4 7 8 6 8-6" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    ),
    href: "/email",
    linkLabel: "E-Mail-Zentrale öffnen",
  },
  {
    title: "Schreibt echten Code",
    text: "Auch für Informatik-Firmen: Scripts, Tools, Webanwendungen und Code-Reviews – als lauffähige Dateien geliefert, mit technischer Dokumentation.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="m8 8-4.5 4L8 16M16 8l4.5 4L16 16" strokeLinecap="round" strokeLinejoin="round" />
        <path d="m13 5-2 14" strokeLinecap="round" />
      </svg>
    ),
    href: "/faehigkeiten",
    linkLabel: "Code-Skills ansehen",
  },
  {
    title: "Autopilot-Workflows",
    text: "Wiederkehrende Aufträge einmal anlegen – Ihre Belegschaft erledigt sie regelmässig: Wochenpläne, Berichte, Angebotsideen.",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className="h-7 w-7">
        <path d="M12 4a8 8 0 1 1-7.5 5.2" strokeLinecap="round" />
        <path d="M4.5 4v5h5" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 8.5V12l2.5 2" strokeLinecap="round" />
      </svg>
    ),
    href: "/workflows",
    linkLabel: "Workflows ansehen",
  },
];

const TRUST = [
  { label: "Schweizer Anbieter", note: "Betrieb und Support aus der Schweiz" },
  { label: "Monatlich kündbar", note: "Keine Mindestlaufzeit, keine Hürden" },
  { label: "Quality-Score", note: "Jedes Ergebnis wird bewertet" },
  { label: "Demo ohne Kreditkarte", note: "In 2 Minuten startklar" },
];

const FAQ = [
  {
    q: "Wie starte ich mit meinem KI-Team?",
    a: "Klicken Sie auf Kostenlos testen und Sie stehen direkt im Dashboard. Die Demo läuft ohne Kreditkarte und ohne Registrierungs-Marathon. Wenn Ihnen gefällt, was Ihr Team liefert, wählen Sie ein Abo im Shop.",
  },
  {
    q: "Kann ich jederzeit kündigen?",
    a: "Ja. Alle Abos sind monatlich kündbar, ohne Mindestlaufzeit. Sie kündigen direkt im Shop-Konto, das Abo läuft dann einfach zum Monatsende aus.",
  },
  {
    q: "Wem gehören die Ergebnisse?",
    a: "Ihnen. Alles, was Ihr KI-Team erstellt, können Sie herunterladen und uneingeschränkt geschäftlich nutzen: Dokumente, Analysen, Code.",
  },
  {
    q: "Was bedeutet der Quality-Score?",
    a: "Jedes Ergebnis wird vor der Auslieferung automatisch geprüft und mit einem Score bewertet. So sehen Sie auf einen Blick, wie belastbar ein Resultat ist, bevor Sie damit weiterarbeiten.",
  },
];

/* ------------------------------------------------------------------ */
/* Produkt-Schaufenster: stilisiertes helles Dashboard (CSS/SVG-Bild)  */
/* ------------------------------------------------------------------ */

function ProductShowcase() {
  return (
    <div className="shop-stage relative mx-auto mt-16 w-full max-w-4xl px-2 sm:mt-20">
      <div className="shop-glow absolute inset-x-0 -top-10 bottom-0 -z-10" aria-hidden="true" />
      <div
        className="shop-mock acc-card relative rounded-2xl p-4 sm:p-6"
        role="img"
        aria-label="Stilisierte Ansicht des AI Command Center Dashboards"
      >
        {/* Kopfzeile */}
        <div className="flex items-center justify-between border-b border-[#e8e1d2] pb-3">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#0f766e] hidden sm:inline">
            Alle Systeme bereit
          </span>
        </div>

        <div className="mt-5 grid gap-5 sm:grid-cols-[1fr_1.2fr_1fr] sm:gap-6">
          {/* Globus-Andeutung */}
          <div className="flex items-center justify-center rounded-xl bg-[#faf6ee] p-4">
            <svg viewBox="0 0 120 120" className="h-28 w-28 text-[#ff8c2a]" aria-hidden="true">
              <g className="hud-spin-slow" fill="none" stroke="currentColor">
                <circle cx="60" cy="60" r="44" strokeOpacity="0.55" />
                <ellipse cx="60" cy="60" rx="44" ry="18" strokeOpacity="0.4" />
                <ellipse cx="60" cy="60" rx="18" ry="44" strokeOpacity="0.4" />
                <circle cx="60" cy="60" r="30" strokeOpacity="0.25" strokeDasharray="4 6" />
              </g>
              <circle cx="60" cy="60" r="52" fill="none" stroke="currentColor" strokeOpacity="0.3" strokeDasharray="2 8" className="hud-spin-rev" />
              <circle cx="88" cy="42" r="2.5" fill="currentColor" />
              <circle cx="38" cy="78" r="2" fill="#5b52d6" />
            </svg>
          </div>

          {/* Agenten-Chips + Aktivität */}
          <div className="flex flex-col justify-between gap-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e] mb-2">Aktive Agenten</p>
              <div className="flex flex-wrap gap-2">
                {["Research", "Code", "Finanzen", "Design", "Recht", "Daten"].map((a) => (
                  <span
                    key={a}
                    className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-3 py-1 text-xs font-medium text-[#c25e0e]"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>
            <div className="space-y-2" aria-hidden="true">
              {[
                [82, "from-[#6d5efc] to-[#8b5cf6]"],
                [64, "from-[#2dd4bf] to-[#0f766e]"],
                [91, "from-[#ff8c2a] to-[#ff5f1f]"],
              ].map(([w, grad], i) => (
                <div key={i} className="h-1.5 overflow-hidden rounded-full bg-[#efe9dd]">
                  <div className={`h-full rounded-full bg-gradient-to-r ${grad}`} style={{ width: `${w}%` }} />
                </div>
              ))}
            </div>
          </div>

          {/* Score-Ring */}
          <div className="flex flex-col items-center justify-center gap-1 rounded-xl bg-[#faf6ee] p-4">
            <svg viewBox="0 0 100 100" className="h-24 w-24" aria-hidden="true">
              <circle cx="50" cy="50" r="40" fill="none" stroke="#ff8c2a" strokeOpacity="0.16" strokeWidth="7" />
              <circle
                cx="50"
                cy="50"
                r="40"
                fill="none"
                stroke="#ff8c2a"
                strokeWidth="7"
                strokeLinecap="round"
                strokeDasharray="251.3"
                strokeDashoffset="0"
                transform="rotate(-90 50 50)"
              />
              <text x="50" y="55" textAnchor="middle" fill="#c25e0e" fontSize="20" fontWeight="700">
                100
              </text>
            </svg>
            <span className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Quality-Score</span>
          </div>
        </div>

        {/* Missions-Zeile */}
        <div className="mt-5 grid gap-2 sm:grid-cols-3">
          {[
            ["Marktanalyse Q3", "Fertig", true],
            ["Landingpage-Code", "In Arbeit", false],
            ["Vertragsprüfung", "Fertig", true],
          ].map(([m, s, done]) => (
            <div key={m as string} className="flex items-center justify-between rounded-lg border border-[#efe9dd] bg-[#faf6ee] px-3 py-2">
              <span className="text-xs font-medium text-[#4a4335]">{m}</span>
              <span className={`text-[10px] font-bold uppercase tracking-wide ${done ? "text-[#177245]" : "text-[#c25e0e]"}`}>{s}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Seite                                                               */
/* ------------------------------------------------------------------ */

export default function Home() {
  return (
    <div className="acc-page flex flex-1 flex-col font-sans text-[#1c1917]">
      {/* Navigation */}
      <header className="sticky top-0 z-20 border-b border-[#e8e1d2] bg-white/75 backdrop-blur-xl">
        <nav className="mx-auto flex w-full max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" aria-hidden="true" />
            <span className="text-sm font-bold">AI Command Center</span>
          </Link>
          <div className="flex items-center gap-3 sm:gap-6">
            <a href="#abos" className="hidden text-sm font-medium text-[#6f6557] hover:text-[#1c1917] sm:inline">
              Abos
            </a>
            <a href="#funktionen" className="hidden text-sm font-medium text-[#6f6557] hover:text-[#1c1917] sm:inline">
              Funktionen
            </a>
            <Link
              href="/dashboard"
              className="shop-btn rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 py-2 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
            >
              Kostenlos testen
            </Link>
          </div>
        </nav>
      </header>

      <main className="flex-1">
        {/* 1) Hero: Produktbühne */}
        <section className="relative overflow-hidden px-6 pb-24 pt-20 sm:pt-28">
          <div className="acc-in mx-auto max-w-3xl text-center">
            <p className="mb-6 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
              Die erste digitale KI-Belegschaft der Schweiz
            </p>
            <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-6xl">
              Eine ganze <span className="acc-grad-text">KI-Belegschaft</span> für Ihr Unternehmen
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-pretty text-lg leading-8 text-[#6f6557]">
              Sie geben einen Auftrag – Ihre digitale Abteilung plant, recherchiert, schreibt
              und programmiert, bis das Ergebnis steht: fertige Websites, Dokumente,
              Präsentationen und Analysen. Geprüft mit Quality-Score, geliefert in Minuten
              statt Wochen.
            </p>
            <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/dashboard"
                className="shop-btn inline-flex h-12 w-full items-center justify-center rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-8 text-base font-bold text-white shadow-[0_10px_30px_-8px_rgba(255,110,30,0.55)] sm:w-auto"
              >
                Kostenlos testen
              </Link>
              <a
                href="#abos"
                className="shop-btn inline-flex h-12 w-full items-center justify-center rounded-full border border-[#e0d8c6] bg-white/70 px-8 text-base font-semibold text-[#4a4335] hover:border-[#ffb066] sm:w-auto"
              >
                Abos ansehen
              </a>
            </div>
            <p className="mt-4 text-sm text-[#8d8172]">Ohne Kreditkarte. In 2 Minuten startklar.</p>
          </div>

          <ProductShowcase />
        </section>

        {/* 1b) KI-Belegschaft bei der Arbeit (Higgsfield-Illustration) */}
        <section className="border-t border-[#e8e1d2] px-6 py-20">
          <div className="mx-auto max-w-6xl">
            <div className="mx-auto max-w-2xl text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Ihre digitale Belegschaft</p>
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Ein ganzes <span className="acc-grad-text">Büro</span>, das für Sie arbeitet
              </h2>
              <p className="mt-4 text-lg text-[#6f6557]">
                Sie geben den Auftrag – Ihre KI-Abteilungen arbeiten parallel: recherchieren,
                schreiben, rechnen und prüfen, bis das fertige Ergebnis vorliegt.
              </p>
            </div>
            <div className="mt-10 overflow-hidden rounded-3xl border border-[#e8e1d2] bg-white p-2 shadow-[0_30px_80px_-40px_rgba(28,25,23,0.28)] sm:p-3">
              {/* Animierter Trailer (Higgsfield) mit Standbild als Poster/Fallback */}
              <video
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
                poster="/ki-buero.webp"
                aria-label="Animierte Szene der digitalen KI-Belegschaft: Figuren arbeiten im Büro an Computern, recherchieren, schreiben und besprechen sich"
                className="h-auto w-full rounded-2xl"
              >
                <source src="/ki-trailer.mp4" type="video/mp4" />
              </video>
            </div>
          </div>
        </section>

        {/* 2) Shop-Regal: Abos */}
        <section id="abos" className="scroll-mt-24 border-t border-[#e8e1d2] px-6 py-24">
          <div className="mx-auto max-w-[88rem]">
            <div className="mx-auto max-w-2xl text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Abos</p>
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Wählen Sie die Grösse Ihrer <span className="acc-grad-text">KI-Abteilung</span>
              </h2>
              <p className="mt-4 text-lg text-[#6f6557]">
                Vom kleinen Team bis zur ganzen Belegschaft. Jedes Abo ist monatlich kündbar.
              </p>
            </div>

            <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {PLANS.map((plan) => (
                <article
                  key={plan.name}
                  className={`shop-card acc-card relative flex flex-col rounded-2xl p-6 ${
                    plan.highlight ? "ring-2 ring-[#ff8c2a]/40" : ""
                  }`}
                >
                  {plan.badge && (
                    <span className="absolute -top-3 left-6 rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-3 py-0.5 text-xs font-semibold text-white shadow-[0_4px_14px_-4px_rgba(255,110,30,0.6)]">
                      {plan.badge}
                    </span>
                  )}
                  <h3 className="text-lg font-semibold">{plan.name}</h3>
                  <p className="mt-4 flex items-baseline gap-2">
                    <span className="text-4xl font-semibold tracking-tight">{plan.price}</span>
                  </p>
                  <p className="mt-1 text-sm text-[#8d8172]">{plan.priceNote}</p>
                  {plan.priceYear && (
                    <p className="mt-1 text-xs font-semibold text-[#0f766e]">
                      oder {plan.priceYear} – 2 Monate geschenkt
                    </p>
                  )}
                  <p className="mt-3 inline-flex w-fit rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-3 py-1 text-xs font-medium text-[#c25e0e]">
                    {plan.team}
                  </p>
                  <ul className="mt-5 flex-1 space-y-2.5 text-sm leading-6 text-[#4a4335]">
                    {plan.benefits.map((b) => (
                      <li key={b} className="flex gap-2">
                        <svg viewBox="0 0 20 20" className="mt-1 h-4 w-4 shrink-0 text-[#ff8c2a]" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                          <path d="m4 10.5 4 4 8-9" strokeLinecap="round" strokeLinejoin="round" />
                        </svg>
                        <span>{b}</span>
                      </li>
                    ))}
                  </ul>
                  <div className="mt-7 flex flex-col gap-2.5">
                    <a
                      href={SHOP_BASE.startsWith("#") ? SHOP_BASE : `${SHOP_BASE}/${plan.handle}`}
                      {...(SHOP_BASE.startsWith("#") ? {} : { target: "_blank", rel: "noopener noreferrer" })}
                      className="shop-btn inline-flex h-11 items-center justify-center rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-5 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
                    >
                      Jetzt kaufen
                    </a>
                    <Link
                      href="/dashboard"
                      className="shop-btn inline-flex h-11 items-center justify-center rounded-full border border-[#e0d8c6] bg-white/70 px-5 text-sm font-semibold text-[#4a4335] hover:border-[#ffb066]"
                    >
                      Testen
                    </Link>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        {/* 3) Funktionen */}
        <section id="funktionen" className="scroll-mt-24 border-t border-[#e8e1d2] px-6 py-24">
          <div className="mx-auto max-w-6xl">
            <div className="mx-auto max-w-2xl text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Funktionen</p>
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Was Ihr <span className="acc-grad-text">Team</span> kann
              </h2>
            </div>
            <div className="mt-14 grid gap-6 sm:grid-cols-2">
              {FEATURES.map((f, i) => (
                <div key={f.title} className="shop-card acc-card acc-card-hover rounded-2xl p-8">
                  <div className={`mb-5 inline-flex rounded-xl p-3 ${FEATURE_ACCENTS[i % FEATURE_ACCENTS.length]}`}>
                    {f.icon}
                  </div>
                  <h3 className="text-xl font-semibold">{f.title}</h3>
                  <p className="mt-3 leading-7 text-[#6f6557]">{f.text}</p>
                  {f.href && (
                    <Link
                      href={f.href}
                      className="mt-4 inline-block text-sm font-semibold text-[#c25e0e] underline underline-offset-4 hover:text-[#ff5f1f]"
                    >
                      {f.linkLabel}
                    </Link>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* 3a) Erklär-Video mit Sprecher */}
        <section id="video" className="scroll-mt-24 border-t border-[#e8e1d2] px-6 py-24">
          <div className="mx-auto max-w-4xl">
            <div className="mx-auto max-w-2xl text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">In 70 Sekunden erklärt</p>
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Sehen Sie Ihrer <span className="acc-grad-text">Belegschaft</span> bei der Arbeit zu
              </h2>
              <p className="mt-4 text-[#6f6557]">
                Vom Befehl bis zur fertigen Datei – alle Bereiche im Überblick,
                professionell erklärt.
              </p>
            </div>
            <div className="shop-stage mt-10">
              <video
                controls
                preload="metadata"
                poster="/shop-hero.webp"
                className="w-full rounded-2xl border border-[#e8e1d2] shadow-[0_24px_80px_-24px_rgba(255,120,40,0.28)]"
              >
                <source src="/erklaervideo.mp4" type="video/mp4" />
                Ihr Browser kann dieses Video nicht abspielen.
              </video>
            </div>
          </div>
        </section>

        {/* 3b) Für Unternehmen: Sicherheit, Zahlen, Enterprise-Kontakt */}
        <section id="unternehmen" className="scroll-mt-24 border-t border-[#e8e1d2] px-6 py-24">
          <div className="mx-auto max-w-6xl">
            <div className="mx-auto max-w-2xl text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">Für Unternehmen gebaut</p>
              <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Professionell. Sicher. Sofort einsatzbereit.
              </h2>
            </div>

            {/* Zahlenleiste – ehrliche System-Fakten, keine Skill-Zählung */}
            <div className="mt-14 grid grid-cols-2 gap-6 text-center lg:grid-cols-4">
              {[
                ["1000", "Mitarbeitende", "Belegschaft im Enterprise-Ausbau", "from-[#ff8c2a] to-[#ff5f1f]"],
                ["9", "KI-Modelle", "Ein Rat führender Modelle unter einem Boss", "from-[#6d5efc] to-[#8b5cf6]"],
                ["24/7", "im Einsatz", "Autopilot erledigt wiederkehrende Aufträge", "from-[#2dd4bf] to-[#0f766e]"],
                ["100", "Quality-Score", "Jedes Ergebnis geprüft, bevor Sie es sehen", "from-[#f472b6] to-[#be185d]"],
              ].map(([wert, label, note, grad]) => (
                <div key={label} className="acc-card acc-card-hover rounded-2xl p-6">
                  <p className={`bg-gradient-to-r ${grad} bg-clip-text text-4xl font-bold text-transparent`}>
                    {wert}
                  </p>
                  <p className="mt-1 font-semibold">{label}</p>
                  <p className="mt-1 text-xs text-[#8d8172]">{note}</p>
                </div>
              ))}
            </div>

            {/* Sicherheits-Argumente */}
            <div className="mt-8 grid gap-6 sm:grid-cols-3">
              {[
                [
                  "Datensparsamkeit ab Werk",
                  "Ihre Arbeitsdaten bleiben in Ihrem Browser statt auf fremden Servern – mit Export und Löschung per Klick. Das ist gelebter Datenschutz, nicht nur ein Versprechen.",
                ],
                [
                  "Fälschungssichere Lizenzen",
                  "Signierte Lizenzschlüssel und Tageslimits nach Industriestandard (HMAC-SHA256). Verschlüsselte Übertragung auf jedem Weg.",
                ],
                [
                  "Ehrliche Enterprise-Roadmap",
                  "Was live ist, ist live. Was pro Kunde eingerichtet wird (ERP/CRM-Anbindung, SSO, On-Premise), sagen wir offen – und setzen es gemeinsam mit Ihnen um.",
                ],
              ].map(([titel, text]) => (
                <div key={titel} className="acc-card rounded-2xl p-6">
                  <h3 className="font-semibold">{titel}</h3>
                  <p className="mt-2 text-sm leading-6 text-[#6f6557]">{text}</p>
                </div>
              ))}
            </div>

            {/* Enterprise-Kontakt */}
            <div className="mt-10 flex flex-col items-center justify-between gap-4 rounded-2xl border border-[#ffb066]/40 bg-gradient-to-br from-[#fff4e6] to-white p-8 sm:flex-row">
              <div>
                <h3 className="text-lg font-semibold">
                  Grösseres Vorhaben? Sprechen wir darüber.
                </h3>
                <p className="mt-1 text-sm text-[#6f6557]">
                  Enterprise ab 8&apos;900 CHF/Monat: eigene Integrationen, private Umgebung,
                  persönliche Einrichtung und Begleitung.
                </p>
              </div>
              <a
                href="mailto:beamswiss@gmail.com?subject=Enterprise-Anfrage%20AI%20Command%20Center"
                className="shop-btn shrink-0 rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-6 py-3 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
              >
                Gespräch vereinbaren
              </a>
            </div>
          </div>
        </section>

        {/* 4) Vertrauens-Leiste */}
        <section className="border-t border-[#e8e1d2] px-6 py-16">
          <div className="mx-auto grid max-w-6xl gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {TRUST.map((t) => (
              <div key={t.label} className="text-center">
                <p className="text-base font-semibold">{t.label}</p>
                <p className="mt-1 text-sm text-[#8d8172]">{t.note}</p>
              </div>
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section className="border-t border-[#e8e1d2] px-6 py-24">
          <div className="mx-auto max-w-3xl">
            <div className="text-center">
              <p className="mb-4 text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">FAQ</p>
              <h2 className="text-3xl font-semibold tracking-tight">
                Häufige Fragen
              </h2>
            </div>
            <div className="mt-10 space-y-3">
              {FAQ.map((item) => (
                <details
                  key={item.q}
                  className="acc-card group rounded-2xl px-6 py-4"
                >
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-base font-semibold [&::-webkit-details-marker]:hidden">
                    {item.q}
                    <svg viewBox="0 0 20 20" className="h-5 w-5 shrink-0 text-[#ff8c2a] transition-transform group-open:rotate-45" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
                      <path d="M10 4v12M4 10h12" strokeLinecap="round" />
                    </svg>
                  </summary>
                  <p className="mt-3 leading-7 text-[#6f6557]">{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        {/* Abschluss-CTA */}
        <section className="px-6 pb-28">
          <div className="acc-card mx-auto max-w-4xl rounded-2xl px-8 py-14 text-center sm:px-14">
            <h2 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
              Starten Sie mit der kostenlosen <span className="acc-grad-text">Demo</span>
            </h2>
            <p className="mx-auto mt-4 max-w-xl text-lg text-[#6f6557]">
              Lernen Sie Ihr KI-Team kennen, bevor Sie sich entscheiden. Ohne Kreditkarte,
              monatlich kündbar, jederzeit erweiterbar.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
              <Link
                href="/dashboard"
                className="shop-btn inline-flex h-12 items-center justify-center rounded-full bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-8 text-base font-bold text-white shadow-[0_10px_30px_-8px_rgba(255,110,30,0.55)]"
              >
                Kostenlos testen
              </Link>
              <a
                href="#abos"
                className="shop-btn inline-flex h-12 items-center justify-center rounded-full border border-[#e0d8c6] bg-white/70 px-8 text-base font-semibold text-[#4a4335] hover:border-[#ffb066]"
              >
                Abos ansehen
              </a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#e8e1d2] px-6 py-10">
        <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-6 sm:flex-row">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" aria-hidden="true" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-6 text-sm">
            <a href="#abos" className="font-medium text-[#6f6557] hover:text-[#1c1917]">
              Abos
            </a>
            <Link href="/integrationen" className="font-medium text-[#6f6557] hover:text-[#1c1917]">
              Integrationen ansehen
            </Link>
            <Link href="/dashboard" className="font-medium text-[#6f6557] hover:text-[#1c1917]">
              Dashboard
            </Link>
          </div>
          <p className="text-sm text-[#a89c8a]">Schweizer Anbieter</p>
        </div>
      </footer>
    </div>
  );
}
