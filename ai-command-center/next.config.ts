import type { NextConfig } from "next";

/**
 * Sicherheits-Header für JEDE Antwort der Plattform (Header-Wächter):
 * - X-Frame-Options / frame-ancestors: kein Einbetten in fremde Seiten
 *   (Schutz vor Clickjacking).
 * - X-Content-Type-Options: Browser dürfen Inhalte nicht umdeuten
 *   (Schutz vor MIME-Sniffing-Angriffen).
 * - Referrer-Policy: keine internen Pfade an fremde Seiten verraten.
 * - Permissions-Policy: Kamera/Mikrofon/Standort bleiben grundsätzlich aus.
 * - HSTS: Browser erzwingen HTTPS für künftige Besuche.
 * - CSP (gezielt): keine Plugins, keine fremden Einbettungen, base-uri fix.
 */
const SICHERHEITS_HEADER = [
  { key: "X-Frame-Options", value: "DENY" },
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
  { key: "Strict-Transport-Security", value: "max-age=63072000; includeSubDomains" },
  {
    key: "Content-Security-Policy",
    value: "frame-ancestors 'none'; object-src 'none'; base-uri 'self'",
  },
];

const nextConfig: NextConfig = {
  // pdf-parse/pdfjs-dist laden ihren Worker zur Laufzeit per Dateipfad –
  // nicht bundeln, sondern aus node_modules auflösen (POST /api/extract).
  serverExternalPackages: ["pdf-parse", "pdfjs-dist"],
  async headers() {
    return [{ source: "/:path*", headers: SICHERHEITS_HEADER }];
  },
};

export default nextConfig;
