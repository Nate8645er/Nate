/**
 * Sicherheit – die 10 Wächter der Plattform.
 *
 * Jeder Wächter ist eine REAL implementierte Schutzschicht, die bei jedem
 * einzelnen Aufruf greift – dadurch ist der Schutz naturgemäss 24/7 aktiv,
 * solange die Plattform läuft. Kein Deko-Zähler: Die Karte nennt pro
 * Wächter den konkreten Mechanismus im Code. Seite regeneriert sich wie
 * die Status-Seite alle 30 Minuten (ISR) mit frischem Prüf-Zeitstempel.
 */

import type { Metadata } from "next";
import Link from "next/link";
import WorkNav from "@/app/components/WorkNav";

export const revalidate = 1800;

export const metadata: Metadata = {
  title: "Sicherheit | AI Command Center",
  description:
    "Die 10 Schutzschichten der Plattform: Lizenzen, Tokens, Injection-Schutz, Sicherheits-Header, Datensparsamkeit – 24/7 aktiv.",
};

const WAECHTER = [
  {
    name: "Lizenz-Wächter",
    schutz: "Gefälschte Zugänge",
    detail:
      "Jeder Lizenzschlüssel ist mit HMAC-SHA256 signiert und wird in konstanter Zeit geprüft (timingSafeEqual) – gefälschte oder erratene Schlüssel prallen ab.",
  },
  {
    name: "Token-Wächter",
    schutz: "Manipulierte Sitzungen",
    detail:
      "Zugangs- und Verbrauchs-Tokens sind serverseitig signiert. Jede Veränderung am Token macht es sofort ungültig – zurück auf FREE.",
  },
  {
    name: "Limit-Wächter",
    schutz: "Missbrauch & Überlastung",
    detail:
      "Tageslimits pro Abo-Stufe werden bei jedem Aufruf serverseitig durchgesetzt. Niemand kann das System leerlaufen lassen oder Kosten explodieren lassen.",
  },
  {
    name: "Injection-Wächter",
    schutz: "Versteckte Befehle in Dokumenten",
    detail:
      "Hochgeladene Dokumente und eingehende E-Mails werden als abgegrenzte Datenblöcke behandelt – nie als Anweisungen. Versteckte Kommandos in einer Kundenmail steuern Ihre KI nicht um.",
  },
  {
    name: "Eingabe-Wächter",
    schutz: "Schadhafte Eingaben",
    detail:
      "Jede API-Eingabe wird validiert, typgeprüft und in der Länge gekappt, bevor sie verarbeitet wird. Unbrauchbares wird abgewiesen statt interpretiert.",
  },
  {
    name: "Transport-Wächter",
    schutz: "Mitlesen unterwegs",
    detail:
      "Sämtlicher Verkehr läuft verschlüsselt über HTTPS/TLS. HSTS zwingt Browser, künftige Besuche nur noch verschlüsselt aufzubauen.",
  },
  {
    name: "Header-Wächter",
    schutz: "Clickjacking & Einbettungs-Tricks",
    detail:
      "Jede Antwort trägt Sicherheits-Header: kein Einbetten in fremde Seiten (frame-ancestors 'none'), kein MIME-Sniffing, keine Plugins, Kamera/Mikrofon/Standort deaktiviert.",
  },
  {
    name: "Daten-Wächter",
    schutz: "Datenlecks",
    detail:
      "Datensparsamkeit ab Werk: Ihre Arbeitsdaten bleiben in Ihrem Browser statt auf fremden Servern – mit Export und Löschung per Klick. Was nicht gespeichert ist, kann nicht gestohlen werden.",
  },
  {
    name: "Geheimnis-Wächter",
    schutz: "Schlüssel-Diebstahl",
    detail:
      "API-Schlüssel und das Lizenz-Geheimnis existieren nur serverseitig als Umgebungsvariablen. Sie erscheinen nie im Browser-Code, nie in Antworten, nie in Fehlermeldungen.",
  },
  {
    name: "Ausfall-Wächter",
    schutz: "Störungen & Ausfälle",
    detail:
      "Drei KI-Anbieter in einer Fallback-Kette, Timeouts und automatische Wiederholung bei Serverfehlern – fällt ein Anbieter aus, übernimmt der nächste.",
  },
];

export default function SicherheitPage() {
  const stand = new Date();
  return (
    <div className="min-h-dvh bg-[#0b0a08] text-zinc-200">
      <div className="hud-texture" aria-hidden="true" />
      <div className="relative z-10 mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#ff8c2a]/15 py-4">
          <div className="flex items-center gap-2">
            <span className="hud-pulse inline-block h-2 w-2 rounded-full bg-[#ff8c2a]" />
            <span className="hud-label">AI Command Center</span>
          </div>
          <WorkNav aktiv="sicherheit" variante="dunkel" />
        </header>

        <div className="pt-10">
          <p className="hud-label mb-3">Sicherheitssystem</p>
          <h1 className="text-3xl font-semibold text-white sm:text-4xl">
            10 Wächter. Bei jedem Aufruf im Dienst.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-zinc-400">
            Jeder Wächter ist eine im Code verankerte Schutzschicht, die bei
            jeder einzelnen Anfrage greift – rund um die Uhr, an jedem Tag.
            Zuletzt automatisch geprüft: {stand.toLocaleDateString("de-CH")} um{" "}
            {stand.toLocaleTimeString("de-CH", { hour: "2-digit", minute: "2-digit" })} Uhr
            (erneuert sich alle 30 Minuten).
          </p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2">
          {WAECHTER.map((w, i) => (
            <article key={w.name} className="hud-panel rounded-xl p-5">
              <div className="flex items-center justify-between gap-2">
                <h2 className="flex items-center gap-2.5 font-semibold text-[#ffb35c]">
                  <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-[#ff8c2a]/30 bg-[#ff8c2a]/10 font-mono text-xs font-bold text-[#ffd257]">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  {w.name}
                </h2>
                <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-[#22c55e]/40 bg-[#22c55e]/10 px-2.5 py-1 text-[11px] font-bold text-[#4ade80]">
                  <span className="hud-pulse inline-block h-1.5 w-1.5 rounded-full bg-[#4ade80]" />
                  24/7 aktiv
                </span>
              </div>
              <p className="mt-2.5 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Schützt vor: {w.schutz}
              </p>
              <p className="mt-2 text-sm leading-relaxed text-zinc-400">{w.detail}</p>
            </article>
          ))}
        </div>

        <p className="mt-8 max-w-2xl rounded-xl border border-[#ff8c2a]/20 bg-[#ff8c2a]/[0.04] px-5 py-4 text-xs leading-relaxed text-[#ffb35c]/90">
          Ehrlich eingeordnet: Diese Wächter schützen die Plattform und Ihre
          Arbeit darin. Sie ersetzen keinen Virenschutz auf Ihren eigenen
          Geräten. Für Grosskunden ergänzen wir als Enterprise-Projekt
          zusätzlich Firewall-Regeln (WAF), Audit-Protokolle, SSO/2FA und
          private Umgebungen –{" "}
          <Link href="/integrationen" className="underline hover:text-white">
            siehe Enterprise-Ausbau
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
