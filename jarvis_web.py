"""JARVIS // COMMAND CENTER - Jarvis im Browser, 1:1 im Kommandozentralen-Look.

Start auf dem eigenen Rechner:
    python jarvis_web.py            # echtes Gehirn (Claude bzw. Ollama)
    python jarvis_web.py --demo     # ohne API-Schlüssel: simulierte Antworten

Dann im Browser http://localhost:8000 öffnen. Die Zentrale zeigt wie im
Vorbild-Video: rotierenden Globus, Reaktorkern mit Hex-Zentrum,
Fokus-Wellenform (reagiert live auf das Mikrofon und auf Jarvis' Stimme),
Kennzahlen-Karten, Alarm-Leiste, Modul-Liste, Live-Gespräch und
System-Log. Unter http://localhost:8000/brain läuft die Neuronen-Kugel
als Vollbild - wie auf dem Laptop im Video.

Sprachfunktion: Mikrofon über die Web Speech API (Chrome/Edge, Deutsch),
Antworten werden satzweise gestreamt und sofort gesprochen.
"""

import argparse
import json
import time

from flask import Flask, Response, request

from jarvis.core.agents import AgentRegistry
from jarvis.core.claude_client import ClaudeClient
from jarvis.core.conversation import ConversationManager
from jarvis.core.errors import LLMError
from jarvis.core.ollama_client import OllamaClient
from jarvis.core.skills import SkillRegistry
from jarvis.memory.long_term import LongTermMemory
from jarvis.plugins.loader import PluginManager
from jarvis.utils.config_loader import PROJECT_ROOT, load_config
from jarvis.utils.latency import TurnTimer
from jarvis.utils.secrets import ensure_secrets_file, load_secret


class DemoClient:
    """Simuliertes Gehirn für den Test ohne API-Schlüssel (--demo)."""

    def chat_stream(self, prompt=None, messages=None):
        answer = (
            "Willkommen im Command Center. "
            "Der erste Satz kommt sofort, wie du siehst. "
            "Die weiteren Sätze entstehen, während der erste schon "
            "gesprochen wird. Genau so fühlt sich das Streaming an."
        )
        for word in answer.split(" "):
            time.sleep(0.1)
            yield word + " "


def _build_client(config: dict, demo: bool):
    """Gleiche Gehirn-Auswahl wie in main.py: Claude, sonst Ollama."""
    if demo:
        return DemoClient()
    if config.get("provider", "ollama") == "claude":
        claude_cfg = config.get("claude", {})
        claude = ClaudeClient(
            model=claude_cfg.get("model", "claude-fable-5"),
            max_tokens=claude_cfg.get("max_tokens", 16000),
            fallback_model=claude_cfg.get("fallback_model", "claude-opus-4-8"),
        )
        if claude.is_available():
            return claude
        print(
            "Hinweis: kein Anthropic-API-Schlüssel gefunden - nutze Ollama. "
            "(Oder starte mit --demo für simulierte Antworten.)"
        )
    ollama_cfg = config["ollama"]
    return OllamaClient(
        base_url=ollama_cfg["base_url"],
        model=ollama_cfg["model"],
        timeout=ollama_cfg.get("timeout_seconds", 120),
    )


