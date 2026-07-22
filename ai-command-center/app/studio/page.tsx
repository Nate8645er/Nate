"use client";

/**
 * KI-Studio – der Browser als KI-Entwicklungsumgebung (erste Version).
 *
 * Eine echte, im Browser laufende Arbeitsplattform für KI-gestützte Arbeit:
 *  - Projekt mit Dateibaum (anlegen, öffnen, umbenennen, löschen), lokal
 *    gespeichert (localStorage acc-studio) – mehrere Dateien gleichzeitig.
 *  - Code-Editor mit Zeilennummern und Syntax-Highlighting (leichtgewichtig,
 *    ohne Fremd-Editor) – Tab-Einrückung, Live-Highlight.
 *  - KI-Assistent (rechts): liest die offene Datei, beantwortet Aufgaben in
 *    natürlicher Sprache (gestreamt über /api/chat) und schlägt Code vor, den
 *    Sie mit einem Klick in die Datei übernehmen.
 *
 * Ehrlich gekennzeichnet: Echtes Terminal, echtes Git und ein Debugger
 * brauchen eine Server-Laufzeit und sind Teil des Enterprise-Ausbaus –
 * hier bewusst als „geplant" markiert, statt es vorzutäuschen.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import WorkNav from "@/app/components/WorkNav";

const STORE = "acc-studio";
const LICENSE_TOKEN_KEY = "acc-license-token";
const USAGE_TOKEN_KEY = "acc-usage-token";
const ULTRA_TOKEN_KEY = "acc-ultra-token";

interface Projekt {
  name: string;
  files: Record<string, string>;
  open: string;
}

const START: Projekt = {
  name: "mein-projekt",
  files: {
    "README.md": "# Mein Projekt\n\nWillkommen im KI-Studio. Öffnen Sie eine Datei\nund bitten Sie den Assistenten rechts um Hilfe.\n",
    "index.ts": 'export function hallo(name: string): string {\n  // Bitten Sie die KI: "Baue eine Begrüssung mit Uhrzeit"\n  return `Hallo, ${name}!`;\n}\n\nconsole.log(hallo("Welt"));\n',
  },
  open: "index.ts",
};

/* Startvorlagen: schnell ein neues Projekt beginnen. Die Web-Vorlagen sind
   direkt in der Live-Vorschau lauffähig. */
const VORLAGEN: { id: string; label: string; hinweis: string; projekt: Projekt }[] = [
  {
    id: "landing",
    label: "Landing-Page",
    hinweis: "HTML + CSS + JS, direkt in der Vorschau lauffähig",
    projekt: {
      name: "landing-page",
      open: "index.html",
      files: {
        "index.html":
          '<!doctype html>\n<html lang="de">\n<head>\n  <meta charset="utf-8">\n  <meta name="viewport" content="width=device-width, initial-scale=1">\n  <title>Meine Firma</title>\n  <link rel="stylesheet" href="style.css">\n</head>\n<body>\n  <header>\n    <h1>Willkommen bei <span>Meine Firma</span></h1>\n    <p>Wir machen Ihr Geschäft schneller, klarer, besser.</p>\n    <button id="cta">Kontakt aufnehmen</button>\n  </header>\n  <script src="app.js"></script>\n</body>\n</html>\n',
        "style.css":
          "* { box-sizing: border-box; margin: 0; }\nbody { font-family: system-ui, sans-serif; background: #0b0a0f; color: #f4f1ea; }\nheader { min-height: 100vh; display: grid; place-content: center; text-align: center; gap: 20px; padding: 24px; }\nh1 { font-size: clamp(28px, 6vw, 56px); }\nh1 span { color: #ff8c2a; }\np { color: #a8a29e; font-size: 18px; }\nbutton { justify-self: center; margin-top: 8px; padding: 12px 26px; border: 0; border-radius: 10px;\n  background: linear-gradient(135deg, #ff8c2a, #ff5f1f); color: #fff; font-weight: 700; font-size: 16px; cursor: pointer; }\n",
        "app.js":
          'document.getElementById("cta").addEventListener("click", () => {\n  alert("Danke! Wir melden uns.");\n});\n',
      },
    },
  },
  {
    id: "python",
    label: "Python-Skript",
    hinweis: "Startgerüst für ein Automations-Skript",
    projekt: {
      name: "python-skript",
      open: "main.py",
      files: {
        "main.py":
          'def main() -> None:\n    """Kurzes Beispiel – bitten Sie die KI, es zu erweitern."""\n    zahlen = [1, 2, 3, 4, 5]\n    print("Summe:", sum(zahlen))\n\n\nif __name__ == "__main__":\n    main()\n',
        "README.md": "# Python-Skript\n\nAusführen: `python main.py`\n",
      },
    },
  },
  {
    id: "api",
    label: "Node-API",
    hinweis: "Minimaler HTTP-Server ohne Framework",
    projekt: {
      name: "node-api",
      open: "server.js",
      files: {
        "server.js":
          'const http = require("http");\n\nconst server = http.createServer((req, res) => {\n  res.setHeader("content-type", "application/json");\n  res.end(JSON.stringify({ ok: true, pfad: req.url }));\n});\n\nserver.listen(3000, () => console.log("API läuft auf http://localhost:3000"));\n',
        "README.md": "# Node-API\n\nStarten: `node server.js`\n",
      },
    },
  },
];

/* ---------- leichtgewichtiges Syntax-Highlighting (sicher, ein Durchgang) ----------
 * Ein kombinierter Tokenizer läuft über den ROHEN Code; jedes Token und jede
 * Lücke werden EINZELN escaped und dann in <span> gepackt. Dadurch matcht keine
 * Regel jemals das HTML, das eine andere eingefügt hat (kein Selbst-Zerfall).
 */
const KW =
  // JS/TS + Python + gängige Web-Sprachen (CSS/HTML/JSON grob abgedeckt).
  "const|let|var|function|return|if|else|for|while|import|export|from|class|extends|new|await|async|try|catch|finally|throw|typeof|interface|type|public|private|static|def|lambda|elif|print|None|True|False|null|true|false|undefined|this|self|struct|enum|switch|case|break|continue|package|func|use|fn|impl|pub|match";
