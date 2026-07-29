/**
 * Freigabe & Ausgang – zentrale Freigabe-Station für Mission-Ergebnisse.
 * Server-Wrapper; die Logik läuft clientseitig (localStorage).
 */

import type { Metadata } from "next";
import WorkNav from "@/app/components/WorkNav";
import WorkFooter from "@/app/components/WorkFooter";
import FreigabeClient from "./FreigabeClient";

export const metadata: Metadata = {
  title: "Freigabe & Ausgang | AI Command Center",
  description:
    "Alle Mission-Ergebnisse an einem Ort prüfen, freigeben und kopieren – bevor Sie sie versenden.",
};

export default function FreigabePage() {
  return (
    <div className="acc-page min-h-dvh text-[#1c1917]">
      <div className="mx-auto max-w-5xl px-4 pb-24">
        <header className="flex items-center justify-between border-b border-[#e8e1d2] py-4">
          <div className="flex items-center gap-2.5">
            <span className="inline-block h-3 w-3 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
            <span className="text-sm font-bold">AI Command Center</span>
          </div>
          <WorkNav aktiv="freigabe" variante="hell" />
        </header>
        <div className="pt-10">
          <FreigabeClient />
        </div>
        <WorkFooter variante="hell" />
      </div>
    </div>
  );
}
