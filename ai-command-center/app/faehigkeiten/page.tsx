/**
 * Fähigkeiten – der Skill- und Befehls-Katalog des Systems.
 *
 * Server-gerendert aus lib/skills.ts: alle Slash-Befehle mit Beschreibung,
 * gruppiert nach Kategorie. Jeder Skill startet direkt in der
 * Kommandozentrale (Vorlage vorbefüllt via ?befehl=).
 */

import type { Metadata } from "next";
import Link from "next/link";
import { SKILLS, SKILL_KATEGORIEN, SKILL_AB_STUFE } from "@/lib/skills";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";

export const metadata: Metadata = {
  title: "Fähigkeiten | AI Command Center",
  description:
    "Alle Skills und Befehle der KI-Belegschaft: Websites, Offerten, Kampagnen, Analysen, Businesspläne und mehr – mit einem Befehl ausgeführt.",
};

export default function FaehigkeitenPage() {
  return (
    <div className="acc-page min-h-dvh text-[#2a2521]">
      
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#1c1917]/10 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#c25e0e]/85">AI Command Center</span>
          </div>
          <WorkNav aktiv="skills" variante="hell" />
        </header>

        <div className="pt-10">
          <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-[#c25e0e]/85 mb-3">Skill-Katalog</p>
          <h1 className="text-3xl font-semibold text-[#1c1917] sm:text-4xl">
            Für jede Aufgabe der richtige Befehl.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#5c5346]">
            Jeder Skill ist ein geprüfter Befehl mit strukturierter Vorlage –
            dadurch liefert Ihre Belegschaft zuverlässig vollständige,
            professionelle Ergebnisse. In der Kommandozentrale einfach{" "}
            <span className="font-mono text-[#c25e0e]">/</span> tippen, Befehl
            wählen, Platzhalter ausfüllen, ausführen.
          </p>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#5c5346]">
            Ein System, sechs Ausbaustufen: Jede Abo-Stufe schaltet weitere
            Skills frei – von den Grundlagen wie{" "}
            <span className="font-semibold text-[#c25e0e]">Website</span>,{" "}
            <span className="font-semibold text-[#c25e0e]">Offerte</span> und{" "}
            <span className="font-semibold text-[#c25e0e]">Dokument</span> in
            jedem Abo über Marketing, Analysen und Kampagnen bis zu
            spezialisierten Business- und Coding-Skills in den höheren Stufen.
            Bei jedem Skill unten steht, ab welcher Stufe er verfügbar ist;
            höhere Stufen enthalten immer alles aus den tieferen.
          </p>
        </div>

        {SKILL_KATEGORIEN.map((kat) => (
          <section key={kat} className="mt-10">
            <h2 className="text-xl font-semibold text-[#1c1917]">{kat}</h2>
            <div className="mt-4 grid gap-4 sm:grid-cols-2">
              {SKILLS.filter((s) => s.kategorie === kat).map((s) => (
                <article key={s.befehl} className="acc-card flex flex-col rounded-xl p-5">
                  <div className="flex items-baseline justify-between gap-2">
                    <span className="font-mono text-sm font-bold text-[#c25e0e]">{s.befehl}</span>
                    <h3 className="truncate font-semibold text-[#1c1917]">{s.name}</h3>
                  </div>
                  <p className="mt-1.5">
                    <span className="rounded-full border border-[#ff8c2a]/30 bg-[#ff8c2a]/8 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[#9a4d12]/85">
                      {(SKILL_AB_STUFE[s.befehl] ?? "FREE") === "FREE" ? "In jedem Abo" : `ab ${SKILL_AB_STUFE[s.befehl]}`}
                    </span>
                  </p>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-[#5c5346]">
                    {s.beschreibung}
                  </p>
                  <Link
                    href={`/chat?befehl=${encodeURIComponent(s.befehl)}`}
                    className="shop-btn mt-4 inline-block self-start rounded-lg border border-[#ff8c2a]/40 bg-[#ff8c2a]/10 px-4 py-2 text-sm font-semibold text-[#c25e0e] hover:bg-[#ff8c2a]/20"
                  >
                    Ausführen
                  </Link>
                </article>
              ))}
            </div>
          </section>
        ))}

        <p className="mt-12 max-w-2xl text-xs leading-relaxed text-[#8d8172]">
          Dazu kommen die freien Bereiche: eigene Befehle in der{" "}
          <Link href="/chat" className="text-[#c25e0e] hover:underline">Kommandozentrale</Link>, die{" "}
          <Link href="/email" className="text-[#c25e0e] hover:underline">E-Mail-Zentrale</Link>, der{" "}
          <Link href="/workflows" className="text-[#c25e0e] hover:underline">Autopilot</Link> für
          wiederkehrende Aufträge und die{" "}
          <Link href="/dashboard" className="text-[#c25e0e] hover:underline">Missions-Ansicht</Link>{" "}
          mit Live-Organigramm.
        </p>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
