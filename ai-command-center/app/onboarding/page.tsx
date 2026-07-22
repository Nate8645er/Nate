/**
 * Einrichtungs- & Video-Onboarding-Bereich (/onboarding).
 *
 * Persönlicher Bereich nach dem Kauf: Übersichtsvideo, tarifspezifisches
 * Tutorial (modular/versioniert) und eine interaktive Checkliste mit Tooltips,
 * die durch Einrichtung, Dienst-Anbindung, Agenten-Setup, Dashboard und
 * Automationen führt. Inhalte zentral in lib/onboarding.ts gepflegt.
 */

import type { Metadata } from "next";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import OnboardingClient from "./OnboardingClient";

export const metadata: Metadata = {
  title: "Einrichtung & Video-Tutorials | AI Command Center",
  description:
    "Ihr persönlicher Einrichtungs-Bereich: Video-Tutorials pro Abo, interaktive Checklisten und Tooltips – vom Zugang über die Dienst-Anbindung bis zu Automationen.",
};

export default function OnboardingPage() {
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="onboarding" variante="hell" />
        </header>

        <div className="acc-in pt-10">
          <p className="text-[11px] font-bold uppercase tracking-wider text-[#c25e0e]">
            Einrichtung & Tutorials
          </p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight sm:text-4xl">
            In wenigen Schritten <span className="acc-grad-text">startklar</span>
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-[#8d8172]">
            Ihr persönlicher Einrichtungs-Bereich: Sehen Sie im Video, wie das System
            funktioniert, und haken Sie die Schritte für Ihren Tarif nacheinander ab –
            von Zugang und Firma über die Anbindung Ihrer Dienste bis zu den ersten
            Automationen. Ihr Fortschritt wird in diesem Browser gespeichert.
          </p>
        </div>

        <OnboardingClient />

        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
