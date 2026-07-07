/* J.A.R.V.I.S. HUD — dashboard logic.
 *
 * Talks to the backend over one WebSocket (chat + live events + approvals)
 * and the REST API (managers). Voice works in every modern Chromium-based
 * browser via the Web Speech API: push-to-talk on the mic button, plus an
 * optional always-on wake-word mode ("Jarvis …").
 */

"use strict";

const $ = (sel) => document.querySelector(sel);
const state = {
  ws: null,
  session: "default",
  listening: false,
  wakeMode: false,
  speaking: false,
  coreLevel: 0, // 0 idle, 1 listening, 2 thinking/speaking
};

/* ---------------------------------------------------------- websocket */
function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws`);
  state.ws = ws;
  ws.onopen = () => setStatus("ONLINE", true);
  ws.onclose = () => {
    setStatus("OFFLINE", false);
    setTimeout(connect, 2000);
  };
  ws.onmessage = (e) => handleEvent(JSON.parse(e.data));
}

function handleEvent(ev) {
  if (ev.type !== "event") return;
  logEvent(ev);
  switch (ev.topic) {
    case "chat.user":
      addMessage("user", ev.data.text);
      setCore(2, "verarbeite…");
      break;
    case "chat.assistant":
      addMessage("jarvis", ev.data.text, ev.data.agent);
      setCore(0, "bereit");
      break;
    case "voice.speak":
      speak(ev.data);
      break;
    case "approval.requested":
      showApproval(ev.data);
      break;
    case "approval.resolved":
    case "approval.timeout":
      hideApproval();
      break;
    case "reminder.due":
      addMessage("jarvis", `⏰ ${ev.data.message}`, "scheduler");
      break;
    case "agent.task.started":
    case "agent.task.completed":
      refreshAgents();
      break;
    case "system.online":
      refreshAll();
      break;
  }
}

/* --------------------------------------------------------------- chat */
function addMessage(who, text, agent) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  if (agent && who === "jarvis") {
    const tag = document.createElement("span");
    tag.className = "agent";
    tag.textContent = agent.toUpperCase();
    div.appendChild(tag);
  }
  div.appendChild(document.createTextNode(text));
  $("#chat").appendChild(div);
  $("#chat").scrollTop = $("#chat").scrollHeight;
}

function sendText(text) {
  text = (text || $("#text").value).trim();
  if (!text || !state.ws || state.ws.readyState !== 1) return;
  state.ws.send(JSON.stringify({ type: "chat", text, session: state.session }));
  $("#text").value = "";
}

$("#send").onclick = () => sendText();
$("#text").addEventListener("keydown", (e) => e.key === "Enter" && sendText());

/* -------------------------------------------------------------- voice */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null;

function startRecognition(continuous) {
  if (!SR) {
    addMessage("jarvis", "Spracherkennung wird von diesem Browser nicht unterstützt (Chrome/Edge nutzen).", "voice");
    return;
  }
  stopRecognition();
  recognizer = new SR();
  recognizer.lang = document.documentElement.lang === "de" ? "de-DE" : "en-US";
  recognizer.continuous = continuous;
  recognizer.interimResults = false;
  recognizer.onstart = () => {
    state.listening = true;
    $("#mic").classList.add("listening");
    setCore(1, "höre zu…");
  };
  recognizer.onend = () => {
    state.listening = false;
    $("#mic").classList.remove("listening");
    if (state.coreLevel === 1) setCore(0, "bereit");
    if (state.wakeMode) setTimeout(() => startRecognition(true), 300);
  };
  recognizer.onresult = (e) => {
    const text = e.results[e.results.length - 1][0].transcript.trim();
    if (!text) return;
    if (state.wakeMode) {
      const wake = ($("#set-wake").textContent || "jarvis").toLowerCase();
      const lower = text.toLowerCase();
      const idx = lower.indexOf(wake);
      if (idx === -1) return; // ignore speech without the wake word
      const command = text.slice(idx + wake.length).replace(/^[,.!?\s]+/, "");
      if (command) sendText(command);
      else setCore(1, "ja?");
    } else {
      sendText(text);
    }
  };
  try { recognizer.start(); } catch (_) { /* already started */ }
}

function stopRecognition() {
  if (recognizer) {
    recognizer.onend = null;
    try { recognizer.stop(); } catch (_) {}
    recognizer = null;
  }
  state.listening = false;
  $("#mic").classList.remove("listening");
}

$("#mic").onclick = () => (state.listening ? stopRecognition() : startRecognition(false));

$("#set-wakeword").onchange = (e) => {
  state.wakeMode = e.target.checked;
  if (state.wakeMode) startRecognition(true);
  else stopRecognition();
};

function speak(data) {
  if (data.wav_b64) {
    // Server-side Piper audio
    new Audio(`data:audio/wav;base64,${data.wav_b64}`).play().catch(() => {});
    return;
  }
  if (!$("#set-tts").checked || !window.speechSynthesis) return;
  const utter = new SpeechSynthesisUtterance(data.text);
  utter.lang = "de-DE";
  utter.onstart = () => setCore(2, "spreche…");
  utter.onend = () => setCore(0, "bereit");
  speechSynthesis.cancel();
  speechSynthesis.speak(utter);
}

/* ---------------------------------------------------------- approvals */
let approvalId = null;
const RISKS = ["LESEN", "SCHREIBEN", "SYSTEMZUGRIFF", "KRITISCH"];

function showApproval(req) {
  approvalId = req.id;
  $("#approval-text").textContent =
    `${req.requested_by} möchte ausführen: ${req.action}\n${req.detail}\nRisiko: ${RISKS[req.risk] || req.risk}`;
  $("#approval-remember").checked = false;
  $("#approval-backdrop").classList.remove("hidden");
}
function hideApproval() {
  approvalId = null;
  $("#approval-backdrop").classList.add("hidden");
}
function decide(approved) {
  if (!approvalId) return;
  state.ws.send(JSON.stringify({
    type: "approval", id: approvalId, approved,
    remember: $("#approval-remember").checked,
  }));
  hideApproval();
}
$("#approve-yes").onclick = () => decide(true);
$("#approve-no").onclick = () => decide(false);

/* --------------------------------------------------------------- core */
function setCore(level, label) {
  state.coreLevel = level;
  $("#core-state").textContent = label || "bereit";
}

function setStatus(text, ok) {
  const el = $("#sys-status");
  el.textContent = text;
  el.style.color = ok ? "var(--ok)" : "var(--danger)";
}

(function animateCore() {
  const canvas = $("#core");
  const ctx = canvas.getContext("2d");
  const cx = canvas.width / 2, cy = canvas.height / 2;
  let t = 0;
  function frame() {
    t += 0.016;
    const speed = [0.4, 1.2, 2.2][state.coreLevel] || 0.4;
    const glow = [0.45, 0.8, 1.0][state.coreLevel] || 0.45;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // inner core
    const grad = ctx.createRadialGradient(cx, cy, 6, cx, cy, 84);
    grad.addColorStop(0, `rgba(190,235,255,${glow})`);
    grad.addColorStop(0.5, `rgba(64,180,255,${glow * 0.55})`);
    grad.addColorStop(1, "rgba(64,180,255,0)");
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(cx, cy, 84 + Math.sin(t * 2 * speed) * 5, 0, Math.PI * 2);
    ctx.fill();

    // rotating rings with gaps
    for (let ring = 0; ring < 3; ring++) {
      const radius = 116 + ring * 34;
      const segments = 5 + ring * 2;
      const rot = t * speed * (ring % 2 ? -0.35 : 0.5) + ring;
      ctx.strokeStyle = `rgba(64,180,255,${0.55 - ring * 0.13})`;
      ctx.lineWidth = 2.5 - ring * 0.6;
      for (let s = 0; s < segments; s++) {
        const start = rot + (s / segments) * Math.PI * 2;
        ctx.beginPath();
        ctx.arc(cx, cy, radius, start, start + (Math.PI * 2 / segments) * 0.62);
        ctx.stroke();
      }
    }

    // ticks
    ctx.strokeStyle = "rgba(159,216,255,0.5)";
    ctx.lineWidth = 1;
    for (let i = 0; i < 60; i++) {
      const a = (i / 60) * Math.PI * 2 + t * speed * 0.15;
      const r1 = 98, r2 = i % 5 === 0 ? 108 : 103;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(a) * r1, cy + Math.sin(a) * r1);
      ctx.lineTo(cx + Math.cos(a) * r2, cy + Math.sin(a) * r2);
      ctx.stroke();
    }
    requestAnimationFrame(frame);
  }
  frame();
})();

setInterval(() => {
  $("#sys-clock").textContent = new Date().toLocaleTimeString("de-DE");
}, 1000);

/* ------------------------------------------------------------ managers */
async function api(path, options) {
  const resp = await fetch(`/api${path}`, options);
  if (!resp.ok) throw new Error(`${resp.status} ${await resp.text()}`);
  return resp.json();
}

async function refreshStatus() {
  const s = await api("/status");
  $("#sys-llm").textContent = s.llm;
  $("#sys-agents").textContent = s.agents.length;
  $("#sys-skills").textContent = s.skills;
  $("#sys-voice").textContent = s.voice.stt_local ? "lokal" : "browser";
  $("#set-wake").textContent = s.voice.wake_word || "jarvis";
  renderSchedule(s.schedule);
}

async function refreshAgents() {
  const agents = await api("/agents");
  $("#sys-agents").textContent = agents.length;
  $("#agent-list").innerHTML = "";
  for (const a of agents) {
    const div = document.createElement("div");
    div.className = `item ${a.busy ? "busy" : ""} ${a.running ? "" : "off"}`;
    div.innerHTML = `<span class="title"></span><div class="sub"></div>`;
    div.querySelector(".title").textContent = a.title;
    div.querySelector(".sub").textContent =
      `${a.department} · ${a.busy ? "arbeitet" : "bereit"} · ${a.queued} in Queue · @${a.name}`;
    div.onclick = () => { $("#text").value = `@${a.name} `; $("#text").focus(); };
    $("#agent-list").appendChild(div);
  }
}

async function refreshSkills() {
  const skills = await api("/skills");
  $("#skill-list").innerHTML = "";
  for (const s of skills) {
    const div = document.createElement("div");
    div.className = `item ${s.enabled ? "" : "off"}`;
    div.innerHTML = `<span class="title"></span><div class="sub"></div>`;
    div.querySelector(".title").textContent = s.name;
    div.querySelector(".sub").textContent = `${s.category} · Risiko ${RISKS[s.risk]} · ${s.description}`;
    div.onclick = async () => {
      await api(`/skills/${s.name}/enabled?enabled=${!s.enabled}`, { method: "POST" });
      refreshSkills();
    };
    $("#skill-list").appendChild(div);
  }
}

async function refreshPlugins() {
  const plugins = await api("/plugins");
  const box = $("#plugin-list");
  box.innerHTML = plugins.length ? "" : '<div class="sub">Keine Plugins im plugins/-Ordner.</div>';
  for (const p of plugins) {
    const div = document.createElement("div");
    div.className = `item ${p.enabled ? "" : "off"}`;
    div.innerHTML = `<span class="title"></span><div class="sub"></div>
      <button class="mini toggle"></button> <button class="mini reload">RELOAD</button>`;
    div.querySelector(".title").textContent = `${p.name} v${p.version}`;
    div.querySelector(".sub").textContent = p.error ? `FEHLER: ${p.error}` : p.description;
    const toggle = div.querySelector(".toggle");
    toggle.textContent = p.enabled ? "DEAKTIVIEREN" : "AKTIVIEREN";
    toggle.onclick = async () => {
      await api(`/plugins/${p.id}/enabled?enabled=${!p.enabled}`, { method: "POST" });
      refreshPlugins();
    };
    div.querySelector(".reload").onclick = async () => {
      await api(`/plugins/${p.id}/reload`, { method: "POST" });
      refreshPlugins();
    };
    box.appendChild(div);
  }
}

async function refreshWorkflows() {
  const flows = await api("/workflows");
  const box = $("#workflow-list");
  box.innerHTML = flows.length ? "" : '<div class="sub">Noch keine Workflows.</div>';
  for (const w of flows) {
    const div = document.createElement("div");
    div.className = "item";
    div.innerHTML = `<span class="title"></span><div class="sub"></div>
      <button class="mini run">▶ START</button>`;
    div.querySelector(".title").textContent = w.name;
    div.querySelector(".sub").textContent = `${w.steps.length} Schritte · ${w.description}`;
    div.querySelector(".run").onclick = () =>
      api(`/workflows/${w.name}/run`, { method: "POST" }).catch((e) => addMessage("jarvis", String(e), "workflow"));
    box.appendChild(div);
  }
}

async function saveWorkflow() {
  try {
    const wf = JSON.parse($("#wf-editor").value);
    await api("/workflows", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(wf),
    });
    refreshWorkflows();
  } catch (e) {
    alert(`Ungültiger Workflow: ${e.message}`);
  }
}

async function refreshMemory(query) {
  const items = query
    ? await api(`/memory/search?query=${encodeURIComponent(query)}`)
    : await api("/memory");
  const box = $("#memory-list");
  box.innerHTML = "";
  for (const m of items) {
    const div = document.createElement("div");
    div.className = "item";
    div.textContent = m.text || `${m.subject}: ${m.content}`;
    box.appendChild(div);
  }
}
$("#mem-query").addEventListener("keydown", (e) => {
  if (e.key === "Enter") refreshMemory(e.target.value);
});

function renderSchedule(jobs) {
  const box = $("#schedule-list");
  box.innerHTML = jobs.length ? "" : '<div class="sub">Nichts geplant.</div>';
  for (const j of jobs) {
    const div = document.createElement("div");
    div.className = "item";
    const when = new Date(j.when * 1000).toLocaleString("de-DE");
    div.innerHTML = `<span class="title"></span><div class="sub"></div>`;
    div.querySelector(".title").textContent = j.message;
    div.querySelector(".sub").textContent = `${j.kind} · ${when}`;
    box.appendChild(div);
  }
}

function logEvent(ev) {
  const box = $("#log-list");
  const div = document.createElement("div");
  div.textContent = `${new Date(ev.timestamp * 1000).toLocaleTimeString("de-DE")} [${ev.topic}] ${ev.source}`;
  box.prepend(div);
  while (box.childElementCount > 200) box.lastChild.remove();
}

async function hirePrompt() {
  const name = prompt("Interner Name (z. B. 'legal'):");
  if (!name) return;
  const title = prompt("Titel:", `${name[0].toUpperCase()}${name.slice(1)} Agent`) || name;
  const department = prompt("Abteilung:", "operations") || "general";
  const description = prompt("Aufgabenbeschreibung:") || "";
  await api("/agents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, title, department, description }),
  }).catch((e) => alert(e.message));
  refreshAgents();
}

/* ----------------------------------------------------------------- tabs */
document.querySelectorAll("#tabs button").forEach((btn) => {
  btn.onclick = () => {
    document.querySelectorAll("#tabs button").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".tab").forEach((t) => t.classList.add("hidden"));
    btn.classList.add("active");
    $(`#tab-${btn.dataset.tab}`).classList.remove("hidden");
    ({ skills: refreshSkills, plugins: refreshPlugins, workflows: refreshWorkflows,
       memory: () => refreshMemory("") }[btn.dataset.tab] || (() => {}))();
  };
});

/* ----------------------------------------------------------------- boot */
function refreshAll() {
  refreshStatus().catch(() => {});
  refreshAgents().catch(() => {});
  refreshSkills().catch(() => {});
}
connect();
refreshAll();
setInterval(() => refreshStatus().catch(() => {}), 15000);
