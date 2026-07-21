import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // pdf-parse/pdfjs-dist laden ihren Worker zur Laufzeit per Dateipfad –
  // nicht bundeln, sondern aus node_modules auflösen (POST /api/extract).
  serverExternalPackages: ["pdf-parse", "pdfjs-dist"],
};

export default nextConfig;
