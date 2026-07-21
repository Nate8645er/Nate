/**
 * WorkNav – die einheitliche Bereichs-Navigation der Plattform (2026).
 *
 * Schwebende Glas-Pill-Leiste: 6 Hauptbereiche sichtbar, der Rest im
 * «Mehr»-Menü (reines <details>, kein JS nötig). Der aktive Bereich
 * bekommt eine Verlaufs-Pille. `variante` passt die Farben an helle
 * bzw. dunkle Seiten an.
 */

import Link from "next/link";

export type BereichId =
  | "missionen"
  | "kommando"
  | "kunden"
  | "email"
  | "skills"
  | "werkzeuge"
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
  { id: "werkzeuge", label: "Blitz-Werkzeuge", href: "/werkzeuge" },
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
  const leiste = hell
    ? "border-[#1c1917]/8 bg-white/60 shadow-[0_2px_16px_-8px_rgba(28,25,23,0.2),inset_0_1px_0_rgba(255,255,255,0.9)]"
    : "border-white/10 bg-white/5 shadow-[0_2px_16px_-8px_rgba(0,0,0,0.6),inset_0_1px_0_rgba(255,255,255,0.08)]";
  const eintrag = hell
    ? "text-[#6f6557] hover:bg-[#1c1917]/5 hover:text-[#1c1917]"
    : "text-zinc-400 hover:bg-white/8 hover:text-white";
  const aktivPille =
    "bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] font-semibold text-white shadow-[0_4px_14px_-4px_rgba(255,110,30,0.6)]";
  const menueBg = hell
    ? "border-[#1c1917]/8 bg-white/85 shadow-[0_16px_44px_-16px_rgba(28,25,23,0.28)]"
    : "border-white/10 bg-[#14100c]/90 shadow-[0_16px_44px_-8px_rgba(0,0,0,0.7)]";
  const menueEintrag = hell
    ? "text-[#4a4335] hover:bg-[#ff8c2a]/10 hover:text-[#c25e0e]"
    : "text-zinc-300 hover:bg-[#ff8c2a]/12 hover:text-[#ffb35c]";

  const mehrAktiv = MEHR.some((m) => m.id === aktiv);
  const pill = "rounded-full px-3 py-1.5 transition-colors";

  return (
    <nav
      className={`flex items-center gap-0.5 rounded-full border p-1 text-[13px] backdrop-blur-xl ${leiste}`}
      aria-label="Bereiche"
    >
      {PRIMAER.map((b, i) =>
        b.id === aktiv ? (
          <span key={b.id} className={`${pill} ${aktivPille}`} aria-current="page">
            {b.label}
          </span>
        ) : (
          <Link
            key={b.id}
            href={b.href}
            className={`${pill} ${eintrag} ${i > 2 ? "hidden lg:inline-block" : i > 1 ? "hidden sm:inline-block" : ""}`}
          >
            {b.label}
          </Link>
        ),
      )}
      <details className="group relative">
        <summary
          className={`flex cursor-pointer list-none items-center gap-1 ${pill} ${mehrAktiv ? aktivPille : eintrag}`}
        >
          Mehr
          <svg viewBox="0 0 12 12" className="h-3 w-3 transition-transform group-open:rotate-180" aria-hidden="true">
            <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </summary>
        <div
          className={`absolute right-0 z-50 mt-3 w-48 overflow-hidden rounded-2xl border py-1.5 backdrop-blur-xl ${menueBg}`}
        >
          {MEHR.map((b) =>
            b.id === aktiv ? (
              <span key={b.id} className="block px-4 py-2 font-semibold text-[#ff8c2a]" aria-current="page">
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
