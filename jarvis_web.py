"""JARVIS // COMMAND CENTER - Jarvis im Browser, im Kommandozentralen-Look.

Start auf dem eigenen Rechner:
    python jarvis_web.py            # echtes Gehirn (Claude bzw. Ollama)
    python jarvis_web.py --demo     # ohne API-Schlüssel: simulierte Antworten

Dann im Browser http://localhost:8000 öffnen. Die Zentrale zeigt:
  * links die Neuronen-Kugel und den Live-Systemstatus (Gehirn, Ohren,
    Stimme, Plugins, Skills, Abteilungen - echte Daten, kein Deko-Text)
  * in der Mitte das Gespräch - gestreamt Satz für Satz, gesprochen über
    die Browser-Stimme, Mikrofon über die Web Speech API (Chrome/Edge)
  * rechts den Arc-Reactor, die ⏱-Latenz der letzten Runde und die
    Abteilungen des virtuellen Konzerns
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
            "commands": len(plugins.command_map),
            "skills": sorted(skills.skills),
            "departments": sorted(agents.agents),
            "memory_facts": len(memory.facts) if hasattr(memory, "facts") else 0,
        }

    app = Flask("jarvis_web")

    @app.get("/")
    def index() -> Response:
        return Response(PAGE, mimetype="text/html")

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
    --amber: #ff8c1a; --amber-dim: #b35900; --amber-glow: rgba(255,140,26,.55);
    --bg: #0a0705; --panel: #120c07; --line: #2a1a0a;
    --green: #3fbf5f; --red: #e04545; --text: #ffd9a8;
    color-scheme: dark;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; height: 100vh; display: flex; flex-direction: column;
    background: radial-gradient(1200px 600px at 70% -10%, #1c0f04 0%, var(--bg) 60%);
    color: var(--text);
    font-family: "Cascadia Mono", "Consolas", "Courier New", monospace;
    font-size: 13px;
  }
  header {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 16px; border-bottom: 1px solid var(--line);
    text-shadow: 0 0 8px var(--amber-glow);
  }
  header .logo { color: var(--amber); font-size: 15px; letter-spacing: .12em; font-weight: bold; }
  header .tick { color: var(--amber-dim); font-size: 11px; letter-spacing: .08em; }
  header .spacer { flex: 1; }
  header .clock { color: var(--amber); font-size: 14px; }
  header label { color: var(--amber-dim); font-size: 11px; display: flex; gap: 5px; align-items: center; }

  #grid {
    flex: 1; display: grid; min-height: 0;
    grid-template-columns: 250px 1fr 250px; gap: 10px; padding: 10px 12px;
  }
  @media (max-width: 900px) { #grid { grid-template-columns: 1fr; } .side { display: none; } }
  .side { display: flex; flex-direction: column; gap: 10px; min-height: 0; }
  .panel {
    background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
    padding: 8px 10px; overflow: hidden;
  }
  .panel h2 {
    margin: 0 0 6px; font-size: 10px; letter-spacing: .18em;
    color: var(--amber); border-bottom: 1px solid var(--line); padding-bottom: 5px;
    text-shadow: 0 0 6px var(--amber-glow);
  }
  .kv { display: flex; justify-content: space-between; gap: 8px; padding: 2px 0; font-size: 11px; }
  .kv .k { color: var(--amber-dim); }
  .kv .v { color: var(--text); text-align: right; }
  .kv .ok { color: var(--green); }
  canvas.viz { width: 100%; display: block; }
  #deptlist { font-size: 10.5px; line-height: 1.7; color: var(--amber-dim); overflow-y: auto; flex: 1; }
  #deptlist b { color: var(--text); font-weight: normal; }

  #center { display: flex; flex-direction: column; min-height: 0; gap: 10px; }
  #chat {
    flex: 1; overflow-y: auto; padding: 12px;
    background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
  }
  .row { margin: 7px 0; line-height: 1.55; white-space: pre-wrap; }
  .row .tag { font-size: 10px; letter-spacing: .12em; margin-right: 8px; }
  .row.user  { color: #ffe9c9; } .row.user .tag { color: var(--green); }
  .row.jarvis { color: var(--text); } .row.jarvis .tag { color: var(--amber); text-shadow: 0 0 6px var(--amber-glow); }
  .row.timing { color: var(--amber-dim); font-size: 10.5px; }
  .row.error { color: var(--red); }
  #form { display: flex; gap: 8px; }
  #text {
    flex: 1; background: var(--panel); border: 1px solid var(--line); border-radius: 4px;
    color: var(--text); font: inherit; padding: 10px 12px; outline: none;
  }
  #text:focus { border-color: var(--amber-dim); box-shadow: 0 0 10px rgba(255,140,26,.15); }
  button {
    background: #1c1208; color: var(--amber); border: 1px solid var(--amber-dim);
    border-radius: 4px; font: inherit; padding: 10px 14px; cursor: pointer;
    letter-spacing: .1em; text-shadow: 0 0 6px var(--amber-glow);
  }
  button:hover { background: #2a1a0a; }
  button.rec { color: #fff; background: var(--red); border-color: var(--red); text-shadow: none; }
  button:disabled { opacity: .45; cursor: default; }
</style>
</head>
<body>
<header>
  <span class="logo">JARVIS // COMMAND CENTER</span>
  <span class="tick" id="ticker">SYSTEME WERDEN GELADEN ...</span>
  <span class="spacer"></span>
  <label><input type="checkbox" id="voice" checked> STIMME</label>
  <span class="clock" id="clock">--:--:--</span>
</header>
<div id="grid">
  <div class="side">
    <div class="panel"><h2>NEURALES NETZ</h2><canvas class="viz" id="brainviz" height="190"></canvas></div>
    <div class="panel" id="sysstatus" style="flex:1">
      <h2>SYSTEME</h2>
      <div class="kv"><span class="k">GEHIRN</span><span class="v" id="s-brain">...</span></div>
      <div class="kv"><span class="k">OHREN</span><span class="v" id="s-ears">...</span></div>
      <div class="kv"><span class="k">STIMME</span><span class="v" id="s-voice">...</span></div>
      <div class="kv"><span class="k">PLUGINS</span><span class="v ok" id="s-plugins">...</span></div>
      <div class="kv"><span class="k">BEFEHLE</span><span class="v ok" id="s-commands">...</span></div>
      <div class="kv"><span class="k">SKILLS</span><span class="v ok" id="s-skills">...</span></div>
      <div class="kv"><span class="k">ABTEILUNGEN</span><span class="v ok" id="s-depts">...</span></div>
      <div class="kv"><span class="k">STATUS</span><span class="v ok">● ONLINE</span></div>
    </div>
  </div>

  <div id="center">
    <div id="chat"></div>
    <form id="form">
      <button type="button" id="mic" title="Sprechen (Chrome/Edge)">MIC</button>
      <input type="text" id="text" placeholder="> Befehl oder Frage an JARVIS ..." autocomplete="off" autofocus>
      <button type="submit" id="send">SENDEN</button>
    </form>
  </div>

  <div class="side">
    <div class="panel"><h2>REAKTORKERN</h2><canvas class="viz" id="reactor" height="190"></canvas></div>
    <div class="panel">
      <h2>LATENZ // LETZTE RUNDE</h2>
      <div class="kv"><span class="k">ERSTER SATZ</span><span class="v" id="m-first">-</span></div>
      <div class="kv"><span class="k">ANTWORT KOMPLETT</span><span class="v" id="m-full">-</span></div>
      <div class="kv"><span class="k">SERVER</span><span class="v" id="m-server" style="font-size:10px">-</span></div>
    </div>
    <div class="panel" style="flex:1; display:flex; flex-direction:column">
      <h2>KONZERN // ABTEILUNGEN</h2>
      <div id="deptlist">wird geladen ...</div>
    </div>
  </div>
</div>
<script>
const $ = id => document.getElementById(id);

// ---- Uhr + Ticker -------------------------------------------------------
setInterval(() => {
  $('clock').textContent = new Date().toLocaleTimeString('de-CH');
}, 500);
const TICKS = ["ALLE SYSTEME NOMINAL", "STREAMING AKTIV", "SATZWEISE AUSGABE BEREIT",
               "MIKROFON BEREIT", "KONZERN IM STANDBY", "LATENZ-MONITOR AKTIV"];
let tick = 0;
setInterval(() => { $('ticker').textContent = TICKS[tick++ % TICKS.length]; }, 4000);

// ---- Systemstatus (echte Daten vom Server) ------------------------------
fetch('/api/status').then(r => r.json()).then(s => {
  $('s-brain').textContent = s.brain;
  $('s-ears').textContent = s.ears;
  $('s-voice').textContent = s.voice;
  $('s-plugins').textContent = s.plugins.length + ' AKTIV';
  $('s-commands').textContent = s.commands;
  $('s-skills').textContent = s.skills.length;
  $('s-depts').textContent = s.departments.length;
  $('deptlist').innerHTML = s.departments
    .map(d => '▸ <b>' + d.replace('ultra-', '').toUpperCase() + '</b>').join('<br>');
  $('ticker').textContent = 'ALLE SYSTEME NOMINAL';
});

// ---- Chat mit Streaming ---------------------------------------------------
function row(cls, tag, text) {
  const el = document.createElement('div');
  el.className = 'row ' + cls;
  const t = document.createElement('span');
  t.className = 'tag'; t.textContent = tag;
  const body = document.createElement('span');
  body.textContent = text;
  el.append(t, body);
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
            $('m-first').textContent = (firstMs / 1000).toFixed(1) + 's';
          }
          body.textContent += (body.textContent ? ' ' : '') + msg.text;
          $('chat').scrollTop = $('chat').scrollHeight;
          speak(msg.text);
        } else if (msg.type === 'timing') {
          $('m-full').textContent = ((performance.now() - t0) / 1000).toFixed(1) + 's';
          $('m-server').textContent = msg.report;
          row('timing', '//', '⏱ ' + msg.report);
        } else if (msg.type === 'error') {
          body.parentElement.classList.add('error');
          body.textContent = '⚠ ' + msg.text;
        }
      }
    }
  } catch (e) {
    body.parentElement.classList.add('error');
    body.textContent = '⚠ Verbindung verloren: ' + e;
  }
  $('send').disabled = false;
  $('text').focus();
}
$('form').addEventListener('submit', e => { e.preventDefault(); send($('text').value); });

// ---- Mikrofon (Web Speech API) -------------------------------------------
const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!Rec) {
  $('mic').disabled = true;
  $('mic').title = 'Dieser Browser kann keine Spracherkennung (nimm Chrome oder Edge).';
} else {
  const rec = new Rec();
  rec.lang = 'de-DE'; rec.interimResults = false;
  let on = false;
  rec.onresult = e => send(e.results[0][0].transcript);
  rec.onend = rec.onerror = () => { on = false; $('mic').classList.remove('rec'); $('mic').textContent = 'MIC'; };
  $('mic').addEventListener('click', () => {
    if (on) { rec.stop(); return; }
    on = true; $('mic').classList.add('rec'); $('mic').textContent = 'STOP';
    rec.start();
  });
}

// ---- Neuronen-Kugel (linkes Panel) ----------------------------------------
(function () {
  const cv = $('brainviz'), ctx = cv.getContext('2d');
  const N = 90, pts = [];
  for (let i = 0; i < N; i++) {
    const t = Math.acos(2 * Math.random() - 1), p = Math.random() * Math.PI * 2;
    pts.push([Math.sin(t) * Math.cos(p), Math.sin(t) * Math.sin(p), Math.cos(t)]);
  }
  function draw(ts) {
    const w = cv.width = cv.clientWidth, h = cv.height;
    ctx.clearRect(0, 0, w, h);
    const a = ts / 4000, R = Math.min(w, h) * 0.42, cx = w / 2, cy = h / 2;
    const proj = pts.map(([x, y, z]) => {
      const x2 = x * Math.cos(a) - z * Math.sin(a);
      const z2 = x * Math.sin(a) + z * Math.cos(a);
      return [cx + x2 * R, cy + y * R, z2];
    });
    ctx.lineWidth = 0.5;
    for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) {
      const dx = proj[i][0] - proj[j][0], dy = proj[i][1] - proj[j][1];
      const d2 = dx * dx + dy * dy;
      if (d2 < R * R * 0.22) {
        ctx.strokeStyle = 'rgba(255,120,20,' + (0.35 - d2 / (R * R)) + ')';
        ctx.beginPath(); ctx.moveTo(proj[i][0], proj[i][1]); ctx.lineTo(proj[j][0], proj[j][1]); ctx.stroke();
      }
    }
    for (const [x, y, z] of proj) {
      ctx.fillStyle = z > 0 ? '#ffab40' : 'rgba(255,140,26,.4)';
      ctx.beginPath(); ctx.arc(x, y, z > 0 ? 1.8 : 1.1, 0, 7); ctx.fill();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();

// ---- Arc-Reactor (rechtes Panel) -------------------------------------------
(function () {
  const cv = $('reactor'), ctx = cv.getContext('2d');
  function draw(ts) {
    const w = cv.width = cv.clientWidth, h = cv.height;
    const cx = w / 2, cy = h / 2, R = Math.min(w, h) * 0.44;
    ctx.clearRect(0, 0, w, h);
    const speaking = window.speechSynthesis && speechSynthesis.speaking;
    const pulse = 0.85 + 0.15 * Math.sin(ts / (speaking ? 90 : 700));
    // glühender Kern
    const g = ctx.createRadialGradient(cx, cy, 2, cx, cy, R * 0.5 * pulse);
    g.addColorStop(0, 'rgba(255,190,90,.95)');
    g.addColorStop(0.4, 'rgba(255,120,20,.55)');
    g.addColorStop(1, 'rgba(255,120,20,0)');
    ctx.fillStyle = g;
    ctx.beginPath(); ctx.arc(cx, cy, R * 0.5 * pulse, 0, 7); ctx.fill();
    // rotierende Ringe
    for (let ring = 0; ring < 3; ring++) {
      const rr = R * (0.55 + ring * 0.16);
      const rot = ts / (900 + ring * 700) * (ring % 2 ? -1 : 1);
      ctx.strokeStyle = 'rgba(255,140,26,' + (0.75 - ring * 0.2) + ')';
      ctx.lineWidth = 2 - ring * 0.5;
      for (let seg = 0; seg < 4; seg++) {
        const start = rot + seg * Math.PI / 2;
        ctx.beginPath(); ctx.arc(cx, cy, rr, start, start + Math.PI / 3); ctx.stroke();
      }
    }
    // Ticks außen
    ctx.strokeStyle = 'rgba(255,140,26,.5)'; ctx.lineWidth = 1;
    for (let i = 0; i < 36; i++) {
      const ang = i * Math.PI / 18 + ts / 6000;
      const r1 = R * 1.02, r2 = R * (i % 3 ? 1.06 : 1.12);
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(ang) * r1, cy + Math.sin(ang) * r1);
      ctx.lineTo(cx + Math.cos(ang) * r2, cy + Math.sin(ang) * r2);
      ctx.stroke();
    }
    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
})();
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
          f"{'  (Demo-Modus)' if args.demo else ''}\n")
    app.run(host="127.0.0.1", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
