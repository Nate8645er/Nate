#!/usr/bin/env node
// Blin — lokaler Agent des ULTRA AI ENTERPRISE OS.
//
// Das ist die "echte" Version aus dem Video: laeuft als Programm auf DEINEM
// Rechner (nicht als Webseite), zeigt das Tages-Dashboard im Terminal und
// kann einen echten Browser fernsteuern.
//
// WICHTIG — ehrliche Grenzen:
// - "Den ganzen Laptop per Stimme bedienen" (beliebige Apps oeffnen, tippen)
//   ist Computer-Use ueber Claude Code, nicht dieses kleine Skript. Was hier
//   real laeuft: Tages-Dashboard + echte Browser-Automation (Playwright).
// - API-Keys kommen aus Umgebungsvariablen, NIE in den Code.
//
// Nutzung:
//   node blin.mjs                      # Tages-Dashboard (Live-Countdown)
//   node blin.mjs --once               # Dashboard einmal rendern (Test)
//   node blin.mjs --browse "whey protein"   # echten Browser oeffnen + suchen
//   node blin.mjs --browse "…" --headless   # ohne sichtbares Fenster (Test/CI)
//
// Aufgaben liegen in tasks.json (siehe tasks.example.json).

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const args = process.argv.slice(2);
const has = (f) => args.includes(f);
const val = (f) => { const i = args.indexOf(f); return i >= 0 ? args[i + 1] : null; };

const C = {
  reset:'\x1b[0m', dim:'\x1b[2m', b:'\x1b[1m',
  red:'\x1b[38;5;203m', coral:'\x1b[38;5;209m', gold:'\x1b[38;5;220m',
  green:'\x1b[38;5;114m', grey:'\x1b[38;5;245m', navy:'\x1b[38;5;60m',
  bgRed:'\x1b[48;5;52m', bgGreen:'\x1b[48;5;22m', bgCoral:'\x1b[48;5;95m',
};

function loadTasks() {
  for (const f of ['tasks.json', 'tasks.example.json']) {
    const p = path.join(__dirname, f);
    if (fs.existsSync(p)) return JSON.parse(fs.readFileSync(p, 'utf8'));
  }
  return { day_start:'08:00', title:'Mein Tag startet.', tasks:[] };
}

function pad(s, n) { s = String(s); return s.length >= n ? s.slice(0, n) : s + ' '.repeat(n - s.length); }
function bar(kind, w) {
  const bg = kind === 'done' ? C.bgGreen : kind === 'active' ? C.bgCoral : C.bgRed;
  return bg + ' '.repeat(w) + C.reset;
}

function render(data) {
  const now = new Date();
  const [dh, dm] = (data.day_start || '08:00').split(':').map(Number);
  const start = new Date(now); start.setHours(dh, dm, 0, 0);
  let secs = Math.max(0, Math.floor((now - start) / 1000)); // Zeit seit Tagesstart
  const hh = String(Math.floor(secs/3600)).padStart(1,'0');
  const mm = String(Math.floor(secs%3600/60)).padStart(2,'0');
  const ss = String(secs%60).padStart(2,'0');

  const lines = [];
  lines.push('');
  lines.push('  ' + C.dim + 'LIVE · IN SEQUENCE   ULTRA · BLIN · MORNING ROUTINE' + C.reset);
  lines.push('  ' + C.b + C.coral + '"' + (data.title || 'Mein Tag startet.') + '"' + C.reset);
  lines.push('  ' + C.red + C.b + `${hh}:${mm}:${ss}` + C.reset + '  ' + C.dim + 'seit Tagesstart' + C.reset);
  lines.push('');

  const tasks = data.tasks || [];
  const doneN = tasks.filter(t => t.status === 'done').length;
  tasks.forEach((t, i) => {
    const kind = t.status || 'todo';
    const dot = kind === 'done' ? C.green + '●' : kind === 'active' ? C.coral + '◐' : C.grey + '○';
    const name = pad(t.name, 34);
    const w = Math.max(4, Math.min(28, Math.round((t.weight || 1) * 7)));
    const meta = t.eta ? C.dim + ' ' + t.eta + C.reset : '';
    lines.push('  ' + dot + C.reset + ' ' + C.b + name + C.reset + ' ' + bar(kind, w) + meta);
  });

  lines.push('');
  lines.push('  ' + C.dim + `Fortschritt: ` + C.reset + C.green + `${doneN}/${tasks.length}` + C.reset +
    C.dim + `  ·  Teams: ULTRA (12)  ·  Modell: Fable 5  ·  Werkzeuge: verbunden` + C.reset);
  lines.push('  ' + C.dim + 'Ausfuehren mit Aussenwirkung erst nach Freigabe · Security defensiv' + C.reset);
  lines.push('');
  return lines.join('\n');
}

async function browse(query, headless) {
  let chromium;
  try { ({ chromium } = await import('playwright-core')); }
  catch { try { ({ chromium } = await import('playwright')); } catch {
    console.error(C.gold + 'Playwright fehlt. Installiere es einmalig:' + C.reset + '\n  npm i playwright-core\n  npx playwright install chromium');
    process.exit(1);
  }}
  const exe = process.env.BLIN_CHROMIUM || process.env.PLAYWRIGHT_CHROMIUM || undefined;
  const proxyUrl = process.env.BLIN_PROXY || process.env.HTTPS_PROXY || process.env.https_proxy || null;
  console.log(C.coral + '● Blin' + C.reset + ' oeffnet einen echten Browser und sucht: ' + C.b + query + C.reset);
  const opts = { headless };
  if (exe) opts.executablePath = exe;
  if (proxyUrl) opts.proxy = { server: proxyUrl };
  const browser = await chromium.launch(opts);
  const page = await browser.newPage();
  const url = 'https://duckduckgo.com/?q=' + encodeURIComponent(query);
  await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);
  const title = await page.title();
  const shot = path.join(__dirname, 'blin-browse.png');
  await page.screenshot({ path: shot });
  console.log(C.green + '✓' + C.reset + ' Seite geoeffnet: ' + C.b + title + C.reset);
  console.log(C.green + '✓' + C.reset + ' Screenshot: ' + shot);
  console.log(C.dim + '  → In Claude Code kann Blin ab hier klicken, Formulare fuellen, Daten holen — mit deiner Freigabe.' + C.reset);
  await browser.close();
}

// ---- main ----
if (has('--browse')) {
  await browse(val('--browse') || 'ULTRA AI ENTERPRISE OS', has('--headless'));
} else {
  const data = loadTasks();
  if (has('--once')) { console.clear(); process.stdout.write(render(data) + '\n'); }
  else {
    const tick = () => { console.clear(); process.stdout.write(render(data) + '\n' +
      '  ' + C.dim + '⌃C zum Beenden · Aufgaben in tasks.json' + C.reset + '\n'); };
    tick(); setInterval(tick, 1000);
  }
}