def create_app(demo: bool = False) -> Flask:
    config = load_config()
    client = _build_client(config, demo)

    memory_file = PROJECT_ROOT / config.get("memory", {}).get(
        "file", "data/memory/long_term.json"
    )
    memory = LongTermMemory(memory_file)
    assistant_cfg = config.get("assistant", {})
    system_prompt = assistant_cfg.get(
        "system_prompt", "Du bist ein hilfsbereiter Assistent."
    ) + memory.as_prompt_context()
    conversation = ConversationManager(
        client=client,
        system_prompt=system_prompt,
        max_history_messages=assistant_cfg.get("max_history_messages", 20),
    )

    # Für die Status-Panels: Plugins, Skills und Abteilungen laden
    plugins = PluginManager()
    plugins.load_plugins()
    skills = SkillRegistry(PROJECT_ROOT / config.get("skills", {}).get("path", "skills"))
    skills.load()
    agents = AgentRegistry([
        PROJECT_ROOT / p
        for p in config.get("agents", {}).get("paths", ["ultra-enterprise-os/agents"])
    ])
    agents.load()

    speech_cfg = config.get("speech", {})

    def status_data() -> dict:
        """Echte Systemdaten für die Panels der Zentrale."""
        if demo:
            brain = "DEMO-MODUS"
        elif isinstance(client, ClaudeClient):
            brain = f"CLAUDE // {client.model}"
        else:
            brain = f"OLLAMA // {getattr(client, 'model', '?')}"
        ears = "DEEPGRAM" if load_secret("deepgram_api_key", "DEEPGRAM_API_KEY") \
            else "GOOGLE WEB SPEECH"
        voice = "ELEVENLABS FLASH" if (
            load_secret("elevenlabs_api_key", "ELEVENLABS_API_KEY")
            and speech_cfg.get("elevenlabs_voice_id")
        ) else "WINDOWS / BROWSER"
        return {
            "brain": brain,
            "ears": ears,
            "voice": voice,
            "plugins": [p.name for p in plugins.plugins],
            "commands": sorted(plugins.command_map),
            "skills": sorted(skills.skills),
            "departments": sorted(agents.agents),
        }

    app = Flask("jarvis_web")

    @app.get("/")
    def index() -> Response:
        return Response(PAGE, mimetype="text/html")

    @app.get("/brain")
    def brain() -> Response:
        return Response(BRAIN_PAGE, mimetype="text/html")

    @app.get("/api/status")
    def status():
        return status_data()

    @app.post("/api/chat")
    def chat():
        text = (request.get_json(silent=True) or {}).get("text", "").strip()
        if not text:
            return {"error": "Kein Text angekommen."}, 400

        def generate():
            timer = TurnTimer()
            timer.start()
            try:
                for sentence in conversation.ask_stream(text):
                    timer.mark("erster Satz")
                    yield json.dumps(
                        {"type": "sentence", "text": sentence}, ensure_ascii=False
                    ) + "\n"
            except LLMError as e:
                yield json.dumps(
                    {"type": "error", "text": str(e)}, ensure_ascii=False
                ) + "\n"
                return
            timer.mark("Antwort komplett")
            timer.log()
            yield json.dumps(
                {"type": "timing", "report": timer.report()}, ensure_ascii=False
            ) + "\n"

        # NDJSON: eine JSON-Zeile pro Satz, der Browser liest sie sofort
        return Response(generate(), mimetype="application/x-ndjson")

    @app.post("/api/reset")
    def reset():
        conversation.reset()
        return {"ok": True}

    return app


PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JARVIS // COMMAND CENTER</title>
<style>
  :root {
    --amber: #ff8c1a; --amber2: #ffab40; --dim: #8a5a20; --deep: #b35900;
    --glow: rgba(255,140,26,.5); --bg: #070503; --panel: #0f0a06;
    --line: #241505; --green: #43c96b; --red: #e03535; --text: #ffd9a8;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body {
    margin: 0; display: flex; flex-direction: column;
    background: radial-gradient(1400px 500px at 60% -15%, #190d03 0%, var(--bg) 55%);
    color: var(--text);
    font-family: "Cascadia Mono", Consolas, "Courier New", monospace;
    font-size: 12px; overflow: hidden;
  }

  /* ---------- Kopfzeile mit Ticker ---------- */
  header {
    display: flex; align-items: center; gap: 12px; padding: 6px 12px;
    border-bottom: 1px solid var(--line); background: #0b0704;
  }
  .logo { color: var(--amber); font-weight: bold; letter-spacing: .14em; font-size: 13px;
          text-shadow: 0 0 10px var(--glow); white-space: nowrap; }
  .badge { background: var(--red); color: #fff; font-size: 9px; padding: 2px 7px;
           border-radius: 2px; letter-spacing: .12em; animation: blink 1.6s infinite; }
  @keyframes blink { 50% { opacity: .45; } }
  #ticker { flex: 1; display: flex; gap: 18px; overflow: hidden; white-space: nowrap;
            font-size: 10px; color: var(--dim); }
  #ticker .up { color: var(--green); } #ticker .down { color: var(--red); }
  .clock { color: var(--amber2); font-size: 13px; }
  header a { color: var(--dim); font-size: 10px; text-decoration: none; letter-spacing: .1em; }
  header a:hover { color: var(--amber); }

  /* ---------- Raster ---------- */
  #wrap { flex: 1; display: flex; flex-direction: column; gap: 6px; padding: 6px 8px; min-height: 0; }
  .r { display: grid; gap: 6px; min-height: 0; }
  #r1 { grid-template-columns: 1.05fr 1.25fr 1.15fr .85fr; flex: 0 0 172px; }
  #r2 { grid-template-columns: 2fr 1fr; flex: 0 0 64px; }
  #r3 { grid-template-columns: repeat(5, 1fr); flex: 0 0 58px; }
  #alertbar { flex: 0 0 22px; background: #2a0705; border: 1px solid #571510;
              color: #ff9d8a; display: flex; align-items: center; overflow: hidden;
              font-size: 10px; letter-spacing: .06em; }
  #alertbar span { padding-left: 100%; display: inline-block; white-space: nowrap;
                   animation: crawl 30s linear infinite; }
  @keyframes crawl { to { transform: translateX(-100%); } }
  #r5 { grid-template-columns: .8fr 2.3fr 1fr; flex: 1; }

  .p { background: var(--panel); border: 1px solid var(--line); border-radius: 3px;
       padding: 6px 8px; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
  .p h2 { margin: 0 0 4px; font-size: 9px; letter-spacing: .2em; color: var(--amber);
          border-bottom: 1px solid var(--line); padding-bottom: 3px;
          text-shadow: 0 0 7px var(--glow); display: flex; justify-content: space-between; }
  .p h2 .sub { color: var(--dim); letter-spacing: .05em; }
  canvas { width: 100%; height: 100%; display: block; flex: 1; min-height: 0; }

  /* Metrik-Zeilen (Reihe 1, Spalte 2) */
  .metric { display: grid; grid-template-columns: 86px 1fr 52px; gap: 6px;
            align-items: center; padding: 2.5px 0; font-size: 10px; }
  .metric .k { color: var(--dim); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .metric .bar { height: 6px; background: #1b1006; border: 1px solid var(--line); position: relative; }
  .metric .bar i { position: absolute; inset: 0; right: auto; background:
      linear-gradient(90deg, var(--deep), var(--amber)); box-shadow: 0 0 6px var(--glow); }
  .metric .v { text-align: right; color: var(--green); }

  /* Protokoll-Panel */
  #proto { font-size: 9.5px; line-height: 1.65; color: var(--dim); overflow: hidden; }
  #proto b { color: var(--green); font-weight: normal; }
  #proto i { color: var(--amber2); font-style: normal; }

  /* Kennzahlen-Karten (Reihe 3) */
  .card { justify-content: center; }
  .card .num { font-size: 21px; color: #ffe9c9; text-shadow: 0 0 10px var(--glow); line-height: 1.1; }
  .card .lbl { font-size: 8.5px; letter-spacing: .18em; color: var(--dim); }
  .card .delta { font-size: 9px; color: var(--green); }

  /* Module / Gespräch / Log (Reihe 5) */
  #modules { font-size: 10px; line-height: 1.9; overflow-y: auto; color: var(--dim); }
  #modules .grp { color: var(--amber); letter-spacing: .15em; font-size: 8.5px; margin-top: 5px; }
  #modules .it b { color: var(--text); font-weight: normal; }
  #modules .it .ok { color: var(--green); float: right; font-size: 9px; }

  #chat { flex: 1; overflow-y: auto; padding-right: 4px; }
  .row { margin: 6px 0; line-height: 1.55; white-space: pre-wrap; font-size: 12.5px; }
  .row .tag { font-size: 9px; letter-spacing: .14em; margin-right: 8px; }
  .row.user .tag { color: var(--green); } .row.user { color: #ffe9c9; }
  .row.jarvis .tag { color: var(--amber); text-shadow: 0 0 7px var(--glow); }
  .row.timing { color: var(--dim); font-size: 10px; }
  .row.error { color: var(--red); }

  #log { flex: 1; overflow-y: auto; font-size: 9.5px; line-height: 1.6; color: var(--dim); }
  #log .t { color: #5a3c14; margin-right: 5px; }
  #log .ok { color: var(--green); } #log .warn { color: var(--red); }

  /* Eingabezeile + Statuszeile */
  #inbar { display: flex; gap: 6px; padding: 0 8px 4px; }
  #text { flex: 1; background: var(--panel); border: 1px solid var(--line); border-radius: 3px;
          color: var(--text); font: inherit; font-size: 13px; padding: 9px 12px; outline: none; }
  #text:focus { border-color: var(--deep); box-shadow: 0 0 12px rgba(255,140,26,.12); }
  button { background: #170e05; color: var(--amber); border: 1px solid var(--deep);
           border-radius: 3px; font: inherit; padding: 9px 14px; cursor: pointer;
           letter-spacing: .12em; text-shadow: 0 0 7px var(--glow); }
  button:hover { background: #241505; }
  button.rec { color: #fff; background: var(--red); border-color: var(--red);
               text-shadow: none; animation: blink 1s infinite; }
  button:disabled { opacity: .4; cursor: default; }
  #statusbar { display: flex; gap: 18px; padding: 3px 12px 6px; font-size: 9px;
               letter-spacing: .12em; color: var(--dim); border-top: 1px solid var(--line); }
  #statusbar .g { color: var(--green); }
</style>
</head>
<body>
<header>
  <span class="logo">JARVIS // COMMAND CENTER</span>
  <span class="badge">LIVE-EINSATZ</span>
  <span id="ticker"></span>
  <a href="/brain" target="_blank">[ NEURO-ANSICHT ]</a>
  <label style="font-size:10px;color:var(--dim)"><input type="checkbox" id="voice" checked> STIMME</label>
  <span class="clock" id="clock">--:--:--</span>
</header>

<div id="wrap">
  <div class="r" id="r1">
    <div class="p"><h2>ORBITALE ÜBERSICHT <span class="sub">SAT-7</span></h2><canvas id="globe"></canvas></div>
    <div class="p"><h2>MISSIONS-METRIKEN <span class="sub">LIVE</span></h2><div id="metrics"></div></div>
    <div class="p"><h2>REAKTORKERN <span class="sub" id="corestate">STABIL</span></h2><canvas id="reactor"></canvas></div>
    <div class="p"><h2>K-PROTOKOLL</h2><div id="proto">wird geladen ...</div></div>
  </div>

  <div class="r" id="r2">
    <div class="p"><h2>FOKUS-WELLENFORM <span class="sub" id="wavestate">BEREIT</span></h2><canvas id="wave"></canvas></div>
    <div class="p"><h2>ENERGIE-MATRIX</h2><canvas id="energy"></canvas></div>
  </div>

  <div class="r" id="r3">
    <div class="p card"><div class="num" id="c-first">-</div><div class="lbl">ERSTER SATZ</div><div class="delta" id="c-first-d">&nbsp;</div></div>
    <div class="p card"><div class="num" id="c-turns">0</div><div class="lbl">RUNDEN</div><div class="delta">Sitzung</div></div>
    <div class="p card"><div class="num" id="c-plugins">-</div><div class="lbl">PLUGINS</div><div class="delta" id="c-cmds">&nbsp;</div></div>
    <div class="p card"><div class="num" id="c-skills">-</div><div class="lbl">SKILLS</div><div class="delta">bereit</div></div>
    <div class="p card"><div class="num" id="c-depts">-</div><div class="lbl">ABTEILUNGEN</div><div class="delta">Konzern online</div></div>
  </div>

  <div id="alertbar"><span id="alerttext">+++ ALLE SYSTEME NOMINAL +++ STREAMING AKTIV +++ SATZWEISE SPRACHAUSGABE BEREIT +++ MIKROFON AUF ABRUF +++ KONZERN IM STANDBY +++</span></div>

  <div class="r" id="r5">
    <div class="p"><h2>MODULE</h2><div id="modules">wird geladen ...</div></div>
    <div class="p"><h2>LIVE-GESPRÄCH <span class="sub">KANAL 01</span></h2><div id="chat"></div></div>
    <div class="p"><h2>SYSTEM-LOG</h2><div id="log"></div></div>
  </div>
</div>

<div id="inbar">
  <button type="button" id="mic" title="Sprechen (Chrome/Edge)">🎙 MIC</button>
  <input type="text" id="text" placeholder="> Befehl oder Frage an JARVIS ..." autocomplete="off" autofocus>
  <button type="button" id="send">SENDEN</button>
</div>
<div id="statusbar">
  <span class="g">● BEREIT</span>
  <span id="sb-brain">GEHIRN: ...</span>
  <span id="sb-ears">OHREN: ...</span>
  <span id="sb-voice">STIMME: ...</span>
</div>

<script>
const $ = id => document.getElementById(id);
const logBox = $('log');
function logLine(text, cls) {
  const el = document.createElement('div');
  const t = new Date().toLocaleTimeString('de-CH');
  el.innerHTML = '<span class="t">' + t + '</span><span class="' + (cls || '') + '">' + text + '</span>';
  logBox.appendChild(el);
  logBox.scrollTop = logBox.scrollHeight;
}

/* ---------- Uhr + Ticker ---------- */
setInterval(() => { $('clock').textContent = new Date().toLocaleTimeString('de-CH'); }, 500);
const tickItems = ['STR', 'NRV', 'PWR', 'SAT', 'LNK', 'MEM', 'CPU'];
function drawTicker() {
  $('ticker').innerHTML = tickItems.map(n => {
    const v = (Math.random() * 4 - 1.6).toFixed(2);
    const cls = v >= 0 ? 'up' : 'down';
    return n + ' <span class="' + cls + '">' + (v >= 0 ? '+' : '') + v + '%' + (v >= 0 ? ' ▲' : ' ▼') + '</span>';
  }).join('&nbsp;&nbsp;');
}
drawTicker(); setInterval(drawTicker, 5000);

/* ---------- Systemstatus (echte Daten) ---------- */
fetch('/api/status').then(r => r.json()).then(s => {
  $('c-plugins').textContent = s.plugins.length;
  $('c-cmds').textContent = s.commands.length + ' Befehle';
  $('c-skills').textContent = s.skills.length;
  $('c-depts').textContent = s.departments.length;
  $('sb-brain').textContent = 'GEHIRN: ' + s.brain;
  $('sb-ears').textContent = 'OHREN: ' + s.ears;
  $('sb-voice').textContent = 'STIMME: ' + s.voice;
  const m = $('modules');
  m.innerHTML =
    '<div class="grp">▾ PLUGINS</div>' +
    s.plugins.map(p => '<div class="it">▸ <b>' + p.toUpperCase() + '</b><span class="ok">AKTIV</span></div>').join('') +
    '<div class="grp">▾ SKILLS</div>' +
    s.skills.map(x => '<div class="it">▸ <b>' + x + '</b><span class="ok">OK</span></div>').join('') +
    '<div class="grp">▾ KONZERN</div>' +
    s.departments.map(d => '<div class="it">▸ <b>' + d.replace('ultra-','').toUpperCase() + '</b></div>').join('');
  const proto = $('proto');
  proto.innerHTML =
    'GEHIRN <b>ONLINE</b><br>' + '<i>' + s.brain + '</i><br>' +
    'OHREN <b>ONLINE</b><br>' + '<i>' + s.ears + '</i><br>' +
    'STIMME <b>ONLINE</b><br>' + '<i>' + s.voice + '</i><br>' +
    'MODULE <b>' + (s.plugins.length + s.skills.length) + ' GELADEN</b><br>' +
    'KONZERN <b>' + s.departments.length + ' ABTEILUNGEN</b>';
  const met = $('metrics');
  const rows = [['UPLINK', 92], ['NEURALNETZ', 84], ['SPRACHKERN', 77], ['SPEICHER', 63],
                ['ANALYSE', 88], ['SCHILDE', 100]];
  met.innerHTML = rows.map(([k, v]) =>
    '<div class="metric"><span class="k">' + k + '</span>' +
    '<span class="bar"><i style="width:' + v + '%"></i></span>' +
    '<span class="v">' + v + '%</span></div>').join('');
  logLine('Systemstatus geladen: ' + s.plugins.length + ' Plugins, ' +
          s.skills.length + ' Skills, ' + s.departments.length + ' Abteilungen', 'ok');
});

/* ---------- Gespräch mit Streaming + Stimme ---------- */
let turns = 0;
function row(cls, tag, text) {
  const el = document.createElement('div');
  el.className = 'row ' + cls;
  el.innerHTML = '<span class="tag">' + tag + '</span>';
  const body = document.createElement('span');
  body.textContent = text;
  el.appendChild(body);
  $('chat').appendChild(el);
  $('chat').scrollTop = $('chat').scrollHeight;
  return body;
}
function speak(sentence) {
  if (!$('voice').checked || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(sentence);
  u.lang = 'de-DE';
  speechSynthesis.speak(u);
}
async function send(text) {
  if (!text.trim()) return;
  $('text').value = '';
  $('send').disabled = true;
  row('user', 'DU //', text);
  logLine('Anfrage gesendet (' + text.length + ' Zeichen)');
  const body = row('jarvis', 'JARVIS //', '');
  const t0 = performance.now();
  let firstMs = null;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const reader = res.body.getReader();
    const dec = new TextDecoder();
    let buf = '';
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += dec.decode(value, {stream: true});
      let i;
      while ((i = buf.indexOf('\\n')) >= 0) {
        const line = buf.slice(0, i).trim(); buf = buf.slice(i + 1);
        if (!line) continue;
        const msg = JSON.parse(line);
        if (msg.type === 'sentence') {
          if (firstMs === null) {
            firstMs = performance.now() - t0;
            $('c-first').textContent = (firstMs / 1000).toFixed(1) + 's';
            $('c-first-d').textContent = 'letzte Runde';
          }
          body.textContent += (body.textContent ? ' ' : '') + msg.text;
          $('chat').scrollTop = $('chat').scrollHeight;
          speak(msg.text);
        } else if (msg.type === 'timing') {
          turns++;
          $('c-turns').textContent = turns;
          row('timing', '//', '⏱ ' + msg.report);
          logLine('⏱ ' + msg.report, 'ok');
        } else if (msg.type === 'error') {
          body.parentElement.classList.add('error');
          body.textContent = '⚠ ' + msg.text;
          $('alerttext').textContent = '+++ STÖRUNG: ' + msg.text + ' +++';
          logLine('Fehler: ' + msg.text, 'warn');
        }
      }
    }
  } catch (e) {
    body.parentElement.classList.add('error');
    body.textContent = '⚠ Verbindung verloren: ' + e;
    logLine('Verbindung verloren', 'warn');
  }
  $('send').disabled = false;
  $('text').focus();
}
$('send').addEventListener('click', () => send($('text').value));
$('text').addEventListener('keydown', e => { if (e.key === 'Enter') send($('text').value); });

/* ---------- Mikrofon: Spracherkennung + echte Wellenform ---------- */
let analyser = null;
async function micWave() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    const ac = new (window.AudioContext || window.webkitAudioContext)();
    const srcNode = ac.createMediaStreamSource(stream);
    analyser = ac.createAnalyser();
    analyser.fftSize = 128;
    srcNode.connect(analyser);
    logLine('Mikrofon-Wellenform aktiv', 'ok');
  } catch (e) { logLine('Kein Mikrofon-Zugriff: Wellenform simuliert', 'warn'); }
}
const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!Rec) {
  $('mic').disabled = true;
  $('mic').title = 'Dieser Browser kann keine Spracherkennung (nimm Chrome oder Edge).';
} else {
  const rec = new Rec();
  rec.lang = 'de-DE'; rec.interimResults = false;
  let on = false;
  rec.onresult = e => { logLine('Verstanden: Spracheingabe', 'ok'); send(e.results[0][0].transcript); };
  rec.onend = rec.onerror = () => {
    on = false; $('mic').classList.remove('rec'); $('mic').textContent = '🎙 MIC';
    $('wavestate').textContent = 'BEREIT';
  };
  $('mic').addEventListener('click', async () => {
    if (on) { rec.stop(); return; }
    if (!analyser) await micWave();
    on = true; $('mic').classList.add('rec'); $('mic').textContent = '⏹ STOP';
    $('wavestate').textContent = 'AUFNAHME';
    rec.start();
  });
}

