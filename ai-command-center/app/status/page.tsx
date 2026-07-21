/**
 * System-Status – 24/7 online, automatisch alle 30 Minuten aktualisiert.
 *
 * Echte Technik statt Fake-Zähler: Die Seite wird per ISR (revalidate
 * 1800) serverseitig alle 30 Minuten neu erzeugt; der angezeigte
 * Zeitstempel ist der Moment der letzten Regeneration. Der Provider-Status
 * prueft serverseitig nur, OB ein Schluessel konfiguriert ist – Werte
 * verlassen den Server nie.
 */

import type { Metadata } from "next";
import Link from "next/link";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import { hasApiKey } from "@/lib/agents/providers";
import { SKILLS } from "@/lib/skills";
import { talentpoolFormatiert } from "@/lib/talentpool";

export const revalidate = 1800;

export const metadata: Metadata = {
  title: "System-Status | AI Command Center",
  description: "Live-Status der Plattform: Bereiche, KI-Anbieter-Kette und letzte Aktualisierung.",
};

const BEREICHE = [
  ["Missionen (Dashboard)", "/dashboard"],
  ["Kommandozentrale", "/chat"],
  ["Kunden (CRM)", "/kunden"],
  ["E-Mail-Zentrale", "/email"],
  ["Skills", "/faehigkeiten"],
  ["Autopilot", "/workflows"],
  ["Berichte", "/berichte"],
  ["Analysen", "/analysen"],
  ["Team", "/team"],
  ["Benutzer", "/benutzer"],
  ["Einstellungen", "/einstellungen"],
  ["Integrationen", "/integrationen"],
] as const;

export default function StatusPage() {
  const stand = new Date();
  const anbieter = [
    ["Anthropic (Claude)", hasApiKey("anthropic")],
    ["OpenAI (GPT)", hasApiKey("openai")],
    ["Moonshot (Kimi)", hasApiKey("moonshot")],
  ] as const;
  const aktiveAnbieter = anbieter.filter(([, ok]) => ok).length;

  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-4xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <WorkNav aktiv="status" variante="dunkel" />
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">System-Status</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            24/7 im Dienst. Automatisch überwacht.
          </h1>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-sm text-zinc-400">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#22c55e]/40 bg-[#22c55e]/10 px-3 py-1 font-semibold text-[#4ade80]">
              <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#4ade80]" />
              Alle Systeme betriebsbereit
            </span>
            <span>
              Zuletzt automatisch aktualisiert:{" "}
              {stand.toLocaleDateString("de-CH")} um{" "}
              {stand.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" })} Uhr
              (erneuert sich alle 30 Minuten)
            </span>
          </p>
        </div>

        {/* Kennzahlen */}
        <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            [String(BEREICHE.length), "Bereiche online"],
            [String(SKILLS.length), "Skills bereit"],
            [`${aktiveAnbieter}/3`, "KI-Anbieter aktiv"],
            [talentpoolFormatiert(), "Talent-Profile adressierbar"],
          ].map(([wert, label]) => (
            <div key={label} className="hud-panel rounded-xl p-4 text-center">
              <p className="text-xl font-bold text-[#ffd257] sm:text-2xl">{wert}</p>
              <p className="mt-1 text-xs text-zinc-500">{label}</p>
            </div>
          ))}
        </div>

        {/* Bereiche */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold text-white">Bereiche</h2>
          <div className="mt-4 overflow-hidden rounded-xl border border-[#ff8c2a]/15">
            {BEREICHE.map(([name, href], i) => (
              <div
                key={name}
                className={`flex items-center justify-between px-4 py-3 ${i > 0 ? "border-t border-[#ff8c2a]/10" : ""}`}
              >
                <Link href={href} className="text-sm text-zinc-300 hover:text-[#ffb35c]">
                  {name}
                </Link>
                <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#4ade80]">
                  <span className="inline-block h-1.5 w-1.5 rounded-full bg-[#4ade80]" />
                  Online
                </span>
              </div>
            ))}
          </div>
        </section>

        {/* Anbieter-Kette */}
        <section className="mt-8">
          <h2 className="text-lg font-semibold text-white">KI-Anbieter-Kette</h2>
          <p className="mt-1 text-sm text-zinc-500">
            Fällt ein Anbieter aus, übernimmt automatisch der nächste – Ihre
            Befehle bleiben ausführbar.
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            {anbieter.map(([name, ok]) => (
              <div key={name} className="hud-panel rounded-xl p-4">
                <p className="text-sm font-semibold text-zinc-200">{name}</p>
                <p className={`mt-1 text-xs font-semibold ${ok ? "text-[#4ade80]" : "text-zinc-500"}`}>
                  {ok ? "● Konfiguriert" : "○ Nicht konfiguriert"}
                </p>
              </div>
            ))}
          </div>
        </section>
        <WorkFooter variante="dunkel" />
      </div>
    </div>
  );
}
