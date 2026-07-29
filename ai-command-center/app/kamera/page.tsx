import type { Metadata } from "next";
import KameraClient from "./KameraClient";

export const metadata: Metadata = {
  title: "Kamera & Bild – AI Command Center",
  description: "Foto aufnehmen oder Bild hochladen und von der KI auswerten lassen.",
};

export default function KameraPage() {
  return (
    <main className="min-h-screen bg-[#fdfbf7] px-6 py-16 text-[#1c1917]">
      <KameraClient />
    </main>
  );
}
