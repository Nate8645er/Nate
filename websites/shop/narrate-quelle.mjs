// Narriertes System-Screencast pro Abo: echte Oberfläche + sichtbarer Cursor +
// Klick-Ripples + deutsche Stimme (piper), Audio deterministisch synchron.
import { chromium } from 'playwright-core';
import { readFileSync, mkdirSync, existsSync } from 'fs';
import { execSync } from 'node:child_process';
import { rename } from 'node:fs/promises';

const SP = '/tmp/claude-0/-home-user-Nate/49db2b86-1d06-54de-afb7-5038c7ccc25a/scratchpad';
const FF = SP + '/node_modules/@ffmpeg-installer/linux-x64/ffmpeg';
const PIPER_MODEL = SP + '/thorsten_high.onnx';  // klare Thorsten-Stimme (High-Quality), ohne Effekte
const BASE = 'http://localhost:3000';
const PLAN = process.argv[2];               // z.B. FREE
const OUTDIR = SP + '/narr'; mkdirSync(OUTDIR, { recursive: true });
const WORK = SP + '/narr/' + PLAN.toLowerCase(); mkdirSync(WORK, { recursive: true });
const size = { width: 1280, height: 720 };
const PREROLL = 2000;                        // fixe Vorlaufzeit je Segment (nav+cursor)

const tiers = JSON.parse(readFileSync(SP + '/tiers.json', 'utf8'));
const T = tiers.find(t => t.plan === PLAN);
if (!T) { console.error('plan not found', PLAN); process.exit(1); }

// Segmente: Intro + je Schritt + Outro
const segs = [];
segs.push({ text: `Willkommen zu Ihrem ${T.name}-Abo bei A I Command Center. Ich zeige Ihnen jetzt Ihr komplettes K I System, Schritt für Schritt.`, href: '/dashboard' });
T.schritte.forEach((s, i) => {
  segs.push({ text: `Schritt ${i + 1} von ${T.schritte.length}: ${s.titel}. ${s.text}`, href: s.href || '/dashboard' });
});
segs.push({ text: `Damit ist Ihr ${T.name}-Team startklar. Viel Erfolg mit Ihrem K I System!`, href: '/dashboard' });

// 1) TTS je Segment + Dauer messen
function ttsDuration(wav) {
  const out = execSync(`"${FF}" -hide_banner -i "${wav}" 2>&1 || true`, { encoding: 'utf8' });
  const m = out.match(/Duration:\s*(\d+):(\d+):(\d+\.\d+)/);
  if (!m) return 3000;
  return Math.round(((+m[1]) * 3600 + (+m[2]) * 60 + parseFloat(m[3])) * 1000);
}
const durs = [];
segs.forEach((sg, i) => {
  const wav = `${WORK}/seg_${i}.wav`;
  execSync(`printf '%s' ${JSON.stringify(sg.text)} | piper --model "${PIPER_MODEL}" --output_file "${wav}"`, { stdio: 'ignore' });
  durs[i] = ttsDuration(wav);
});
console.log(PLAN, 'segments:', segs.length, 'audio ms:', durs.reduce((a, b) => a + b, 0));

