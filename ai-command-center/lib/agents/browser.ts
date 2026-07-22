/**
 * Eingebauter KI-Browser: Web-Recherche für Missionen.
 *
 * Die Belegschaft recherchiert vor der Arbeit selbstständig im Web:
 * Suche über DuckDuckGo (HTML-Endpunkt, kein API-Schlüssel nötig),
 * danach werden die Top-Quellen gelesen, von HTML befreit und gekürzt.
 *
 * Sicherheit:
 * - Ergebnisse sind DATEN, keine Anweisungen – sie werden im Orchestrator
 *   als abgegrenzter Datenblock an die USER-Messages gehängt (nie an
 *   System-Prompts), gleiches Muster wie die Dokumenten-Analyse.
 * - Nur http(s)-Ziele, ein Abruf pro Host, harte Timeouts, harte
 *   Längen-Kappung. Fehler einzelner Quellen brechen nichts ab.
 *
 * Stufen: Jedes Abo hat den Browser; höhere Stufen lesen mehr Quellen.
 */

import { lookup } from "node:dns/promises";
import type { PlanId } from "./types";

export interface RechercheQuelle {
  titel: string;
  url: string;
  auszug: string;
}

/** Wie viele Web-Quellen der Browser pro Mission liest (je Abo-Stufe). */
export const RECHERCHE_QUELLEN: Record<PlanId, number> = {
  FREE: 2,
  PERSONAL: 3,
  STARTER: 4,
  PROFESSIONAL: 6,
  BUSINESS: 8,
  ENTERPRISE: 10,
};

const SUCHE_TIMEOUT_MS = 8_000;
const SEITE_TIMEOUT_MS = 6_000;
/** Kappung pro Quelle und für die Recherche insgesamt (Prompt-Budget). */
const MAX_AUSZUG_ZEICHEN = 3_000;
const MAX_GESAMT_ZEICHEN = 16_000;
const USER_AGENT =
  "Mozilla/5.0 (compatible; AI-Command-Center-Research/1.0)";

/** HTML zu lesbarem Text: Skripte/Styles raus, Tags raus, Whitespace glätten. */
function htmlZuText(html: string): string {
  return html
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<noscript[\s\S]*?<\/noscript>/gi, " ")
    .replace(/<(nav|header|footer|aside)[\s\S]*?<\/\1>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

/** Maximal so viele Weiterleitungen folgen wir (jede wird neu geprüft). */
const MAX_REDIRECTS = 4;

/**
 * SSRF-Schutz: private/interne IP-Bereiche, Loopback und Link-Local
 * (inkl. Cloud-Metadaten 169.254.169.254) sind als Ziel verboten.
 */
function istPrivateIp(ip: string): boolean {
  const v4 = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(ip);
  if (v4) {
    const a = Number(v4[1]);
    const b = Number(v4[2]);
    if (a === 0 || a === 10 || a === 127) return true; // this-net, privat, loopback
    if (a === 169 && b === 254) return true; // Link-Local + Cloud-Metadaten
    if (a === 172 && b >= 16 && b <= 31) return true; // privat
    if (a === 192 && b === 168) return true; // privat
    if (a === 100 && b >= 64 && b <= 127) return true; // CGNAT
    return false;
  }
  const ip6 = ip.toLowerCase();
  if (ip6 === "::1" || ip6 === "::") return true; // Loopback / unspezifiziert
  if (ip6.startsWith("::ffff:")) return istPrivateIp(ip6.slice(7)); // v4-mapped
  if (ip6.startsWith("fe80")) return true; // Link-Local
  if (/^f[cd]/.test(ip6)) return true; // Unique-Local fc00::/7
  return false;
}

/**
 * Prüft, ob eine URL ein erlaubtes, externes http(s)-Ziel ist. Hostnamen
 * werden per DNS aufgelöst und ALLE Adressen geprüft (Schutz auch gegen
 * DNS-Rebinding auf interne Adressen).
 */
async function istErlaubtesZiel(rawUrl: string): Promise<boolean> {
  let u: URL;
  try {
    u = new URL(rawUrl);
  } catch {
    return false;
  }
  if (u.protocol !== "http:" && u.protocol !== "https:") return false;
  const host = u.hostname.replace(/^\[|\]$/g, "").toLowerCase();
  if (!host) return false;
  if (
    host === "localhost" ||
    host.endsWith(".localhost") ||
    host.endsWith(".local") ||
    host.endsWith(".internal")
  ) {
    return false;
  }
  // Host ist bereits ein IP-Literal?
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(host) || host.includes(":")) {
    return !istPrivateIp(host);
  }
  // Hostname: auflösen und jede Adresse prüfen.
  try {
    const adressen = await lookup(host, { all: true });
    return adressen.length > 0 && adressen.every((a) => !istPrivateIp(a.address));
  } catch {
    return false;
  }
}

