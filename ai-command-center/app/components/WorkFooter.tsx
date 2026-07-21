/**
 * WorkFooter – der einheitliche Seitenabschluss der Arbeitsbereiche.
 * Kompakt: Markenzeile, wichtige Querlinks, Vertrauenshinweis.
 * `variante` passt die Farben an helle bzw. dunkle Seiten an.
 */

import Link from "next/link";

export default function WorkFooter({ variante }: { variante: "hell" | "dunkel" }) {
  const hell = variante === "hell";
  const rahmen = hell ? "border-[#e8e1d2]" : "border-[#ff8c2a]/15";
  const text = hell ? "text-[#8d8172]" : "text-zinc-500";
  const link = hell ? "hover:text-[#c25e0e]" : "hover:text-[#ffb35c]";
  return (
    <footer className={`mt-16 border-t ${rahmen} py-6 text-xs ${text}`}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-gradient-to-br from-[#ffb066] to-[#ff5f1f]" />
          AI Command Center · Schweizer Anbieter · © {new Date().getFullYear()}
        </p>
        <nav className="flex flex-wrap items-center gap-4" aria-label="Fusszeile">
          <Link href="/status" className={link}>System-Status</Link>
          <Link href="/sicherheit" className={link}>Sicherheit</Link>
          <Link href="/faehigkeiten" className={link}>Skills</Link>
          <a href="mailto:beamswiss@gmail.com" className={link}>Kontakt</a>
        </nav>
      </div>
      <p className="mt-2">
        Alle Ergebnisse gehören Ihnen. Arbeitsdaten bleiben in Ihrem Browser –
        Export und Löschung unter Einstellungen.
      </p>
    </footer>
  );
}
