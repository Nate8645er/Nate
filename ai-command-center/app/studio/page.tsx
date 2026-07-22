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
        if (p?.files && p.open) setProj(p);
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

  function setCode(next: string) {
    setProj((p) => ({ ...p, files: { ...p.files, [p.open]: next } }));
  }
  function openFile(path: string) {
    setProj((p) => ({ ...p, open: path }));
  }
  function neueDatei() {
    const name = prompt("Dateiname (z. B. app.ts, style.css, notizen.md):");
    if (!name) return;
    const clean = name.trim().replace(/^\/+/, "");
    if (!clean || proj.files[clean] !== undefined) return;
    setProj((p) => ({ ...p, files: { ...p.files, [clean]: "" }, open: clean }));
  }
  function umbenennen(path: string) {
    const name = prompt("Neuer Name:", path);
    if (!name || name === path) return;
    const clean = name.trim().replace(/^\/+/, "");
    if (!clean || proj.files[clean] !== undefined) return;
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
  }
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
    if (e.key === "Tab") {
      e.preventDefault();
      const el = e.currentTarget;
      const s = el.selectionStart;
      const next = code.slice(0, s) + "  " + code.slice(el.selectionEnd);
      setCode(next);
      requestAnimationFrame(() => {
        el.selectionStart = el.selectionEnd = s + 2;
      });
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
    const kontextNachricht =
      `Du hilfst im KI-Studio an der Datei «${proj.open}». Aktueller Inhalt:\n\n` +
      "```" + ext(proj.open) + "\n" + code + "\n```\n\n" +
      "Aufgabe des Nutzers: " + frage +
      "\n\nWenn du Code lieferst, gib die VOLLSTÄNDIGE neue Datei in EINEM Codeblock zurück.";
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
  const vorschlag = ersterCodeblock(letzteAntwort);

  return (
    <div className="flex h-screen flex-col bg-[#0b0a0f] text-zinc-100">
      <header className="flex items-center justify-between gap-3 border-b border-white/8 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-[#ff8c2a] shadow-[0_0_10px_2px_rgba(255,140,42,0.7)]" />
          <span className="font-mono text-[11px] tracking-[0.2em] text-zinc-400">KI-STUDIO</span>
          <span className="ml-2 rounded-md bg-white/[0.05] px-2 py-0.5 font-mono text-[11px] text-zinc-400">{proj.name}</span>
        </div>
        <WorkNav aktiv="studio" variante="dunkel" />
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-[210px_1fr_360px] max-lg:grid-cols-[180px_1fr] max-md:grid-cols-1">
        {/* Dateibaum */}
        <aside className="min-h-0 overflow-y-auto border-r border-white/8 bg-white/[0.02] p-2 max-md:hidden">
          <div className="mb-2 flex items-center justify-between px-1">
            <span className="font-mono text-[10px] uppercase tracking-wider text-zinc-500">Dateien</span>
            <div className="flex items-center gap-1.5 text-zinc-400">
              <button onClick={() => uploadRef.current?.click()} className="text-[12px] hover:text-[#ffb35c]" title="Dateien hochladen">↑</button>
              <button onClick={downloadDatei} className="text-[12px] hover:text-[#ffb35c]" title="Aktuelle Datei herunterladen">↓</button>
              <button onClick={downloadZip} className="text-[10px] font-semibold hover:text-[#ffb35c]" title="Projekt als ZIP">ZIP</button>
              <button onClick={neueDatei} className="text-[16px] leading-none hover:text-[#ffb35c]" title="Neue Datei">+</button>
            </div>
          </div>
          <input ref={uploadRef} type="file" multiple onChange={hochladen} className="hidden" accept=".txt,.md,.js,.ts,.tsx,.jsx,.json,.css,.html,.py,.java,.go,.rs,.c,.cpp,.sh,.yml,.yaml,.csv" />
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
        </aside>

        {/* Editor */}
        <main className="relative min-h-0 min-w-0 bg-[#0b0a0f]">
          <div className="flex items-center gap-2 border-b border-white/8 px-3 py-1.5 text-[12px] text-zinc-400">
            <span className="font-mono">{proj.open}</span>
            <span className="rounded bg-white/[0.05] px-1.5 py-0.5 text-[10px] uppercase">{ext(proj.open) || "txt"}</span>
          </div>
          <div className="acc-ed relative h-[calc(100%-33px)] overflow-hidden">
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
        </main>

        {/* KI-Assistent */}
        <aside className="flex min-h-0 flex-col border-l border-white/8 bg-white/[0.02] max-md:hidden">
          <div className="border-b border-white/8 px-3 py-2 text-[12px] font-semibold text-zinc-300">KI-Assistent</div>
          <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-3">
            {chat.length === 0 && (
              <p className="text-[12px] leading-relaxed text-zinc-500">
                Bitten Sie die KI, an <b className="text-zinc-300">{proj.open}</b> zu arbeiten – z. B. „Erkläre diesen Code",
                „Baue eine Funktion X" oder „Finde Fehler". Sie kennt den Datei-Inhalt.
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
          {vorschlag && !streaming && (
            <div className="border-t border-white/8 p-2">
              <button
                onClick={() => setCode(vorschlag)}
                className="w-full rounded-lg bg-gradient-to-br from-[#22c55e] to-[#16a34a] px-3 py-2 text-[12.5px] font-semibold text-white"
              >
                Vorgeschlagenen Code in {proj.open} übernehmen
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
              🔧 Terminal, echtes Git &amp; Debugger laufen server-/Enterprise-seitig (geplant). Hier: Dateien, Editor &amp; KI-Bearbeitung im Browser.
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
