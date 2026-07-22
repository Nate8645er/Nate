/**
 * Fähigkeiten – der Skill- und Befehls-Katalog des Systems.
 *
 * Server-gerendert aus lib/skills.ts: alle Slash-Befehle mit Beschreibung,
 * gruppiert nach Kategorie. Jeder Skill startet direkt in der
 * Kommandozentrale (Vorlage vorbefüllt via ?befehl=). Helles Design (2026):
 * Fähigkeiten werden BESCHRIEBEN – wofür sie da sind –, nicht als Zahl gezählt.
 */

import type { Metadata } from "next";
import Link from "next/link";
import { SKILLS, SKILL_KATEGORIEN, SKILL_AB_STUFE, STUFEN_REIHENFOLGE } from "@/lib/skills";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

export const metadata: Metadata = {
  title: "Fähigkeiten | AI Command Center",
  description:
    "Alle Skills und Befehle der KI-Belegschaft: Websites, Offerten, Kampagnen, Analysen, Businesspläne und mehr – mit einem Befehl ausgeführt.",
};

export default function FaehigkeitenPage() {
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="skills" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
            Skill-Katalog
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            Was Ihre <span className="acc-grad-text">KI-Belegschaft</span> für Sie erledigt.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
            Jeder Skill ist ein geprüfter Befehl mit strukturierter Vorlage –
            dadurch liefert Ihre Belegschaft zuverlässig vollständige,
            professionelle Ergebnisse. In der Kommandozentrale einfach{" "}
            <span className="font-mono font-semibold text-[#c25e0e]">/</span> tippen,
            Befehl wählen, Platzhalter ausfüllen, ausführen.
          </p>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#6f6557]">
            Ein System, sechs Ausbaustufen – jede Stufe erweitert, wofür Ihre
            Belegschaft zuständig ist:{" "}
            {STUFEN_REIHENFOLGE.map((st, i) => (
              <span key={st}>
                {i > 0 && " · "}
                <span className="font-semibold text-[#c25e0e]">{st}</span>
              </span>
            ))}
            . Höhere Stufen enthalten immer alles aus den tieferen.
          </p>
        </div>

        {SKILL_KATEGORIEN.map((kat) => (
          <section key={kat} className="mt-10">
            <h2 className="text-xl font-semibold tracking-tight">{kat}</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {SKILLS.filter((s) => s.kategorie === kat).map((s) => (
                <article key={s.befehl} className="acc-card acc-card-hover flex flex-col rounded-2xl p-5">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-mono text-sm font-bold text-[#c25e0e]">{s.befehl}</span>
                    <h3 className="truncate font-semibold">{s.name}</h3>
                  </div>
                  <p className="mt-1.5">
                    <span className="rounded-full border border-[#ffb066]/40 bg-[#fff4e6] px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#c25e0e]">
                      {(SKILL_AB_STUFE[s.befehl] ?? "FREE") === "FREE" ? "In jedem Abo" : `ab ${SKILL_AB_STUFE[s.befehl]}`}
                    </span>
                  </p>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-[#6f6557]">
                    {s.beschreibung}
                  </p>
                  <Link
                    href={`/chat?befehl=${encodeURIComponent(s.befehl)}`}
                    className="shop-btn mt-4 inline-block self-start rounded-xl bg-gradient-to-r from-[#ff8c2a] to-[#ff5f1f] px-4 py-2 text-sm font-bold text-white shadow-[0_6px_20px_-6px_rgba(255,110,30,0.5)]"
                  >
                    Ausführen
                  </Link>
                </article>
              ))}
            </div>
          </section>
        ))}

        <p className="mt-12 max-w-2xl text-xs leading-relaxed text-[#6f6557]">
          Dazu kommen die freien Bereiche: eigene Befehle in der{" "}
          <Link href="/chat" className="font-semibold text-[#c25e0e] hover:underline">Kommandozentrale</Link>, die{" "}
          <Link href="/email" className="font-semibold text-[#c25e0e] hover:underline">E-Mail-Zentrale</Link>, der{" "}
          <Link href="/workflows" className="font-semibold text-[#c25e0e] hover:underline">Autopilot</Link> für
          wiederkehrende Aufträge und die{" "}
          <Link href="/dashboard" className="font-semibold text-[#c25e0e] hover:underline">Missions-Ansicht</Link>{" "}
          mit Live-Organigramm.
        </p>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
