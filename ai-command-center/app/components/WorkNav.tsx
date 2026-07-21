/**
 * WorkNav – die einheitliche Bereichs-Navigation der Plattform.
 *
 * Überall dieselben Bereiche in derselben Reihenfolge: 6 Hauptbereiche
 * sichtbar, der Rest im «Mehr»-Menü (reines <details>, kein JS nötig).
 * `variante` passt die Farben an helle bzw. dunkle Seiten an.
 */

import Link from "next/link";

export type BereichId =
  | "missionen"
  | "kommando"
  | "kunden"
  | "email"
  | "skills"
  | "autopilot"
  | "berichte"
  | "analysen"
  | "team"
  | "benutzer"
  | "einstellungen"
  | "integrationen"
  | "status"
  | "sicherheit";

const PRIMAER: { id: BereichId; label: string; href: string }[] = [
  { id: "missionen", label: "Missionen", href: "/dashboard" },
  { id: "kommando", label: "Kommando", href: "/chat" },
  { id: "kunden", label: "Kunden", href: "/kunden" },
  { id: "email", label: "E-Mail", href: "/email" },
  { id: "skills", label: "Skills", href: "/faehigkeiten" },
  { id: "autopilot", label: "Autopilot", href: "/workflows" },
];

const MEHR: { id: BereichId; label: string; href: string }[] = [
  { id: "berichte", label: "Berichte", href: "/berichte" },
  { id: "analysen", label: "Analysen", href: "/analysen" },
  { id: "team", label: "Team", href: "/team" },
  { id: "benutzer", label: "Benutzer", href: "/benutzer" },
  { id: "einstellungen", label: "Einstellungen", href: "/einstellungen" },
  { id: "integrationen", label: "Integrationen", href: "/integrationen" },
  { id: "status", label: "System-Status", href: "/status" },
  { id: "sicherheit", label: "Sicherheit", href: "/sicherheit" },
];

export default function WorkNav({
  aktiv,
  variante,
}: {
  aktiv: BereichId;
  variante: "hell" | "dunkel";
}) {
  const hell = variante === "hell";
  const basis = hell ? "text-[#6f6557]" : "text-zinc-400";
  const hover = hell ? "hover:text-[#c25e0e]" : "hover:text-[#ffb35c]";
  const aktivKlasse = hell ? "font-semibold text-[#c25e0e]" : "font-semibold text-[#ffb35c]";
  const menueBg = hell
    ? "border-[#e8e1d2] bg-white shadow-[0_10px_36px_rgba(40,30,10,0.14)]"
    : "border-[#ff8c2a]/25 bg-[#12100d] shadow-[0_10px_36px_rgba(0,0,0,0.5)]";
  const menueEintrag = hell
    ? "text-[#4a4335] hover:bg-[#fff4e6] hover:text-[#c25e0e]"
    : "text-zinc-300 hover:bg-[#ff8c2a]/10 hover:text-[#ffb35c]";

  const mehrAktiv = MEHR.some((m) => m.id === aktiv);

  return (
    <nav className={`flex items-center gap-4 text-sm ${basis}`} aria-label="Bereiche">
      {PRIMAER.map((b, i) =>
        b.id === aktiv ? (
          <span key={b.id} className={aktivKlasse} aria-current="page">
            {b.label}
          </span>
        ) : (
          <Link
            key={b.id}
            href={b.href}
            className={`${hover} ${i > 2 ? "hidden lg:inline" : i > 1 ? "hidden sm:inline" : ""}`}
          >
            {b.label}
          </Link>
        ),
      )}
      <details className="group relative">
        <summary
          className={`flex cursor-pointer list-none items-center gap-1 ${mehrAktiv ? aktivKlasse : hover}`}
        >
          Mehr
          <svg viewBox="0 0 12 12" className="h-3 w-3 transition-transform group-open:rotate-180" aria-hidden="true">
            <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </summary>
        <div className={`absolute right-0 z-50 mt-2 w-44 overflow-hidden rounded-xl border py-1.5 ${menueBg}`}>
          {MEHR.map((b) =>
            b.id === aktiv ? (
              <span key={b.id} className={`block px-4 py-2 ${aktivKlasse}`} aria-current="page">
                {b.label}
              </span>
            ) : (
              <Link key={b.id} href={b.href} className={`block px-4 py-2 ${menueEintrag}`}>
                {b.label}
              </Link>
            ),
          )}
        </div>
      </details>
    </nav>
  );
}