/**
 * Sicherer HTML/Text-Abruf mit Timeout. Weiterleitungen werden MANUELL
 * verfolgt und bei jedem Sprung erneut gegen die SSRF-Regeln geprüft,
 * damit ein Redirect nicht auf ein internes Ziel führen kann.
 */
async function fetchMitTimeout(url: string, timeoutMs: number): Promise<string | null> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    let ziel = url;
    for (let hop = 0; hop <= MAX_REDIRECTS; hop++) {
      if (!(await istErlaubtesZiel(ziel))) return null;
      const res = await fetch(ziel, {
        signal: controller.signal,
        headers: { "User-Agent": USER_AGENT, Accept: "text/html,*/*" },
        redirect: "manual",
      });
      // Weiterleitung: Location auflösen und erneut prüfen.
      if (res.status >= 300 && res.status < 400) {
        const loc = res.headers.get("location");
        if (!loc) return null;
        ziel = new URL(loc, ziel).toString();
        continue;
      }
      if (!res.ok) return null;
      const typ = res.headers.get("content-type") ?? "";
      if (!typ.includes("text/html") && !typ.includes("text/plain") && !typ.includes("json")) return null;
      return await res.text();
    }
    return null; // zu viele Weiterleitungen
  } catch {
    return null;
  } finally {
    clearTimeout(timer);
  }
}

/** DuckDuckGo-HTML-Suche (Backend 1). */
async function sucheDuckDuckGo(query: string): Promise<{ titel: string; url: string }[]> {
  const html = await fetchMitTimeout(
    `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`,
    SUCHE_TIMEOUT_MS,
  );
  if (!html) return [];
  const treffer: { titel: string; url: string }[] = [];
  // Ergebnis-Links: <a class="result__a" href="...uddg=<encodiertes Ziel>...">Titel</a>
  const re = /<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) && treffer.length < 24) {
    let ziel = m[1];
    const uddg = /[?&]uddg=([^&]+)/.exec(ziel);
    if (uddg) {
      try {
        ziel = decodeURIComponent(uddg[1]);
      } catch {
        continue;
      }
    }
    if (!/^https?:\/\//i.test(ziel)) continue;
    const titel = htmlZuText(m[2]).slice(0, 120);
    if (titel) treffer.push({ titel, url: ziel });
  }
  return treffer;
}

/** Bing-HTML-Suche (Backend 2, falls DuckDuckGo blockt). */
async function sucheBing(query: string): Promise<{ titel: string; url: string }[]> {
  const html = await fetchMitTimeout(
    `https://www.bing.com/search?q=${encodeURIComponent(query)}&count=20`,
    SUCHE_TIMEOUT_MS,
  );
  if (!html) return [];
  const treffer: { titel: string; url: string }[] = [];
  // Organische Treffer: <li class="b_algo">…<h2><a href="URL">Titel</a>
  const re = /<li class="b_algo"[\s\S]*?<h2[^>]*>\s*<a[^>]*href="(https?:\/\/[^"]+)"[^>]*>([\s\S]*?)<\/a>/gi;
  let m: RegExpExecArray | null;
  while ((m = re.exec(html)) && treffer.length < 24) {
    const url = m[1];
    // Bing-eigene Redirect-/Werbelinks überspringen.
    if (/bing\.com|microsoft\.com\/bing/i.test(url)) continue;
    const titel = htmlZuText(m[2]).slice(0, 120);
    if (titel) treffer.push({ titel, url });
  }
  return treffer;
}