const TOKEN = new RegExp(
  `(\\/\\/[^\\n]*|#[^\\n]*)` + // 1 Kommentar
    `|("(?:[^"\\\\\\n]|\\\\.)*"|'(?:[^'\\\\\\n]|\\\\.)*'|\`(?:[^\`\\\\]|\\\\.)*\`)` + // 2 String
    `|(\\b\\d+(?:\\.\\d+)?\\b)` + // 3 Zahl
    `|(\\b(?:${KW})\\b)`, // 4 Keyword
  "g",
);
function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function highlight(code: string): string {
  let out = "";
  let last = 0;
  let m: RegExpExecArray | null;
  TOKEN.lastIndex = 0;
  while ((m = TOKEN.exec(code))) {
    out += esc(code.slice(last, m.index));
    const t = esc(m[0]);
    if (m[1]) out += `<span class="tk-com">${t}</span>`;
    else if (m[2]) out += `<span class="tk-str">${t}</span>`;
    else if (m[3]) out += `<span class="tk-num">${t}</span>`;
    else out += `<span class="tk-kw">${t}</span>`;
    last = TOKEN.lastIndex;
    if (m.index === TOKEN.lastIndex) TOKEN.lastIndex++; // Endlosschutz
  }
  out += esc(code.slice(last));
  return out;
}

function ext(path: string): string {
  const m = /\.([a-z0-9]+)$/i.exec(path);
  return m ? m[1].toLowerCase() : "";
}

/* Codeblock aus einer KI-Antwort ziehen (erster ```-Block). */
function ersterCodeblock(text: string): string | null {
  const m = /```[a-z0-9]*\n?([\s\S]*?)```/i.exec(text);
  return m ? m[1].replace(/\n$/, "") : null;
}

