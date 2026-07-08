"""Jarvis im Browser testen: kleiner lokaler Webserver mit Streaming.

Start auf dem eigenen Rechner:
    python jarvis_web.py            # echtes Gehirn (Claude bzw. Ollama)
    python jarvis_web.py --demo     # ohne API-Schlüssel: simulierte Antworten

Dann im Browser http://localhost:8000 öffnen. Die Seite nutzt:
  * Mikrofon über die Web Speech API des Browsers (Chrome/Edge, Deutsch)
  * Sprachausgabe über speechSynthesis - satzweise, sobald ein Satz fertig ist
  * dieselbe Streaming-Pipeline wie der Sprachmodus in der Konsole,
    inklusive ⏱-Latenz-Anzeige pro Runde
"""

import argparse
import json
import time

from flask import Flask, Response, request

from jarvis.core.claude_client import ClaudeClient
from jarvis.core.conversation import ConversationManager
from jarvis.core.errors import LLMError
from jarvis.core.ollama_client import OllamaClient
from jarvis.memory.long_term import LongTermMemory
from jarvis.utils.config_loader import PROJECT_ROOT, load_config
from jarvis.utils.latency import TurnTimer


class DemoClient:
    """Simuliertes Gehirn für den Test ohne API-Schlüssel (--demo).

    Streamt eine Antwort Wort für Wort mit kleiner Verzögerung, damit man
    im Browser sieht und hört, wie satzweises Sprechen sich anfühlt.
    """

    def chat_stream(self, prompt=None, messages=None):
        answer = (
            "Das ist eine Demo-Antwort ohne echtes Modell. "
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

    app = Flask("jarvis_web")

    @app.get("/")
    def index() -> Response:
        return Response(PAGE, mimetype="text/html")

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
<title>Jarvis – Browser-Test</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: system-ui, "Segoe UI", sans-serif;
    background: #0b1020; color: #e8ecf5;
    display: flex; flex-direction: column; height: 100vh;
  }
  header {
    padding: 14px 20px; border-bottom: 1px solid #1e2a45;
    display: flex; align-items: center; gap: 12px;
  }
  header h1 { font-size: 17px; margin: 0; font-weight: 600; letter-spacing: .04em; }
  header .dot { width: 9px; height: 9px; border-radius: 50%; background: #39d98a; }
  header .spacer { flex: 1; }
  header label { font-size: 13px; color: #9fb0d0; display: flex; gap: 6px; align-items: center; }
  #chat { flex: 1; overflow-y: auto; padding: 18px; display: flex; flex-direction: column; gap: 10px; }
  .bubble { max-width: 72%; padding: 10px 14px; border-radius: 14px; line-height: 1.45; white-space: pre-wrap; }
  .user   { align-self: flex-end; background: #2b62d9; border-bottom-right-radius: 4px; }
  .jarvis { align-self: flex-start; background: #17203a; border: 1px solid #223052; border-bottom-left-radius: 4px; }
  .timing { align-self: flex-start; font-size: 12px; color: #7f92b8; padding: 0 6px; }
  .error  { align-self: flex-start; background: #3a1720; border: 1px solid #5a2333; }
  form { display: flex; gap: 8px; padding: 14px 18px; border-top: 1px solid #1e2a45; }
  input[type=text] {
    flex: 1; padding: 11px 14px; border-radius: 10px; border: 1px solid #223052;
    background: #101830; color: inherit; font-size: 15px; outline: none;
  }
  input[type=text]:focus { border-color: #2b62d9; }
  button {
    padding: 11px 16px; border-radius: 10px; border: none; cursor: pointer;
    background: #2b62d9; color: white; font-size: 15px;
  }
  button.mic { background: #17203a; border: 1px solid #223052; }
  button.mic.rec { background: #b3263c; border-color: #b3263c; }
  button:disabled { opacity: .5; cursor: default; }
</style>
</head>
<body>
<header>
  <div class="dot"></div>
  <h1>J.A.R.V.I.S. – Browser-Test</h1>
  <div class="spacer"></div>
  <label><input type="checkbox" id="voice" checked> 🔊 Stimme</label>
</header>
<div id="chat"></div>
<form id="form">
  <button type="button" class="mic" id="mic" title="Im Browser sprechen (Chrome/Edge)">🎤</button>
  <input type="text" id="text" placeholder="Schreib Jarvis etwas … (oder 🎤 drücken und sprechen)" autocomplete="off" autofocus>
  <button type="submit" id="send">Senden</button>
</form>
<script>
const chat = document.getElementById('chat');
const form = document.getElementById('form');
const input = document.getElementById('text');
const sendBtn = document.getElementById('send');
const micBtn = document.getElementById('mic');
const voiceOn = document.getElementById('voice');

function bubble(cls, text) {
  const el = document.createElement('div');
  el.className = 'bubble ' + cls;
  el.textContent = text;
  chat.appendChild(el);
  chat.scrollTop = chat.scrollHeight;
  return el;
}

function speak(sentence) {
  if (!voiceOn.checked || !window.speechSynthesis) return;
  const u = new SpeechSynthesisUtterance(sentence);
  u.lang = 'de-DE';
  speechSynthesis.speak(u);  // reiht sich automatisch satzweise ein
}

async function send(text) {
  if (!text.trim()) return;
  input.value = '';
  sendBtn.disabled = true;
  bubble('user', text);
  const answer = bubble('jarvis', '');
  const t0 = performance.now();
  let firstSentenceMs = null;
  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = '';
    for (;;) {
      const {done, value} = await reader.read();
      if (done) break;
      buf += decoder.decode(value, {stream: true});
      let i;
      while ((i = buf.indexOf('\\n')) >= 0) {
        const line = buf.slice(0, i).trim();
        buf = buf.slice(i + 1);
        if (!line) continue;
        const msg = JSON.parse(line);
        if (msg.type === 'sentence') {
          if (firstSentenceMs === null) firstSentenceMs = performance.now() - t0;
          answer.textContent += (answer.textContent ? ' ' : '') + msg.text;
          chat.scrollTop = chat.scrollHeight;
          speak(msg.text);
        } else if (msg.type === 'timing') {
          const browser = firstSentenceMs === null ? '' :
            ' · im Browser: erster Satz ' + (firstSentenceMs / 1000).toFixed(1) + 's';
          bubble('timing', '⏱ ' + msg.report + browser).classList.remove('bubble');
        } else if (msg.type === 'error') {
          answer.classList.add('error');
          answer.textContent = '⚠ ' + msg.text;
        }
      }
    }
  } catch (e) {
    answer.classList.add('error');
    answer.textContent = '⚠ Verbindung zum Server verloren: ' + e;
  }
  sendBtn.disabled = false;
  input.focus();
}

form.addEventListener('submit', (e) => { e.preventDefault(); send(input.value); });

// Mikrofon über die Web Speech API des Browsers (Chrome/Edge)
const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
if (!Rec) {
  micBtn.disabled = true;
  micBtn.title = 'Dieser Browser kann keine Spracherkennung (nimm Chrome oder Edge).';
} else {
  const rec = new Rec();
  rec.lang = 'de-DE';
  rec.interimResults = false;
  let recording = false;
  rec.onresult = (e) => {
    const text = e.results[0][0].transcript;
    send(text);
  };
  rec.onend = () => { recording = false; micBtn.classList.remove('rec'); micBtn.textContent = '🎤'; };
  rec.onerror = rec.onend;
  micBtn.addEventListener('click', () => {
    if (recording) { rec.stop(); return; }
    recording = true;
    micBtn.classList.add('rec');
    micBtn.textContent = '⏹';
    rec.start();
  });
}
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvis im Browser testen")
    parser.add_argument("--demo", action="store_true",
                        help="simulierte Antworten ohne API-Schlüssel/Ollama")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    app = create_app(demo=args.demo)
    print(f"\n  Jarvis läuft: http://localhost:{args.port}"
          f"{'  (Demo-Modus)' if args.demo else ''}\n")
    app.run(host="127.0.0.1", port=args.port, threaded=True)


if __name__ == "__main__":
    main()
