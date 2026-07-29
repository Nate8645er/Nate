import type { Metadata } from "next";
import KontoClient from "./KontoClient";

export const metadata: Metadata = {
  title: "Mein Konto – AI Command Center",
  description: "Ihr Abo, Ihr Zugang und die Verwaltung Ihrer KI-Abteilung.",
};

export default function KontoPage() {
  return (
    <main className="min-h-screen bg-[#fdfbf7] px-6 py-16 text-[#1c1917]">
      <KontoClient />
    </main>
  );
}
