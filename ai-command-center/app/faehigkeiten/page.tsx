/**
 * Fähigkeiten – der Skill- und Befehls-Katalog des Systems.
 *
 * Server-gerendert aus lib/skills.ts: alle Slash-Befehle mit Beschreibung,
 * gruppiert nach Kategorie. Jeder Skill startet direkt in der
 * Kommandozentrale (Vorlage vorbefüllt via ?befehl=).
 */

import type { Metadata } from "next";
import Link from "next/link";
import { SKILLS, SKILL_KATEGORIEN } from "@/lib/skills";

export const metadata: Metadata = {
  title: "Fähigkeiten | AI Command Center",
  description:
    "Alle Skills und Befehle der KI-Belegschaft: Websites, Offerten, Kampagnen, Analysen, Businesspläne und mehr – mit einem Befehl ausgeführt.",
};

export default function FaehigkeitenPage() {
  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <nav className="flex items-center gap-4 text-sm text-zinc-400" aria-label="Bereiche">
            <Link href="/dashboard" className="hover:text-[#ffb35c]">Missionen</Link>
            <Link href="/chat" className="hover:text-[#ffb35c]">Kommando</Link>
            <span className="text-[#ffb35c]">Skills</span>
            <Link href="/team" className="hidden hover:text-[#ffb35c] sm:inline">Team</Link>
            <Link href="/berichte" className="hidden hover:text-[#ffb35c] sm:inline">Berichte</Link>
          </nav>
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">Skill-Katalog</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            {SKILLS.length} Fähigkeiten. Ein Befehl genügt.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Jeder Skill ist ein geprüfter Befehl mit strukturierter Vorlage –
            dadurch liefert Ihre Belegschaft zuverlässig vollständige,
            professionelle Ergebnisse. In der Kommandozentrale einfach{" "}
            <span className="font-mono text-[#ffb35c]">/</span> tippen, Befehl
            wählen, Platzhalter ausfüllen, ausführen.
          </p>
        </div>

        {SKILL_KATEGORIEN.map((kat) => (
          <section key={kat} className="mt-10">
            <h2 className="text-xl font-semibold text-white">{kat}</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {SKILLS.filter((s) => s.kategorie === kat).map((s) => (
                <article key={s.befehl} className="hud-panel flex flex-col rounded-xl p-5">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-mono text-sm font-bold text-[#ffb35c]">{s.befehl}</span>
                    <h3 className="truncate font-semibold text-white">{s.name}</h3>
                  </div>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-zinc-400">
                    {s.beschreibung}
                  </p>
                  <Link
                    href={`/chat?befehl=${encodeURIComponent(s.befehl)}`}
                    className="shop-btn mt-4 inline-block self-start rounded-lg border border-[#ff8c2a]/40 bg-[#ff8c2a]/10 px-4 py-2 text-sm font-semibold text-[#ffb35c] hover:bg-[#ff8c2a]/20"
                  >
                    Ausführen
                  </Link>
                </article>
              ))}
            </div>
          </section>
        ))}

        <p className="mt-12 max-w-2xl text-xs leading-relaxed text-zinc-500">
          Dazu kommen die freien Bereiche: eigene Befehle in der{" "}
          <Link href="/chat" className="text-[#ffb35c] hover:underline">Kommandozentrale</Link>, die{" "}
          <Link href="/email" className="text-[#ffb35c] hover:underline">E-Mail-Zentrale</Link>, der{" "}
          <Link href="/workflows" className="text-[#ffb35c] hover:underline">Autopilot</Link> für
          wiederkehrende Aufträge und die{" "}
          <Link href="/dashboard" className="text-[#ffb35c] hover:underline">Missions-Ansicht</Link>{" "}
          mit Live-Organigramm.
        </p>
      </div>
    </div>
  );
}