/* Sieht ein Token wie ein Dateipfad aus (hat eine Endung, keine Leerzeichen)? */
function istPfad(s: string): boolean {
  const t = s.trim();
  return t.length > 0 && t.length <= 120 && /^[\w./-]+\.[a-z0-9]+$/i.test(t);
}
/* Markdown-Dekoration von einer Pfad-Zeile entfernen (**x**, `x`, ### x, - x, x:). */
function saeuberePfad(zeile: string): string {
  return zeile
    .replace(/^#{1,6}\s+/, "")
    .replace(/^[-*]\s+/, "")
    .replace(/[*`]/g, "")
    .replace(/^(datei|file|pfad|path)\s*[:=]?\s*/i, "")
    .replace(/[:：]\s*$/, "")
    .trim();
}
/* Alle ```-Blöcke mit zugehörigem Dateipfad aus einer KI-Antwort ziehen.
   Der Pfad stammt aus der Fence-Info (```ts src/util.ts) oder aus der
   letzten nicht-leeren Zeile vor dem Block (**pfad**, `pfad`, ### pfad …).
   Blöcke ohne erkennbaren Pfad bekommen path=null. */
function dateiBloecke(text: string): { path: string | null; content: string }[] {
  const out: { path: string | null; content: string }[] = [];
  const re = /```([^\n`]*)\n([\s\S]*?)```/g;
  let m: RegExpExecArray | null;
  let letztesEnde = 0;
  while ((m = re.exec(text))) {
    const content = m[2].replace(/\n$/, "");
    let path: string | null = null;
    // 1) Pfad in der Fence-Info-Zeile?
    for (const tok of m[1].trim().split(/\s+/).filter(Boolean)) {
      const c = saeuberePfad(tok);
      if (istPfad(c)) { path = c; break; }
    }
    // 2) sonst letzte nicht-leere Zeile vor dem Block.
    if (!path) {
      const davor = text.slice(letztesEnde, m.index).split("\n").filter((z) => z.trim());
      const kand = davor.length ? saeuberePfad(davor[davor.length - 1]) : "";
      if (istPfad(kand)) path = kand;
    }
    out.push({ path, content });
    letztesEnde = re.lastIndex;
  }
  return out;
}

/* Grobe zeilenbasierte Diff-Zusammenfassung (Mengen-Vergleich). */
function diffZusammenfassung(alt: string, neu: string): { plus: number; minus: number } {
  const a = new Map<string, number>();
  for (const z of alt.split("\n")) a.set(z, (a.get(z) ?? 0) + 1);
  const b = new Map<string, number>();
  for (const z of neu.split("\n")) b.set(z, (b.get(z) ?? 0) + 1);
  let plus = 0;
  let minus = 0;
  for (const [z, n] of b) plus += Math.max(0, n - (a.get(z) ?? 0));
  for (const [z, n] of a) minus += Math.max(0, n - (b.get(z) ?? 0));
  return { plus, minus };
}

/* Live-Vorschau: index.html (oder erste .html) nehmen und lokale
   <link>/<script src> durch den Datei-Inhalt ersetzen. Externe URLs
   (http…) bleiben unangetastet. Leerer String = keine HTML-Datei. */
function baueVorschau(files: Record<string, string>): string {
  const keys = Object.keys(files);
  const htmlKey =
    keys.find((k) => /(^|\/)index\.html$/i.test(k)) ?? keys.find((k) => /\.html$/i.test(k));
  if (!htmlKey) return "";
  const dir = htmlKey.includes("/") ? htmlKey.slice(0, htmlKey.lastIndexOf("/") + 1) : "";
  const hole = (src: string): string | null => {
    if (/^(https?:)?\/\//i.test(src) || src.startsWith("data:")) return null; // extern lassen
    const clean = src.replace(/^\.?\//, "");
    return files[dir + clean] ?? files[clean] ?? null;
  };
  let html = files[htmlKey];
  html = html.replace(/<link\b[^>]*\bhref=["']([^"']+)["'][^>]*>/gi, (m, href) => {
    const css = hole(href);
    return css != null ? `<style>\n${css}\n</style>` : m;
  });
  html = html.replace(/<script\b[^>]*\bsrc=["']([^"']+)["'][^>]*>\s*<\/script>/gi, (m, src) => {
    const js = hole(src);
    return js != null ? `<script>\n${js}\n</script>` : m;
  });
  return html;
}

/* ---------- Download / Upload / ZIP (ohne Fremd-Bibliothek) ---------- */
function downloadBlob(name: string, blob: Blob) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}

// CRC32 (für gültige ZIP-Einträge).
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();
function crc32(bytes: Uint8Array): number {
  let crc = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ bytes[i]) & 0xff];
  return (crc ^ 0xffffffff) >>> 0;
}
// Minimaler „store"-ZIP (keine Kompression) – erzeugt eine gültige .zip-Datei.
function makeZip(files: Record<string, string>): Blob {
  const enc = new TextEncoder();
  const chunks: Uint8Array[] = [];
  const central: Uint8Array[] = [];
  let offset = 0;
  const u16 = (n: number) => new Uint8Array([n & 255, (n >>> 8) & 255]);
  const u32 = (n: number) => new Uint8Array([n & 255, (n >>> 8) & 255, (n >>> 16) & 255, (n >>> 24) & 255]);
  const cat = (arr: Uint8Array[]) => {
    const len = arr.reduce((n, a) => n + a.length, 0);
    const out = new Uint8Array(len);
    let p = 0;
    for (const a of arr) { out.set(a, p); p += a.length; }
    return out;
  };
  for (const [name, content] of Object.entries(files)) {
    const nameB = enc.encode(name);
    const data = enc.encode(content);
    const crc = crc32(data);
    const local = cat([
      u32(0x04034b50), u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(crc), u32(data.length), u32(data.length), u16(nameB.length), u16(0), nameB, data,
    ]);
    chunks.push(local);
    central.push(cat([
      u32(0x02014b50), u16(20), u16(20), u16(0), u16(0), u16(0), u16(0),
      u32(crc), u32(data.length), u32(data.length), u16(nameB.length),
      u16(0), u16(0), u16(0), u16(0), u32(0), u32(offset), nameB,
    ]));
    offset += local.length;
  }
  const cd = cat(central);
  const end = cat([
    u32(0x06054b50), u16(0), u16(0), u16(central.length), u16(central.length),
    u32(cd.length), u32(offset), u16(0),
  ]);
  return new Blob([cat(chunks), cd, end], { type: "application/zip" });
}

export default function StudioPage() {
  const [proj, setProj] = useState<Projekt>(START);
  const [chat, setChat] = useState<{ role: "user" | "assistant"; content: string }[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [suche, setSuche] = useState("");
  const [seiten, setSeiten] = useState<"dateien" | "suche">("dateien");
  const [projSuche, setProjSuche] = useState("");
  const [sprung, setSprung] = useState<{ path: string; zeile: number } | null>(null);
  const [tabs, setTabs] = useState<string[]>([START.open]);
  const [fr, setFr] = useState({ show: false, find: "", replace: "" });
  const [ansicht, setAnsicht] = useState<"code" | "vorschau">("code");
  const taRef = useRef<HTMLTextAreaElement>(null);
  const preRef = useRef<HTMLPreElement>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const uploadRef = useRef<HTMLInputElement>(null);
  const lnRef = useRef<HTMLDivElement>(null);

  // Laden / Speichern.
  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORE);
      if (raw) {
        const p = JSON.parse(raw) as Projekt;
        if (p?.files && p.open) {
          setProj(p);
          setTabs([p.open]);
        }
      }
    } catch {
      /* nichts */
    }
  }, []);
  useEffect(() => {
    try {
      localStorage.setItem(STORE, JSON.stringify(proj));
    } catch {
      /* voll */
    }
  }, [proj]);
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const code = proj.files[proj.open] ?? "";
  const paths = useMemo(() => Object.keys(proj.files).sort(), [proj.files]);
  // Suche filtert nach Dateiname/Pfad.
  const gefiltert = useMemo(() => {
    const q = suche.trim().toLowerCase();
    return q ? paths.filter((p) => p.toLowerCase().includes(q)) : paths;
  }, [paths, suche]);
  // Ordner-Ansicht: Segmente vor der Datei dimmen, nach Tiefe einrücken.
  function teile(p: string) {
    const i = p.lastIndexOf("/");
    return i === -1 ? { ordner: "", datei: p, tiefe: 0 } : { ordner: p.slice(0, i + 1), datei: p.slice(i + 1), tiefe: p.slice(0, i).split("/").length };
  }
  const zeilenNr = useMemo(() => {
    const n = code.split("\n").length;
    return Array.from({ length: n }, (_, i) => i + 1).join("\n");
  }, [code]);
  const vorschauDoc = useMemo(() => baueVorschau(proj.files), [proj.files]);
  const hatVorschau = vorschauDoc !== "";

  // Projektweite Inhaltssuche: Treffer je Datei mit Zeilennummer (Deckel 300).
  const inhaltTreffer = useMemo(() => {
    const q = projSuche.trim().toLowerCase();
    if (q.length < 2) return { proDatei: [] as { path: string; zeilen: { nr: number; text: string }[] }[], gesamt: 0, gedeckelt: false };
    const proDatei: { path: string; zeilen: { nr: number; text: string }[] }[] = [];
    let gesamt = 0;
    let gedeckelt = false;
    for (const p of paths) {
      const zeilen: { nr: number; text: string }[] = [];
      const lines = proj.files[p].split("\n");
      for (let i = 0; i < lines.length; i++) {
        if (lines[i].toLowerCase().includes(q)) {
          zeilen.push({ nr: i, text: lines[i] });
          gesamt++;
          if (gesamt >= 300) { gedeckelt = true; break; }
        }
      }
      if (zeilen.length) proDatei.push({ path: p, zeilen });
      if (gedeckelt) break;
    }
    return { proDatei, gesamt, gedeckelt };
  }, [paths, proj.files, projSuche]);

  function springeZu(path: string, zeile: number) {
    setAnsicht("code");
    openFile(path);
    setSprung({ path, zeile });
  }
  // Nach dem Öffnen der Zieldatei: Cursor auf die Zeile setzen und hinscrollen.
  useEffect(() => {
    if (!sprung || proj.open !== sprung.path) return;
    const ta = taRef.current;
    if (!ta) return;
    const lines = code.split("\n");
    let off = 0;
    for (let i = 0; i < sprung.zeile && i < lines.length; i++) off += lines[i].length + 1;
    ta.focus();
    ta.setSelectionRange(off, off + (lines[sprung.zeile]?.length ?? 0));
    ta.scrollTop = Math.max(0, sprung.zeile * 20 - 100);
    if (preRef.current) preRef.current.scrollTop = ta.scrollTop;
    if (lnRef.current) lnRef.current.scrollTop = ta.scrollTop;
    setSprung(null);
  }, [sprung, proj.open, code]);

  function setCode(next: string) {
    setProj((p) => ({ ...p, files: { ...p.files, [p.open]: next } }));
  }
  function oeffneTab(path: string) {
    setTabs((t) => (t.includes(path) ? t : [...t, path]));
  }
  function openFile(path: string) {
    oeffneTab(path);
    setProj((p) => ({ ...p, open: path }));
  }
  function schliesseTab(path: string) {
    setTabs((t) => {
      const rest = t.filter((x) => x !== path);
      if (proj.open === path && rest.length) setProj((p) => ({ ...p, open: rest[rest.length - 1] }));
      return rest.length ? rest : t; // mindestens ein Tab offen lassen
    });
  }
  function neueDatei() {
    const name = prompt("Dateiname (z. B. app.ts, style.css, src/util.ts):");
    if (!name) return;
    const clean = name.trim().replace(/^\/+/, "");
    if (!clean || proj.files[clean] !== undefined) return;
    oeffneTab(clean);
    setProj((p) => ({ ...p, files: { ...p.files, [clean]: "" }, open: clean }));
  }
  function umbenennen(path: string) {
    const name = prompt("Neuer Name:", path);
    if (!name || name === path) return;
    const clean = name.trim().replace(/^\/+/, "");
    if (!clean || proj.files[clean] !== undefined) return;
    setTabs((t) => t.map((x) => (x === path ? clean : x)));
    setProj((p) => {
      const files = { ...p.files };
      files[clean] = files[path];
      delete files[path];
      return { ...p, files, open: p.open === path ? clean : p.open };
    });
  }
  function loeschen(path: string) {
    if (!confirm(`«${path}» löschen?`)) return;
    setProj((p) => {
      const files = { ...p.files };
      delete files[path];
      const rest = Object.keys(files);
      if (rest.length === 0) files["neu.txt"] = "";
      const open = p.open === path ? Object.keys(files)[0] : p.open;
      return { ...p, files, open };
    });
    setTabs((t) => {
      const rest = t.filter((x) => x !== path);
      return rest.length ? rest : [Object.keys(proj.files).filter((f) => f !== path)[0] ?? "neu.txt"];
    });
  }
  // Suchen & Ersetzen in der aktuellen Datei.
  function ersetzeAlle() {
    if (!fr.find) return;
    setCode(code.split(fr.find).join(fr.replace));
  }
  function ersetzeErstes() {
    if (!fr.find) return;
    const i = code.indexOf(fr.find);
    if (i === -1) return;
    setCode(code.slice(0, i) + fr.replace + code.slice(i + fr.find.length));
  }
  const treffer = fr.find ? code.split(fr.find).length - 1 : 0;
  function downloadDatei() {
    downloadBlob(proj.open.split("/").pop() || "datei.txt", new Blob([code], { type: "text/plain" }));
  }
  function downloadZip() {
    downloadBlob(`${proj.name || "projekt"}.zip`, makeZip(proj.files));
  }
  async function hochladen(e: React.ChangeEvent<HTMLInputElement>) {
    const list = e.target.files;
    if (!list || list.length === 0) return;
    const neu: Record<string, string> = {};
    for (const f of Array.from(list)) {
      try {
        neu[f.name] = await f.text();
      } catch {
        /* Binärdatei übersprungen */
      }
    }
    if (Object.keys(neu).length) {
      setProj((p) => ({ ...p, files: { ...p.files, ...neu }, open: Object.keys(neu)[0] }));
    }
    e.target.value = "";
  }

  // Editor: Tab-Einrückung + Highlight-Overlay-Scroll synchron.
  function onKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    const el = e.currentTarget;
    const s = el.selectionStart;
    const eEnd = el.selectionEnd;
    // Cursor/Selektion nach dem Neu-Rendern setzen.
    const setzen = (next: string, ss: number, se: number = ss) => {
      setCode(next);
      requestAnimationFrame(() => { el.selectionStart = ss; el.selectionEnd = se; });
    };
    const OFFEN: Record<string, string> = { "(": ")", "[": "]", "{": "}" };
    const ZU = new Set([")", "]", "}"]);
    const QUOTE = new Set(['"', "'", "`"]);

    if (e.key === "Tab") {
      e.preventDefault();
      setzen(code.slice(0, s) + "  " + code.slice(eEnd), s + 2);
      return;
    }

    // Enter: Einrückung der Vorzeile übernehmen; leeres Klammerpaar ausklappen.
    if (e.key === "Enter" && !e.shiftKey && s === eEnd) {
      const zeilenStart = code.lastIndexOf("\n", s - 1) + 1;
      const vorher = code.slice(zeilenStart, s);
      const einzug = /^[ \t]*/.exec(vorher)?.[0] ?? "";
      const davor = code[s - 1];
      const danach = code[s];
      if (davor && danach && OFFEN[davor] === danach) {
        e.preventDefault();
        const ins = "\n" + einzug + "  " + "\n" + einzug;
        setzen(code.slice(0, s) + ins + code.slice(s), s + 1 + einzug.length + 2);
        return;
      }
      if (einzug || /[([{:]\s*$/.test(vorher)) {
        e.preventDefault();
        const extra = /[([{:]\s*$/.test(vorher) ? "  " : "";
        const ins = "\n" + einzug + extra;
        setzen(code.slice(0, s) + ins + code.slice(s), s + ins.length);
        return;
      }
      return;
    }

    if (e.ctrlKey || e.metaKey || e.altKey) return;

    // Öffnende Klammer: Paar einsetzen oder Selektion umschliessen.
    if (OFFEN[e.key]) {
      e.preventDefault();
      const zu = OFFEN[e.key];
      if (s !== eEnd) { setzen(code.slice(0, s) + e.key + code.slice(s, eEnd) + zu + code.slice(eEnd), s + 1, eEnd + 1); return; }
      setzen(code.slice(0, s) + e.key + zu + code.slice(s), s + 1);
      return;
    }
    // Schliessende Klammer direkt vor dem Cursor: überspringen statt einfügen.
    if (ZU.has(e.key) && s === eEnd && code[s] === e.key) {
      e.preventDefault();
      requestAnimationFrame(() => { el.selectionStart = el.selectionEnd = s + 1; });
      return;
    }
    // Anführungszeichen: überspringen / Selektion umschliessen / Paar einsetzen.
    if (QUOTE.has(e.key)) {
      if (s === eEnd && code[s] === e.key) { e.preventDefault(); requestAnimationFrame(() => { el.selectionStart = el.selectionEnd = s + 1; }); return; }
      if (s !== eEnd) { e.preventDefault(); setzen(code.slice(0, s) + e.key + code.slice(s, eEnd) + e.key + code.slice(eEnd), s + 1, eEnd + 1); return; }
      // Nicht doppeln, wenn direkt an Wort/Quote (z. B. Apostroph in Text).
      const davor = code[s - 1];
      if (davor && /[\w"'`]/.test(davor)) return;
      e.preventDefault();
      setzen(code.slice(0, s) + e.key + e.key + code.slice(s), s + 1);
      return;
    }
    // Backspace zwischen leerem Paar: beide Zeichen löschen.
    if (e.key === "Backspace" && s === eEnd && s > 0) {
      const davor = code[s - 1];
      const danach = code[s];
      if ((OFFEN[davor] === danach) || (QUOTE.has(davor) && davor === danach)) {
        e.preventDefault();
        setzen(code.slice(0, s - 1) + code.slice(s + 1), s - 1);
      }
    }
  }
  function syncScroll() {
    if (preRef.current && taRef.current) {
      preRef.current.scrollTop = taRef.current.scrollTop;
      preRef.current.scrollLeft = taRef.current.scrollLeft;
    }
    if (lnRef.current && taRef.current) lnRef.current.scrollTop = taRef.current.scrollTop;
  }

  async function frag(text: string) {
    const frage = text.trim();
    if (!frage || streaming) return;
    setInput("");
    // Ganzes Projekt als Kontext (bis ~60k Zeichen), damit die KI mehrere
    // Dateien lesen und ändern kann. Bei sehr grossen Projekten nur die
    // offene Datei voll, der Rest als Pfadliste.
    const alleDateien = Object.entries(proj.files);
    const gesamt = alleDateien.reduce((n, [, c]) => n + c.length, 0);
    let projektKontext: string;
    if (gesamt <= 60000) {
      projektKontext = alleDateien
        .map(([p, c]) => `### ${p}\n\`\`\`${ext(p)}\n${c}\n\`\`\``)
        .join("\n\n");
    } else {
      projektKontext =
        `Offene Datei ### ${proj.open}\n\`\`\`${ext(proj.open)}\n${code}\n\`\`\`\n\n` +
        `Weitere Dateien (Inhalt auf Nachfrage): ${paths.filter((p) => p !== proj.open).join(", ")}`;
    }
    const kontextNachricht =
      `Du bist der Programmier-Agent im KI-Studio. Projekt «${proj.name}», offene Datei «${proj.open}».\n\n` +
      `Projektdateien:\n\n${projektKontext}\n\n` +
      `Aufgabe des Nutzers: ${frage}\n\n` +
      `Wenn du Dateien änderst oder neu anlegst, gib pro Datei ZUERST den Pfad in einer eigenen Zeile als **pfad/zur/datei.ext** aus und danach EINEN Codeblock mit dem VOLLSTÄNDIGEN neuen Inhalt der Datei. Du darfst mehrere Dateien in einer Antwort liefern. Ändere nur, was nötig ist.`;
    const verlauf = [...chat, { role: "user" as const, content: frage }];
    setChat([...verlauf, { role: "assistant", content: "" }]);
    setStreaming(true);

    let lic = "", use = "", ult = "";
    try {
      lic = localStorage.getItem(LICENSE_TOKEN_KEY) ?? "";
      use = localStorage.getItem(USAGE_TOKEN_KEY) ?? "";
      ult = localStorage.getItem(ULTRA_TOKEN_KEY) ?? "";
    } catch {
      /* nichts */
    }
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "content-type": "application/json",
          ...(lic ? { "x-acc-license": lic } : {}),
          ...(use ? { "x-acc-usage": use } : {}),
          ...(ult ? { "x-acc-ultra": ult } : {}),
        },
        body: JSON.stringify({
          messages: [
            ...verlauf.slice(0, -1).map((m) => ({ role: m.role, content: m.content })),
            { role: "user", content: kontextNachricht },
          ],
        }),
      });
      if (!res.ok || !res.body) throw new Error();
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\n\n");
        buf = parts.pop() ?? "";
        for (const part of parts) {
          const line = part.split("\n").find((l) => l.startsWith("data:"));
          if (!line) continue;
          let ev: { type: string; text?: string; token?: string };
          try {
            ev = JSON.parse(line.slice(line.indexOf(":") + 1).trim());
          } catch {
            continue;
          }
          if (ev.type === "delta" && ev.text) {
            const t = ev.text;
            setChat((ms) => {
              const last = ms[ms.length - 1];
              if (last?.role !== "assistant") return ms;
              return [...ms.slice(0, -1), { ...last, content: last.content + t }];
            });
          } else if (ev.type === "usage" && ev.token) {
            try {
              localStorage.setItem(USAGE_TOKEN_KEY, ev.token);
            } catch {
              /* voll */
            }
          }
        }
      }
    } catch {
      setChat((ms) => [...ms.slice(0, -1), { role: "assistant", content: "Verbindung unterbrochen. Bitte erneut senden." }]);
    } finally {
      setStreaming(false);
    }
  }

  const letzteAntwort = chat.length && chat[chat.length - 1].role === "assistant" ? chat[chat.length - 1].content : "";
  // Mehr-Datei-Vorschläge: Blöcke mit erkanntem Pfad, gegen Dublikaten (letzter gewinnt).
  const dateiVorschlaege = useMemo(() => {
    const map = new Map<string, string>();
    for (const b of dateiBloecke(letzteAntwort)) if (b.path) map.set(b.path, b.content);
    return Array.from(map, ([path, content]) => ({ path, content }));
  }, [letzteAntwort]);
  // Nur Vorschläge, die die Datei wirklich verändern (oder neu sind).
  const echteVorschlaege = dateiVorschlaege.filter((v) => proj.files[v.path] !== v.content);
  // Fallback: eine einzelne Datei ohne Pfad-Markierung → betrifft die offene Datei.
  const vorschlag = echteVorschlaege.length === 0 ? ersterCodeblock(letzteAntwort) : null;

  function uebernehmeDatei(path: string, content: string) {
    oeffneTab(path);
    setProj((p) => ({ ...p, files: { ...p.files, [path]: content }, open: path }));
  }
  // Suchbegriff im Ergebnistext hervorheben (ohne HTML-Injektion).
  function markiere(text: string, q: string): React.ReactNode[] {
    const t = text.length > 160 ? text.slice(0, 160) : text;
    const ql = q.toLowerCase();
    if (!ql) return [t];
    const low = t.toLowerCase();
    const out: React.ReactNode[] = [];
    let i = 0;
    let k = 0;
    for (;;) {
      const j = low.indexOf(ql, i);
      if (j === -1) { out.push(t.slice(i)); break; }
      if (j > i) out.push(t.slice(i, j));
      out.push(<mark key={k++} className="rounded bg-[#ff8c2a]/30 px-0.5 text-[#ffb35c]">{t.slice(j, j + ql.length)}</mark>);
      i = j + ql.length;
    }
    return out;
  }
  function neuesProjekt(p: Projekt) {
    if (!confirm(`Neues Projekt «${p.name}» starten? Das aktuelle Projekt wird ersetzt (vorher ggf. als ZIP sichern).`)) return;
    setProj(p);
    setTabs([p.open]);
    setChat([]);
    setAnsicht("code");
  }
  function uebernehmeAlle() {
    if (!echteVorschlaege.length) return;
    const neu: Record<string, string> = {};
    for (const v of echteVorschlaege) neu[v.path] = v.content;
    const ziele = Object.keys(neu);
    setTabs((t) => Array.from(new Set([...t, ...ziele])));
    setProj((p) => ({ ...p, files: { ...p.files, ...neu }, open: ziele[0] }));
  }

  return (
    <div className="flex h-screen flex-col bg-[#0b0a0f] text-zinc-100">
      <header className="flex items-center justify-between gap-3 border-b border-white/8 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-[#ff8c2a] shadow-[0_0_10px_2px_rgba(255,140,42,0.7)]" />
          <span className="font-mono text-[11px] tracking-[0.2em] text-zinc-400">KI-STUDIO</span>
          <span className="ml-2 rounded-md bg-white/[0.05] px-2 py-0.5 font-mono text-[11px] text-zinc-400">{proj.name}</span>
          <details className="group relative ml-1">
            <summary className="flex cursor-pointer list-none items-center gap-1 rounded-md px-2 py-0.5 text-[11px] text-zinc-400 hover:bg-white/[0.06] hover:text-zinc-200">
              ＋ Neu
              <svg viewBox="0 0 12 12" className="h-2.5 w-2.5 transition-transform group-open:rotate-180" aria-hidden="true">
                <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </summary>
            <div className="absolute left-0 z-50 mt-2 w-64 overflow-hidden rounded-xl border border-white/10 bg-[#14100c]/95 py-1 shadow-[0_16px_44px_-8px_rgba(0,0,0,0.7)] backdrop-blur-xl">
              {VORLAGEN.map((v) => (
                <button
                  key={v.id}
                  onClick={() => neuesProjekt(v.projekt)}
                  className="block w-full px-3 py-2 text-left hover:bg-[#ff8c2a]/12"
                >
                  <span className="block text-[12.5px] font-semibold text-zinc-100">{v.label}</span>
                  <span className="block text-[10.5px] text-zinc-500">{v.hinweis}</span>
                </button>
              ))}
            </div>
          </details>
        </div>
        <WorkNav aktiv="studio" variante="dunkel" />
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[210px_1fr_360px] max-lg:grid-cols-[180px_1fr] max-md:grid-cols-1">
        {/* Dateibaum / Projektsuche */}
        <aside className="min-h-0 overflow-y-auto border-r border-white/8 bg-white/[0.02] p-2 max-md:hidden">
          <div className="mb-2 flex items-center gap-1">
            <button
              onClick={() => setSeiten("dateien")}
              className={`rounded px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${seiten === "dateien" ? "bg-white/[0.06] text-[#ffb35c]" : "text-zinc-500 hover:text-zinc-300"}`}
            >
              Dateien
            </button>
            <button
              onClick={() => setSeiten("suche")}
              className={`rounded px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider ${seiten === "suche" ? "bg-white/[0.06] text-[#ffb35c]" : "text-zinc-500 hover:text-zinc-300"}`}
            >
              Suche
            </button>
            {seiten === "dateien" && (
              <div className="ml-auto flex items-center gap-1.5 text-zinc-400">
                <button onClick={() => uploadRef.current?.click()} className="text-[12px] hover:text-[#ffb35c]" title="Dateien hochladen">↑</button>
                <button onClick={downloadDatei} className="text-[12px] hover:text-[#ffb35c]" title="Aktuelle Datei herunterladen">↓</button>
                <button onClick={downloadZip} className="text-[10px] font-semibold hover:text-[#ffb35c]" title="Projekt als ZIP">ZIP</button>
                <button onClick={neueDatei} className="text-[16px] leading-none hover:text-[#ffb35c]" title="Neue Datei">+</button>
              </div>
            )}
          </div>
          <input ref={uploadRef} type="file" multiple onChange={hochladen} className="hidden" accept=".txt,.md,.js,.ts,.tsx,.jsx,.json,.css,.html,.py,.java,.go,.rs,.c,.cpp,.sh,.yml,.yaml,.csv" />

          {seiten === "dateien" ? (
            <>
              <input
                value={suche}
                onChange={(e) => setSuche(e.target.value)}
                placeholder="Dateien suchen …"
                className="mb-2 w-full rounded-md border border-white/8 bg-white/[0.03] px-2 py-1 text-[12px] text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-[#ff8c2a]/40"
              />
              {gefiltert.length === 0 && <p className="px-2 py-1 text-[12px] text-zinc-600">Keine Treffer.</p>}
              {gefiltert.map((p) => {
                const t = teile(p);
                return (
                  <div
                    key={p}
                    style={{ paddingLeft: 8 + t.tiefe * 12 }}
                    className={`group flex items-center justify-between rounded py-1 pr-2 text-[13px] ${p === proj.open ? "bg-[#ff8c2a]/15 text-[#ffb35c]" : "text-zinc-300 hover:bg-white/5"}`}
                  >
                    <button onClick={() => openFile(p)} className="min-w-0 truncate text-left" title={p}>
                      {t.ordner && <span className="text-zinc-600">{t.ordner}</span>}
                      {t.datei}
                    </button>
                    <span className="hidden shrink-0 gap-1 group-hover:flex">
                      <button onClick={() => umbenennen(p)} className="text-zinc-500 hover:text-zinc-200" title="Umbenennen">✎</button>
                      <button onClick={() => loeschen(p)} className="text-zinc-500 hover:text-red-400" title="Löschen">✕</button>
                    </span>
                  </div>
                );
              })}
              <p className="mt-2 px-2 text-[10px] text-zinc-600">Tipp: Namen mit „/" erzeugen Ordner, z. B. src/app.ts</p>
            </>
          ) : (
            <>
              <input
                value={projSuche}
                onChange={(e) => setProjSuche(e.target.value)}
                placeholder="Im ganzen Projekt suchen …"
                autoFocus
                className="mb-2 w-full rounded-md border border-white/8 bg-white/[0.03] px-2 py-1 text-[12px] text-zinc-200 outline-none placeholder:text-zinc-600 focus:border-[#ff8c2a]/40"
              />
              {projSuche.trim().length < 2 ? (
                <p className="px-2 py-1 text-[11px] text-zinc-600">Mindestens 2 Zeichen eingeben.</p>
              ) : inhaltTreffer.gesamt === 0 ? (
                <p className="px-2 py-1 text-[12px] text-zinc-600">Keine Fundstellen.</p>
              ) : (
                <>
                  <p className="mb-1 px-1 text-[10.5px] text-zinc-500">
                    {inhaltTreffer.gesamt}{inhaltTreffer.gedeckelt ? "+" : ""} Fundstellen in {inhaltTreffer.proDatei.length} Dateien
                  </p>
                  {inhaltTreffer.proDatei.map((d) => (
                    <div key={d.path} className="mb-1.5">
                      <div className="truncate px-1 py-0.5 font-mono text-[11px] text-zinc-400" title={d.path}>{d.path}</div>
                      {d.zeilen.map((z) => (
                        <button
                          key={z.nr}
                          onClick={() => springeZu(d.path, z.nr)}
                          className="flex w-full items-baseline gap-2 rounded px-1 py-0.5 text-left hover:bg-white/5"
                        >
                          <span className="shrink-0 font-mono text-[10px] text-zinc-600">{z.nr + 1}</span>
                          <span className="min-w-0 truncate font-mono text-[11.5px] text-zinc-300">{markiere(z.text.trim(), projSuche.trim())}</span>
                        </button>
                      ))}
                    </div>
                  ))}
                </>
              )}
            </>
          )}
        </aside>

        {/* Editor */}
        <main className="relative min-h-0 min-w-0 bg-[#0b0a0f]">
          {/* Tab-Leiste */}
          <div className="flex items-stretch border-b border-white/8 text-[12px]">
            <div className="flex min-w-0 flex-1 overflow-x-auto">
              {tabs.filter((t) => proj.files[t] !== undefined).map((t) => (
                <div
                  key={t}
                  className={`flex shrink-0 items-center gap-1.5 border-r border-white/8 px-3 py-1.5 ${t === proj.open ? "bg-[#0b0a0f] text-[#ffb35c]" : "bg-white/[0.02] text-zinc-400 hover:text-zinc-200"}`}
                >
                  <button onClick={() => openFile(t)} className="font-mono" title={t}>{t.split("/").pop()}</button>
                  <button onClick={() => schliesseTab(t)} className="text-zinc-600 hover:text-red-400" title="Tab schliessen">✕</button>
                </div>
              ))}
            </div>
            {hatVorschau && (
              <div className="flex shrink-0 items-center border-l border-white/8">
                <button
                  onClick={() => setAnsicht("code")}
                  className={`px-2.5 py-1.5 ${ansicht === "code" ? "text-[#ffb35c]" : "text-zinc-400 hover:text-zinc-200"}`}
                  title="Code bearbeiten"
                >
                  Code
                </button>
                <button
                  onClick={() => setAnsicht("vorschau")}
                  className={`px-2.5 py-1.5 ${ansicht === "vorschau" ? "text-[#ffb35c]" : "text-zinc-400 hover:text-zinc-200"}`}
                  title="Live-Vorschau im Browser"
                >
                  ▶ Vorschau
                </button>
              </div>
            )}
            <button
              onClick={() => setFr((f) => ({ ...f, show: !f.show }))}
              className={`shrink-0 border-l border-white/8 px-3 ${fr.show ? "text-[#ffb35c]" : "text-zinc-400 hover:text-zinc-200"}`}
              title="Suchen & Ersetzen"
            >
              ⌕
            </button>
          </div>
          {fr.show && (
            <div className="flex flex-wrap items-center gap-2 border-b border-white/8 bg-white/[0.02] px-3 py-1.5 text-[12px]">
              <input value={fr.find} onChange={(e) => setFr((f) => ({ ...f, find: e.target.value }))} placeholder="Suchen"
                className="w-40 rounded border border-white/8 bg-white/[0.03] px-2 py-1 text-zinc-200 outline-none focus:border-[#ff8c2a]/40" />
              <input value={fr.replace} onChange={(e) => setFr((f) => ({ ...f, replace: e.target.value }))} placeholder="Ersetzen durch"
                className="w-40 rounded border border-white/8 bg-white/[0.03] px-2 py-1 text-zinc-200 outline-none focus:border-[#ff8c2a]/40" />
              <span className="text-zinc-500">{treffer} Treffer</span>
              <button onClick={ersetzeErstes} disabled={!treffer} className="rounded bg-white/[0.06] px-2 py-1 text-zinc-200 hover:bg-white/10 disabled:opacity-40">Ersetzen</button>
              <button onClick={ersetzeAlle} disabled={!treffer} className="rounded bg-[#ff8c2a]/20 px-2 py-1 text-[#ffb35c] hover:bg-[#ff8c2a]/30 disabled:opacity-40">Alle ersetzen</button>
            </div>
          )}
          {hatVorschau && ansicht === "vorschau" ? (
            <iframe
              title="Live-Vorschau"
              srcDoc={vorschauDoc}
              sandbox="allow-scripts allow-forms allow-modals"
              className={`w-full bg-white ${fr.show ? "h-[calc(100%-70px)]" : "h-[calc(100%-33px)]"}`}
            />
          ) : (
            <div className={`acc-ed relative overflow-hidden ${fr.show ? "h-[calc(100%-70px)]" : "h-[calc(100%-33px)]"}`}>
              <div ref={lnRef} className="acc-ed__ln" aria-hidden="true">{zeilenNr}</div>
              <pre ref={preRef} className="acc-ed__pre" aria-hidden="true" dangerouslySetInnerHTML={{ __html: highlight(code) + "\n" }} />
              <textarea
                ref={taRef}
                value={code}
                onChange={(e) => setCode(e.target.value)}
                onKeyDown={onKeyDown}
                onScroll={syncScroll}
                spellCheck={false}
                className="acc-ed__ta"
              />
            </div>
          )}
        </main>

        {/* KI-Assistent */}
        <aside className="flex min-h-0 flex-col border-l border-white/8 bg-white/[0.02] max-md:hidden">
          <div className="border-b border-white/8 px-3 py-2 text-[12px] font-semibold text-zinc-300">KI-Assistent</div>
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
            {chat.length === 0 && (
              <p className="text-[12px] leading-relaxed text-zinc-500">
                Bitten Sie die KI, am Projekt zu arbeiten – z. B. „Erkläre <b className="text-zinc-300">{proj.open}</b>",
                „Baue eine Funktion X" oder „Splitte das in mehrere Dateien auf". Sie kennt alle Dateien und kann
                mehrere davon in einem Schritt anlegen oder ändern.
              </p>
            )}
            {chat.map((m, i) => (
              <div key={i} className={m.role === "user" ? "text-right" : ""}>
                <div className={`inline-block max-w-[95%] whitespace-pre-wrap rounded-xl px-3 py-2 text-left text-[12.5px] leading-relaxed ${m.role === "user" ? "bg-[#ff8c2a]/15 text-[#ffd9b0]" : "border border-white/8 bg-white/[0.03] text-zinc-200"}`}>
                  {m.content || (streaming && i === chat.length - 1 ? "…" : "")}
                </div>
              </div>
            ))}
            <div ref={chatEndRef} />
          </div>
          {echteVorschlaege.length > 0 && !streaming && (
            <div className="border-t border-white/8 p-2">
              <div className="mb-1.5 flex items-center justify-between gap-2 px-1 text-[11px]">
                <span className="font-mono text-zinc-500">
                  KI-Änderung an {echteVorschlaege.length} {echteVorschlaege.length === 1 ? "Datei" : "Dateien"}
                </span>
                {echteVorschlaege.length > 1 && (
                  <button onClick={uebernehmeAlle} className="rounded-md bg-[#22c55e]/15 px-2 py-0.5 font-semibold text-[#86efac] hover:bg-[#22c55e]/25">
                    Alle übernehmen
                  </button>
                )}
              </div>
              <div className="max-h-44 space-y-1 overflow-y-auto">
                {echteVorschlaege.map((v) => {
                  const alt = proj.files[v.path];
                  const neu = alt === undefined;
                  const d = diffZusammenfassung(alt ?? "", v.content);
                  return (
                    <div key={v.path} className="flex items-center gap-2 rounded-lg border border-white/8 bg-white/[0.03] px-2 py-1.5">
                      <span className="min-w-0 flex-1 truncate font-mono text-[11.5px] text-zinc-200" title={v.path}>{v.path}</span>
                      {neu ? (
                        <span className="shrink-0 rounded bg-[#ff8c2a]/15 px-1.5 text-[10px] font-semibold text-[#ffb35c]">neu</span>
                      ) : (
                        <span className="shrink-0 text-[10.5px]">
                          <span className="text-[#86efac]">+{d.plus}</span> <span className="text-red-400">−{d.minus}</span>
                        </span>
                      )}
                      <button
                        onClick={() => uebernehmeDatei(v.path, v.content)}
                        className="shrink-0 rounded-md bg-gradient-to-br from-[#22c55e] to-[#16a34a] px-2 py-1 text-[11px] font-semibold text-white"
                      >
                        Übernehmen
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          {vorschlag && !streaming && vorschlag !== code && (
            <div className="border-t border-white/8 p-2">
              {(() => {
                const d = diffZusammenfassung(code, vorschlag);
                return (
                  <div className="mb-1.5 flex items-center gap-2 px-1 text-[11px]">
                    <span className="font-mono text-zinc-500">Vorgeschlagene Änderung:</span>
                    <span className="text-[#86efac]">+{d.plus}</span>
                    <span className="text-red-400">−{d.minus}</span>
                    <span className="text-zinc-600">Zeilen</span>
                  </div>
                );
              })()}
              <button
                onClick={() => setCode(vorschlag)}
                className="w-full rounded-lg bg-gradient-to-br from-[#22c55e] to-[#16a34a] px-3 py-2 text-[12.5px] font-semibold text-white"
              >
                Änderung in {proj.open.split("/").pop()} übernehmen
              </button>
            </div>
          )}
          <div className="border-t border-white/8 p-2">
            <div className="flex items-end gap-2 rounded-xl border border-white/10 bg-white/[0.04] p-1.5 focus-within:border-[#ff8c2a]/40">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); frag(input); } }}
                rows={1}
                placeholder="Aufgabe in natürlicher Sprache …"
                disabled={streaming}
                className="max-h-28 flex-1 resize-none bg-transparent px-1.5 py-1 text-[12.5px] text-zinc-100 outline-none placeholder:text-zinc-500"
              />
              <button onClick={() => frag(input)} disabled={streaming || !input.trim()} className="h-7 shrink-0 rounded-lg bg-gradient-to-br from-[#ff8c2a] to-[#ff5f1f] px-3 text-[12px] font-semibold text-white disabled:opacity-40">
                {streaming ? "…" : "Senden"}
              </button>
            </div>
            <p className="mt-1.5 px-1 text-[10.5px] leading-snug text-zinc-500">
              🔧 Die KI liest &amp; ändert mehrere Dateien auf einmal (Diff prüfen, dann übernehmen). Terminal, echtes Git &amp; Debugger laufen server-/Enterprise-seitig (geplant).
            </p>
          </div>
        </aside>
      </div>

      <style>{`
        .acc-ed { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 13px; line-height: 20px; }
        .acc-ed__ln {
          position: absolute; top: 0; left: 0; bottom: 0; width: 48px;
          margin: 0; padding: 12px 8px 12px 0; font: inherit; text-align: right;
          white-space: pre; overflow: hidden; color: #4b5563; user-select: none;
          background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.06); z-index: 0;
        }
        .acc-ed__pre, .acc-ed__ta {
          position: absolute; top: 0; right: 0; bottom: 0; left: 48px; margin: 0; padding: 12px 14px;
          font: inherit; letter-spacing: normal; tab-size: 2;
          white-space: pre; overflow: auto; border: 0;
        }
        .acc-ed__pre { color: #cdd3de; pointer-events: none; z-index: 0; }
        .acc-ed__ta {
          color: transparent; background: transparent; caret-color: #ff8c2a;
          resize: none; outline: none; z-index: 1;
        }
        .acc-ed__ta::selection { background: rgba(255,140,42,0.28); }
        .tk-kw { color: #ff8c2a; } .tk-str { color: #86efac; }
        .tk-com { color: #6b7280; font-style: italic; } .tk-num { color: #7dd3fc; }
      `}</style>
    </div>
  );
}