/** Wikipedia-Suche (Backend 3 – liefert immer belastbare Grundlagen). */
async function sucheWikipedia(query: string): Promise<{ titel: string; url: string }[]> {
  const treffer: { titel: string; url: string }[] = [];
  for (const wiki of ["de", "en"]) {
    const json = await fetchMitTimeout(
      `https://${wiki}.wikipedia.org/w/api.php?action=opensearch&search=${encodeURIComponent(
        query.slice(0, 100),
      )}&limit=5&format=json`,
      SUCHE_TIMEOUT_MS,
    );
    if (!json) continue;
    try {
      const [, titelListe, , urls] = JSON.parse(json) as [string, string[], string[], string[]];
      for (let i = 0; i < titelListe.length && i < urls.length; i++) {
        treffer.push({ titel: `${titelListe[i]} (Wikipedia)`, url: urls[i] });
      }
    } catch {
      /* unerwartetes Format */
    }
    if (treffer.length >= 5) break;
  }
  return treffer;
}

/**
 * Suche mit Fallback-Kette: DuckDuckGo -> Bing -> Wikipedia.
 * Je nach Netz/Umgebung ist mal das eine, mal das andere erreichbar –
 * der Browser liefert dadurch praktisch immer Quellen.
 */
async function webSuche(query: string): Promise<{ titel: string; url: string }[]> {
  for (const backend of [sucheDuckDuckGo, sucheBing, sucheWikipedia]) {
    try {
      const treffer = await backend(query);
      if (treffer.length) return treffer;
    } catch {
      /* naechstes Backend */
    }
  }
  return [];
}

/**
 * Führt die Web-Recherche für eine Mission aus: sucht, wählt maximal
 * `maxQuellen` Treffer (ein Abruf pro Host), liest und kürzt die Seiten.
 * `onQuelle` meldet jede gelesene Quelle für die Live-Aktivität.
 */
export async function webRecherche(
  query: string,
  maxQuellen: number,
  onQuelle?: (q: { titel: string; url: string }) => void,
): Promise<RechercheQuelle[]> {
  const suchbegriff = query.replace(/\s+/g, " ").trim().slice(0, 300);
  if (!suchbegriff || maxQuellen < 1) return [];

  const treffer = await webSuche(suchbegriff);
  // Ein Abruf pro Host: breitere Abdeckung, keine Doppel-Quellen.
  const gesehen = new Set<string>();
  const auswahl: { titel: string; url: string }[] = [];
  for (const t of treffer) {
    try {
      const host = new URL(t.url).hostname.replace(/^www\./, "");
      if (gesehen.has(host)) continue;
      gesehen.add(host);
      auswahl.push(t);
    } catch {
      /* unbrauchbare URL */
    }
    if (auswahl.length >= maxQuellen) break;
  }

  const gelesen = await Promise.all(
    auswahl.map(async (t) => {
      onQuelle?.(t);
      const html = await fetchMitTimeout(t.url, SEITE_TIMEOUT_MS);
      if (!html) return null;
      const text = htmlZuText(html).slice(0, MAX_AUSZUG_ZEICHEN);
      if (text.length < 200) return null; // leere/wertlose Seite
      return { titel: t.titel, url: t.url, auszug: text };
    }),
  );

  const quellen: RechercheQuelle[] = [];
  let gesamt = 0;
  for (const q of gelesen) {
    if (!q) continue;
    if (gesamt + q.auszug.length > MAX_GESAMT_ZEICHEN) {
      q.auszug = q.auszug.slice(0, Math.max(0, MAX_GESAMT_ZEICHEN - gesamt));
    }
    if (!q.auszug) break;
    gesamt += q.auszug.length;
    quellen.push(q);
  }
  return quellen;
}
