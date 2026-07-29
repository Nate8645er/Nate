import type { Metadata } from "next";
import PreiseClient from "./PreiseClient";

export const metadata: Metadata = {
  title: "Preise – AI Command Center",
  description:
    "Ihre KI-Abteilung ab Tag 1. Pakete Basic, Pro und Enterprise – für Einzelunternehmer bis Grosskonzern. Kein Chatbot, sondern echte Ergebnisse.",
};

export default function PreisePage() {
  return (
    <main className="bg-[#fdfbf7] text-[#1c1917]">
      <PreiseClient />
    </main>
  );
}