// 2) Screencast aufnehmen
const CURSOR = () => {
  const c = document.createElement('div');
  c.id = '__cur';
  c.style.cssText = 'position:fixed;z-index:2147483647;width:24px;height:24px;margin:-12px 0 0 -12px;border-radius:50%;background:rgba(255,140,42,.45);border:2px solid #fff;box-shadow:0 0 14px rgba(255,140,42,.9);pointer-events:none;left:640px;top:380px;transition:left .55s cubic-bezier(.4,0,.2,1),top .55s cubic-bezier(.4,0,.2,1)';
  (document.documentElement || document.body).appendChild(c);
  window.addEventListener('mousemove', e => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  window.__ripple = (x, y) => {
    const r = document.createElement('div');
    r.style.cssText = 'position:fixed;z-index:2147483646;left:' + x + 'px;top:' + y + 'px;width:12px;height:12px;margin:-6px 0 0 -6px;border-radius:50%;border:3px solid #ff8c2a;pointer-events:none;opacity:1;transition:all .55s ease';
    (document.documentElement || document.body).appendChild(r);
    requestAnimationFrame(() => { r.style.width = '52px'; r.style.height = '52px'; r.style.margin = '-26px 0 0 -26px'; r.style.opacity = '0'; });
    setTimeout(() => r.remove(), 600);
  };
};

const browser = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome', args: ['--no-sandbox'] });
const ctx = await browser.newContext({ viewport: size, recordVideo: { dir: WORK, size } });
await ctx.addInitScript(`localStorage.setItem('acc-plan','${PLAN}');localStorage.setItem('acc-firma','Ihre Firma');localStorage.setItem('acc-branche','Marketing/Agentur');localStorage.setItem('acc-groesse','2-10');`);
await ctx.addInitScript(CURSOR);
const page = await ctx.newPage();

let cur = null;
const targets = [[640, 300], [430, 440], [860, 400], [520, 520], [760, 300], [380, 360], [900, 480], [600, 420]];
for (let i = 0; i < segs.length; i++) {
  const sg = segs[i];
  if (sg.href !== cur) {
    try { await page.goto(BASE + sg.href, { waitUntil: 'domcontentloaded', timeout: 45000 }); }
    catch { await page.goto(BASE + sg.href, { waitUntil: 'load', timeout: 45000 }); }
    cur = sg.href;
  }
  await page.waitForTimeout(1150);
  // Cursor zu einem Zielpunkt bewegen (sichtbar animiert) + Klick-Ripple
  const [tx, ty] = targets[i % targets.length];
  await page.mouse.move(tx, ty, { steps: 12 });
  await page.waitForTimeout(650);
  await page.evaluate(([x, y]) => window.__ripple && window.__ripple(x, y), [tx, ty]);
  await page.waitForTimeout(PREROLL - 1150 - 650);   // Rest der Vorlaufzeit
  // Halten für die Sprechdauer, dabei sanft scrollen
  const hold = durs[i];
  const t0 = Date.now();
  await page.evaluate(async (ms) => {
    const H = Math.max(0, document.body.scrollHeight - window.innerHeight);
    const start = performance.now();
    return new Promise(res => {
      function tick(now) {
        const p = Math.min(1, (now - start) / ms);
        window.scrollTo(0, Math.round(H * 0.6 * p));
        if (p < 1) requestAnimationFrame(tick); else res();
      }
      requestAnimationFrame(tick);
    });
  }, hold);
  const rest = hold - (Date.now() - t0);
  if (rest > 0) await page.waitForTimeout(rest);
}
const video = page.video();
await ctx.close();
const vpath = await video.path();
await rename(vpath, `${WORK}/screen.webm`);
await browser.close();

// 3) Audiospur bauen: je Segment [PREROLL ms Stille + Sprache], dann concat
execSync(`"${FF}" -y -f lavfi -t ${PREROLL / 1000} -i anullsrc=r=22050:cl=mono "${WORK}/sil.wav" 2>/dev/null`, { stdio: 'ignore' });
const parts = [];
for (let i = 0; i < segs.length; i++) { parts.push(`${WORK}/sil.wav`); parts.push(`${WORK}/seg_${i}.wav`); }
const listFile = `${WORK}/list.txt`;
execSync(`printf '%s\\n' ${parts.map(p => `"file '${p}'"`).join(' ')} > "${listFile}"`);
execSync(`"${FF}" -y -f concat -safe 0 -i "${listFile}" -ar 44100 -ac 2 "${WORK}/narration.wav" 2>/dev/null`, { stdio: 'ignore' });

// 4) Mux: Video (H.264) + Stimme (AAC)
const out = `${OUTDIR}/anleitung-${PLAN.toLowerCase()}.mp4`;
execSync(`"${FF}" -y -i "${WORK}/screen.webm" -i "${WORK}/narration.wav" -map 0:v:0 -map 1:a:0 -c:v libx264 -pix_fmt yuv420p -profile:v high -crf 22 -preset veryfast -c:a aac -b:a 128k -movflags +faststart -shortest "${out}" 2>/dev/null`, { stdio: 'ignore' });
console.log('DONE', out);