/* ---------- Fokus-Wellenform (reagiert auf Mikro und Stimme) ---------- */
(function () {
  const cv = $('wave'), ctx = cv.getContext('2d');
  const data = new Uint8Array(64);
  function draw(ts) {
    const w = cv.width = cv.clientWidth, h = cv.height = cv.clientHeight;
    ctx.clearRect(0, 0, w, h);
    const speaking = window.speechSynthesis && speechSynthesis.speaking;
    let levels = [];
    if (analyser) { analyser.getByteFrequencyData(data); levels = [...data.slice(0, 48)].map(v => v / 255); }
    else levels = Array.from({length: 48}, (_, i) => 0.05 + 0.04 * Math.sin(ts / 300 + i));
    if (speaking) levels = levels.map((v, i) =>
      Math.max(v, 0.25 + 0.6 * Math.abs(Math.sin(ts / 90 + i * 0.7)) * Math.random()));
    const bw = w / levels.length;
    levels.forEach((v, i) => {
      const bh = Math.max(2, v * (h - 6));
      ctx.fillStyle = 'rgba(255,140,26,' + (0.35 + v * 0.65) + ')';
      ctx.shadowColor = 'rgba(255,140,26,.8)'; ctx.shadowBlur = v * 10;
      ctx.fillRect(i * bw + 1, (h - bh) / 2, bw - 2, bh);
    });
    ctx.shadowBlur = 0;
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

/* ---------- Energie-Matrix (grüne Sparkline) ---------- */
(function () {
  const cv = $('energy'), ctx = cv.getContext('2d');
  const hist = Array.from({length: 60}, () => Math.random() * 0.5 + 0.25);
  setInterval(() => { hist.shift(); hist.push(Math.random() * 0.6 + 0.2); }, 500);
  function draw() {
    const w = cv.width = cv.clientWidth, h = cv.height = cv.clientHeight;
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = '#43c96b'; ctx.lineWidth = 1.4;
    ctx.shadowColor = 'rgba(67,201,107,.7)'; ctx.shadowBlur = 6;
    ctx.beginPath();
    hist.forEach((v, i) => {
      const x = i / (hist.length - 1) * w, y = h - v * h;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke(); ctx.shadowBlur = 0;
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

/* ---------- Globus (dunkler Planet mit orangen Lichtern) ---------- */
(function () {
  const cv = $('globe'), ctx = cv.getContext('2d');
  const N = 240, pts = [];
  for (let i = 0; i < N; i++) {
    const t = Math.acos(2 * Math.random() - 1), p = Math.random() * Math.PI * 2;
    pts.push([Math.sin(t) * Math.cos(p), Math.sin(t) * Math.sin(p), Math.cos(t)]);
  }
  function draw(ts) {
    const w = cv.width = cv.clientWidth, h = cv.height = cv.clientHeight;
    ctx.clearRect(0, 0, w, h);
    const R = Math.min(w, h) * 0.42, cx = w / 2, cy = h / 2, a = ts / 9000;
    // Planetenscheibe
    const g = ctx.createRadialGradient(cx - R * 0.3, cy - R * 0.3, R * 0.1, cx, cy, R);
    g.addColorStop(0, '#191009'); g.addColorStop(1, '#050302');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.fill();
    // Stadtlichter (nur Vorderseite)
    for (const [x, y, z] of pts) {
      const x2 = x * Math.cos(a) - z * Math.sin(a);
      const z2 = x * Math.sin(a) + z * Math.cos(a);
      if (z2 < 0.05) continue;
      const flick = 0.5 + 0.5 * Math.sin(ts / 400 + x * 20 + y * 30);
      ctx.fillStyle = 'rgba(255,150,40,' + (0.25 + 0.6 * z2 * flick) + ')';
      ctx.beginPath();
      ctx.arc(cx + x2 * R * 0.94, cy + y * R * 0.94, 0.9 + z2, 0, 7);
      ctx.fill();
    }
    // Atmosphären-Rand
    ctx.strokeStyle = 'rgba(255,140,26,.35)'; ctx.lineWidth = 1.4;
    ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke();
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

/* ---------- Reaktorkern mit Hex-Zentrum ---------- */
(function () {
  const cv = $('reactor'), ctx = cv.getContext('2d');
  function hex(cx, cy, r, rot) {
    ctx.beginPath();
    for (let i = 0; i < 6; i++) {
      const a = rot + i * Math.PI / 3;
      const x = cx + Math.cos(a) * r, y = cy + Math.sin(a) * r;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.closePath();
  }
  function draw(ts) {
    const w = cv.width = cv.clientWidth, h = cv.height = cv.clientHeight;
    const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.46;
    ctx.clearRect(0, 0, w, h);
    const speaking = window.speechSynthesis && speechSynthesis.speaking;
    $('corestate').textContent = speaking ? 'SPRICHT' : 'STABIL';
    const pulse = 0.85 + 0.15 * Math.sin(ts / (speaking ? 80 : 650));
    // Kernglut
    const g = ctx.createRadialGradient(cx, cy, 1, cx, cy, R * 0.5 * pulse);
    g.addColorStop(0, 'rgba(255,205,120,.95)');
    g.addColorStop(0.45, 'rgba(255,120,20,.5)');
    g.addColorStop(1, 'rgba(255,120,20,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, R * 0.5 * pulse, 0, 7); ctx.fill();
    // Hexagon im Zentrum
    ctx.strokeStyle = 'rgba(255,190,90,.9)'; ctx.lineWidth = 1.6;
    ctx.shadowColor = 'rgba(255,150,40,.9)'; ctx.shadowBlur = 8;
    hex(cx, cy, R * 0.2 * pulse, ts / 3000); ctx.stroke();
    hex(cx, cy, R * 0.13 * pulse, -ts / 2000); ctx.stroke();
    ctx.shadowBlur = 0;
    // Segment-Ringe
    for (let ring = 0; ring < 3; ring++) {
      const rr = R * (0.5 + ring * 0.16);
      const rot = ts / (800 + ring * 600) * (ring % 2 ? -1 : 1);
      ctx.strokeStyle = 'rgba(255,140,26,' + (0.8 - ring * 0.22) + ')';
      ctx.lineWidth = 2.2 - ring * 0.6;
      for (let seg = 0; seg < 4; seg++) {
        const s = rot + seg * Math.PI / 2;
        ctx.beginPath(); ctx.arc(cx, cy, rr, s, s + Math.PI / 3.2); ctx.stroke();
      }
    }
    // Ticks
    ctx.strokeStyle = 'rgba(255,140,26,.45)'; ctx.lineWidth = 1;
    for (let i = 0; i < 40; i++) {
      const ang = i * Math.PI / 20 + ts / 7000;
      const r1 = R * 0.99, r2 = R * (i % 4 ? 1.03 : 1.08);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1);
      ctx.lineTo(cx + Math.cos(ang) * r2, cy + Math.sin(ang) * r2);
      ctx.stroke();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

logLine('JARVIS // COMMAND CENTER hochgefahren', 'ok');
</script>
</body>
</html>
"""


BRAIN_PAGE = """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<title>JARVIS // NEURO-ANSICHT</title>
<style>
  body { margin: 0; background: #050302; overflow: hidden; }
  canvas { display: block; width: 100vw; height: 100vh; }
  #tag { position: fixed; top: 12px; left: 14px; color: #ff8c1a;
         font: 11px "Cascadia Mono", Consolas, monospace; letter-spacing: .2em;
         text-shadow: 0 0 10px rgba(255,140,26,.6); }
</style>
</head>
<body>
<div id="tag">JARVIS // NEURALES NETZ - LIVE</div>
<canvas id="c"></canvas>
<script>
// Vollbild-Neuronenkugel wie auf dem Laptop im Vorbild-Video
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const N = 320, pts = [];
for (let i = 0; i < N; i++) {
  const r = Math.cbrt(Math.random());  // auch Punkte im Inneren
  const t = Math.acos(2 * Math.random() - 1), p = Math.random() * Math.PI * 2;
  pts.push([r * Math.sin(t) * Math.cos(p), r * Math.sin(t) * Math.sin(p), r * Math.cos(t)]);
}
function draw(ts) {
  const w = cv.width = innerWidth, h = cv.height = innerHeight;
  ctx.fillStyle = 'rgba(5,3,2,0.35)';
  ctx.fillRect(0, 0, w, h);
  const R = Math.min(w, h) * 0.4, cx = w / 2, cy = h / 2;
  const a = ts / 6000, b = ts / 11000;
  const proj = pts.map(([x, y, z]) => {
    let x2 = x * Math.cos(a) - z * Math.sin(a);
    let z2 = x * Math.sin(a) + z * Math.cos(a);
    let y2 = y * Math.cos(b) - z2 * Math.sin(b);
    z2 = y * Math.sin(b) + z2 * Math.cos(b);
    return [cx + x2 * R, cy + y2 * R, z2];
  });
  ctx.lineWidth = 0.6;
  for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
    const dx = proj[i][0] - proj[j][0], dy = proj[i][1] - proj[j][1];
    const d2 = dx * dx + dy * dy;
    if (d2 < R * R * 0.06) {
      const puls = 0.5 + 0.5 * Math.sin(ts / 500 + i);
      ctx.strokeStyle = 'rgba(255,110,20,' + ((0.3 - d2 / (R * R * 0.22)) * puls) + ')';
      ctx.beginPath(); ctx.moveTo(proj[i][0], proj[i][1]); ctx.lineTo(proj[j][0], proj[j][1]); ctx.stroke();
    }
  }
  for (const [x, y, z] of proj) {
    ctx.fillStyle = z > 0 ? '#ffb054' : 'rgba(255,130,26,.5)';
    ctx.beginPath(); ctx.arc(x, y, z > 0 ? 2.1 : 1.2, 0, 7); ctx.fill();
  }
  requestAnimationFrame(draw);
}
requestAnimationFrame(draw);
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="JARVIS // COMMAND CENTER im Browser")
    parser.add_argument("--demo", action="store_true",
                        help="simulierte Antworten ohne API-Schlüssel/Ollama")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if ensure_secrets_file():
        print(
            "\nHinweis: config/secrets.json wurde angelegt - dort gehören "
            "deine API-Schlüssel hinein (oder: python einrichten.py)."
        )
    app = create_app(demo=args.demo)
    print(f"\n  JARVIS // COMMAND CENTER: http://localhost:{args.port}"
          f"\n  NEURO-ANSICHT (Vollbild):  http://localhost:{args.port}/brain"
          f"{'   (Demo-Modus)' if args.demo else ''}\n")
    app.run(host="127.0.0.1", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
