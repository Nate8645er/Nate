import type { Metadata } from "next";
import { Geist, Geist_Mono, Space_Grotesk, Sora, Inter } from "next/font/google";
import "./globals.css";

// display:"swap" + Fallback: Text bleibt sichtbar (System-Schrift), falls ein
// Web-Font-Fetch beim Boot langsam ist oder fehlschlägt – kein Blank/500.
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "arial"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap",
  fallback: ["ui-monospace", "monospace"],
});

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
  display: "swap",
  fallback: ["system-ui", "arial"],
});

// Neues Marken-Schriftpaar (dunkler Premium-Shop): Sora für Überschriften,
// Inter für Fliesstext. display:"swap" + Fallback = kein Blank beim Boot.
const sora = Sora({
  variable: "--font-sora",
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  display: "swap",
  fallback: ["system-ui", "arial"],
});

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "arial"],
});

export const metadata: Metadata = {
  title: "AI Command Center – Ihre komplette KI-Abteilung im Abo",
  description:
    "Die erste digitale KI-Belegschaft für Unternehmen: Missionen starten, " +
    "fertige Ergebnisse erhalten. Monatlich kündbar, Schweizer Anbieter.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      className={`${geistSans.variable} ${geistMono.variable} ${spaceGrotesk.variable} ${sora.variable} ${inter.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
