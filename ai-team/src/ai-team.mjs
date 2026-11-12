#!/usr/bin/env node
// ai-team — Unified AI Team orchestrator (Claude Code + OpenCode + Grok + GPT/Codex)
// Zero dependency. Node >=18. Honesty-first: an agent "result" is ONLY ever real CLI
// stdout from a real invocation. A seat that is missing/unauthenticated is reported as
// its true state and NEVER given a fabricated answer.

import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, appendFileSync, writeFileSync, readFileSync, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';
import { dirname, join, resolve } from 'node:path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');            // ai-team/
const CONFIG_PATH = join(ROOT, 'config', 'agents.json');
const STATE = join(ROOT, 'state');
const TASKS = join(STATE, 'tasks');
const BUS = join(STATE, 'messages.jsonl');

// ---- capability states (honest ladder) -----------------------------------
const STATE_RANK = {
  NOT_INSTALLED: 0,  // binary not on PATH
  INSTALLED: 1,      // binary runs, auth unknown/missing
  AUTHENTICATED: 2,  // auth material present
  EXECUTION_READY: 3,// probed and runnable
  BLOCKED: -1,       // present but cannot be used under current policy (e.g. paid-only)
};

const C = { // tiny ansi
  g: s => `\x1b[32m${s}\x1b[0m`, r: s => `\x1b[31m${s}\x1b[0m`,
  y: s => `\x1b[33m${s}\x1b[0m`, b: s => `\x1b[1m${s}\x1b[0m`, d: s => `\x1b[2m${s}\x1b[0m`,
};

function loadConfig() {
  if (!existsSync(CONFIG_PATH)) die(`config not found: ${CONFIG_PATH}`);
  return JSON.parse(readFileSync(CONFIG_PATH, 'utf8'));
}
function ensureState() { mkdirSync(TASKS, { recursive: true }); }
function nowISO() { return new Date().toISOString(); }
function tid() { return 't' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6); }
function expandHome(p) { return p && p.startsWith('~') ? join(homedir(), p.slice(1)) : p; }
function die(msg) { console.error(C.r('ai-team: ' + msg)); process.exit(1); }

// ---- probing: real, no fabrication ---------------------------------------
function which(cmd) {
  const r = spawnSync(process.platform === 'win32' ? 'where' : 'command',
    process.platform === 'win32' ? [cmd] : ['-v', cmd],
    { shell: process.platform !== 'win32', encoding: 'utf8' });
  return r.status === 0 && (r.stdout || '').trim() ? (r.stdout || '').trim().split('\n')[0] : null;
}

function probeAgent(id, cfg) {
  const a = cfg.agents[id];
  const out = { id, role: a.role, billing: a.billing, state: 'NOT_INSTALLED', path: null, reason: '', version: '' };
  const path = which(a.probe.cmd);
  if (!path) { out.reason = `CLI '${a.probe.cmd}' not found on PATH`; return out; }
  out.path = path; out.state = 'INSTALLED';
  // run version/probe (bounded)
  const pr = spawnSync(a.probe.cmd, a.probe.args || ['--version'], { encoding: 'utf8', timeout: 8000 });
  if (pr.status === 0) out.version = (pr.stdout || pr.stderr || '').trim().split('\n')[0];
  // auth signals
  let authed = false;
  if (id === 'claude') {
    authed = existsSync(join(homedir(), '.claude', '.credentials.json')) || !!process.env.ANTHROPIC_BASE_URL;
  }
  if (a.probe.authFile && existsSync(expandHome(a.probe.authFile))) authed = true;
  if (a.probe.authEnv && process.env[a.probe.authEnv]) authed = true;
  // opencode / codex / grok: also treat a config dir as a weak auth signal
  if (!authed) {
    const cfgHints = {
      opencode: ['~/.config/opencode', '~/.local/share/opencode'],
      codex: ['~/.codex', '~/.config/codex'],
      grok: ['~/.grok', '~/.config/grok'],
    }[id] || [];
    if (cfgHints.some(p => existsSync(expandHome(p)))) authed = true;
  }
  out.state = authed ? 'EXECUTION_READY' : 'INSTALLED';
  if (!authed) out.reason = `installed but no login/auth material found — run its own 'login' once (free subscription)`;
  // policy: zero unapproved paid API. We never inject a paid key ourselves.
  // A seat reachable ONLY via a paid key that the user has not placed in its own CLI login
  // stays INSTALLED (not BLOCKED) — the CLI's own login is the free path we rely on.
  return out;
}

function probeAll(cfg) {
  return Object.keys(cfg.agents).filter(id => cfg.agents[id].enabled !== false).map(id => probeAgent(id, cfg));
}

// ---- bus (persistent group chat) -----------------------------------------
function busWrite(msg) {
  ensureState();
  const rec = {
    id: 'm' + Date.now().toString(36) + Math.random().toString(36).slice(2, 5),
    ts: nowISO(),
    agent: msg.agent, role: msg.role || '',
    task: msg.task || '', analysis: msg.analysis || '',
    result: msg.result || '', evidence: msg.evidence || '',
    nextAction: msg.nextAction || '', status: msg.status || 'info',
  };
  appendFileSync(BUS, JSON.stringify(rec) + '\n');
  return rec;
}
function busRead(n = 50) {
  if (!existsSync(BUS)) return [];
  const lines = readFileSync(BUS, 'utf8').trim().split('\n').filter(Boolean);
  return lines.slice(-n).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
}

// ---- task decomposition (heuristic, transparent) -------------------------
function decompose(request, cfg) {
  // Deterministic, explainable plan. No hidden model call here — the planning
  // itself is cheap/local; the real model work happens per-subtask via adapters.
  const steps = [
    { phase: 'research',     desc: `Analyse & Recherche zum Auftrag: ${request}` },
    { phase: 'architecture', desc: `Technischer Loesungsvorschlag / Architektur` },
    { phase: 'implement',    desc: `Umsetzung der beschlossenen Aenderung` },
    { phase: 'test',         desc: `Unabhaengige Tests / Verifikation` },
    { phase: 'review',       desc: `Abschliessendes Code-Review & Qualitaetsurteil` },
  ];
  return steps.map((s, i) => {
    const candidates = cfg.routing[s.phase] || ['claude'];
    return { n: i + 1, phase: s.phase, desc: s.desc, candidates,
             branch: ['implement', 'test'].includes(s.phase) ? null : undefined };
  });
}

function pickAgent(candidates, probes) {
  const ready = candidates.find(id => (probes[id]?.state === 'EXECUTION_READY'));
  if (ready) return { id: ready, state: 'EXECUTION_READY' };
  const installed = candidates.find(id => probes[id]?.state === 'INSTALLED');
  if (installed) return { id: installed, state: 'INSTALLED' };
  return { id: candidates[0], state: probes[candidates[0]]?.state || 'NOT_INSTALLED' };
}

// ---- real invocation (the ONLY source of an agent result) ----------------
function invokeAgent(id, cfg, prompt, { timeoutMs = 180000 } = {}) {
  const a = cfg.agents[id];
  const args = (a.invoke.args || []).map(x => x === '{PROMPT}' ? prompt : x);
  const started = Date.now();
  const r = spawnSync(a.invoke.cmd, args, { encoding: 'utf8', timeout: timeoutMs, maxBuffer: 1024 * 1024 * 16 });
  const ms = Date.now() - started;
  if (r.error) return { ok: false, status: 'FAILED', reason: String(r.error.message || r.error), ms };
  const stdout = (r.stdout || '').trim();
  if (r.status !== 0) return { ok: false, status: 'FAILED', reason: `exit ${r.status}: ${(r.stderr || '').trim().slice(0, 500)}`, ms };
  if (!stdout) return { ok: false, status: 'EMPTY', reason: 'CLI returned no output', ms };
  return { ok: true, status: 'OK', output: stdout, ms };
}

// ---- orchestration -------------------------------------------------------
function runTask(request, cfg, { live = true } = {}) {
  ensureState();
  const probes = Object.fromEntries(probeAll(cfg).map(p => [p.id, p]));
  const id = tid();
  const plan = decompose(request, cfg);
  console.log(C.b(`\n▶ ai-team task ${id}`));
  console.log(C.d(`  "${request}"\n`));

  busWrite({ agent: 'USER', task: request, status: 'task_open', nextAction: 'decompose & route' });

  const results = [];
  for (const step of plan) {
    const pick = pickAgent(step.candidates, probes);
    const agent = cfg.agents[pick.id];
    const header = `  [${step.n}/${plan.length}] ${step.phase.toUpperCase()} → ${pick.id} (${agent.role})`;
    if (pick.state === 'EXECUTION_READY' && live) {
      process.stdout.write(header + C.d(' …running… '));
      const prompt =
`Du bist ${agent.role} in einem KI-Team. Teilaufgabe (${step.phase}): ${step.desc}
Gesamtauftrag des Nutzers: "${request}"
Antworte knapp und konkret auf Deutsch. Liefere: Analyse, Ergebnis, Belege, naechste Aktion.`;
      const inv = invokeAgent(pick.id, cfg, prompt);
      if (inv.ok) {
        console.log(C.g(`OK ${inv.ms}ms`));
        const rec = busWrite({ agent: pick.id, role: agent.role, task: step.desc,
          result: inv.output.slice(0, 4000), evidence: `real CLI call (${agent.invoke.cmd}), exit 0, ${inv.ms}ms`,
          status: 'done', nextAction: step.n < plan.length ? plan[step.n].phase : 'deliver' });
        results.push({ step: step.n, phase: step.phase, agent: pick.id, status: 'DONE', ms: inv.ms, msgId: rec.id, output: inv.output });
      } else {
        console.log(C.r(inv.status));
        busWrite({ agent: pick.id, role: agent.role, task: step.desc,
          result: '', evidence: `real CLI call failed: ${inv.reason}`, status: inv.status.toLowerCase(),
          nextAction: 'needs attention' });
        results.push({ step: step.n, phase: step.phase, agent: pick.id, status: inv.status, reason: inv.reason });
      }
    } else {
      const label = pick.state === 'NOT_INSTALLED' ? 'BLOCKED (CLI not installed)'
                  : pick.state === 'INSTALLED' ? 'MANUAL ONLY (installed, not authenticated)'
                  : `BLOCKED (${pick.state})`;
      console.log(header + '  ' + C.y('→ ' + label));
      busWrite({ agent: pick.id, role: agent.role, task: step.desc, result: '',
        evidence: `${pick.id} state=${pick.state}: ${probes[pick.id]?.reason || 'unavailable'}`,
        status: 'blocked', nextAction: 'run this seat on a machine where it is logged in (free subscription)' });
      results.push({ step: step.n, phase: step.phase, agent: pick.id, status: label, reason: probes[pick.id]?.reason || '' });
    }
  }

  const task = { id, ts: nowISO(), request, plan, probes, results,
    status: results.every(r => r.status === 'DONE') ? 'complete'
          : results.some(r => r.status === 'DONE') ? 'partial' : 'blocked' };
  writeFileSync(join(TASKS, id + '.json'), JSON.stringify(task, null, 2));
  busWrite({ agent: 'ai-team', task: request, status: task.status,
    result: `${results.filter(r => r.status === 'DONE').length}/${results.length} Schritte live ausgefuehrt`,
    evidence: `task file state/tasks/${id}.json`, nextAction: task.status === 'complete' ? 'review output' : 'unblock missing seats' });

  console.log('');
  console.log(C.b('  Ergebnis: ') + (task.status === 'complete' ? C.g(task.status)
    : task.status === 'partial' ? C.y(task.status) : C.r(task.status)) +
    C.d(`  (${results.filter(r => r.status === 'DONE').length}/${results.length} Schritte live)`));
  console.log(C.d(`  gespeichert: ai-team/state/tasks/${id}.json`));
  return task;
}

// ---- views ---------------------------------------------------------------
function cmdAgents(cfg) {
  const probes = probeAll(cfg);
  console.log(C.b('\nAI TEAM — Seat-Status (echte Probe)\n'));
  for (const p of probes) {
    const badge = p.state === 'EXECUTION_READY' ? C.g('● EXECUTION READY')
      : p.state === 'AUTHENTICATED' ? C.g('● AUTHENTICATED')
      : p.state === 'INSTALLED' ? C.y('● INSTALLED (not authed)')
      : p.state === 'BLOCKED' ? C.r('● BLOCKED')
      : C.r('● NOT INSTALLED');
    console.log(`  ${p.id.padEnd(9)} ${badge}  ${C.d(p.role)}`);
    if (p.version) console.log(C.d(`            ${p.version}`));
    if (p.reason) console.log(C.d(`            ${p.reason}`));
  }
  console.log('');
}

function cmdStatus(cfg) {
  ensureState();
  const files = existsSync(TASKS) ? readdirSync(TASKS).filter(f => f.endsWith('.json')) : [];
  console.log(C.b(`\nAI TEAM — Status`));
  console.log(C.d(`  Tasks gespeichert: ${files.length}`));
  const recent = files.map(f => JSON.parse(readFileSync(join(TASKS, f), 'utf8')))
    .sort((a, b) => b.ts.localeCompare(a.ts)).slice(0, 8);
  for (const t of recent) {
    const s = t.status === 'complete' ? C.g(t.status) : t.status === 'partial' ? C.y(t.status) : C.r(t.status);
    console.log(`  ${t.id}  ${s.padEnd(18)} ${C.d(t.request.slice(0, 60))}`);
  }
  console.log('');
}

function cmdBus(n) {
  const msgs = busRead(n || 30);
  console.log(C.b(`\nAI TEAM — Gruppenchat (letzte ${msgs.length})\n`));
  for (const m of msgs) {
    const who = m.agent === 'USER' ? C.b('USER') : m.agent === 'ai-team' ? C.d('ai-team') : C.b(m.agent);
    console.log(`${C.d(m.ts)}  ${who}${m.role ? C.d(' · ' + m.role) : ''}`);
    if (m.task) console.log(`  task: ${m.task}`);
    if (m.result) console.log(`  → ${m.result.slice(0, 300).replace(/\n/g, '\n    ')}`);
    if (m.evidence) console.log(C.d(`  beleg: ${m.evidence}`));
    if (m.nextAction) console.log(C.d(`  next: ${m.nextAction}`));
    console.log('');
  }
}

function cmdStart(cfg) {
  console.log(C.b('\n==================================================='));
  console.log(C.b('  UNIFIED AI TEAM — Claude · Codex · Grok · OpenCode'));
  console.log(C.b('==================================================='));
  cmdAgents(cfg);
  const probes = probeAll(cfg);
  const ready = probes.filter(p => p.state === 'EXECUTION_READY').map(p => p.id);
  const blocked = probes.filter(p => p.state !== 'EXECUTION_READY');
  console.log(C.b('  Policy: ') + 'FREE FIRST · keine unautorisierten API-Kosten · keine Simulation');
  console.log(C.b('  Live-Seats: ') + (ready.length ? C.g(ready.join(', ')) : C.r('keine')));
  if (blocked.length) {
    console.log(C.y('  Nicht einsatzbereit:'));
    for (const b of blocked) console.log(C.d(`    - ${b.id}: ${b.state}${b.reason ? ' — ' + b.reason : ''}`));
  }
  console.log('\n  Befehle:');
  console.log(C.d('    ai-team agents          # Seat-Status (echte Probe)'));
  console.log(C.d('    ai-team task "..."      # Aufgabe verteilen & live ausfuehren'));
  console.log(C.d('    ai-team status          # gespeicherte Tasks'));
  console.log(C.d('    ai-team bus [n]         # Gruppenchat-Verlauf'));
  console.log('');
}

function help() {
  console.log(`ai-team — Unified AI Team orchestrator
Usage:
  ai-team start                 System hochfahren, Seats proben, Uebersicht
  ai-team agents                Seat-Status (NOT_INSTALLED/INSTALLED/EXECUTION_READY)
  ai-team task "<auftrag>"      Aufgabe zerlegen, an reale Seats routen, ausfuehren
  ai-team council "<aufgabe>"   Round-Table: dieselbe Aufgabe an ALLE Seats, Diskussion [--rounds=2]
  ai-team status                Gespeicherte Tasks anzeigen
  ai-team bus [n]               Persistenten Gruppenchat anzeigen (default 30)
  ai-team probe <id>            Einen Seat einzeln proben
  ai-team help                  Diese Hilfe

Grundsatz: Ein Agenten-"Ergebnis" ist IMMER echte CLI-Ausgabe eines realen Aufrufs.
Ein fehlender/nicht angemeldeter Seat wird ehrlich als solcher gemeldet — nie simuliert.`);
}

// ---- council / round-table (no fixed roles; all seats equal) -------------
function councilProposePrompt(request) {
  return `TEAM-AUFGABE (Round-Table, KEINE festen Rollen): "${request}"
Du bist ein gleichberechtigtes Mitglied eines KI-Teams (Claude, OpenCode, Codex, Grok).
Antworte als DU SELBST. Erste Zeile GENAU: "MODELL: <dein echter Modellname>".
Dann kompakt auf Deutsch: Analyse · Loesungsvorschlag · Belege/Annahmen · offene Fragen ans Team.
Bestaetige am Ende, dass du diese Team-Nachricht erhalten hast.`;
}
function councilReviewPrompt(request, transcript) {
  return `TEAM-AUFGABE: "${request}"
Vorschlaege der anderen Teammitglieder (lies sie und reagiere darauf):
---
${transcript}
---
Erste Zeile GENAU: "MODELL: <dein echter Modellname>".
Dann: Wo stimmst du zu? Wo widersprichst du (mit Begruendung)? Welche Fehler siehst du?
Wie verbesserst du die GEMEINSAME Loesung? Kompakt, Deutsch.`;
}

function runCouncil(request, cfg, { rounds = 1, maxSeatCalls = 8 } = {}) {
  ensureState();
  const probes = Object.fromEntries(probeAll(cfg).map(p => [p.id, p]));
  const ready = Object.keys(probes).filter(id => probes[id].state === 'EXECUTION_READY');
  const blocked = Object.keys(probes).filter(id => probes[id].state !== 'EXECUTION_READY');
  const id = tid();
  console.log(C.b(`\n==  ai-team council ${id}`));
  console.log(C.d(`  "${request}"`));
  console.log(C.b('  Teilnehmer (EXECUTION READY): ') + (ready.length ? C.g(ready.join(', ')) : C.r('keine')));
  if (blocked.length) console.log(C.y('  BLOCKED/MANUAL: ') + blocked.map(b => `${b}(${probes[b].state})`).join(', '));

  const planned = ready.length * rounds;
  console.log(C.d(`  geplante echte Aufrufe: ${planned} (Seats ${ready.length} x Runden ${rounds})`));
  if (planned > maxSeatCalls) die(`Kostenschutz: ${planned} Aufrufe > Limit ${maxSeatCalls}. Senke --rounds oder Seat-Zahl.`);
  if (ready.length === 0) {
    busWrite({ agent: 'ai-team', task: request, status: 'blocked', result: 'kein Seat EXECUTION READY',
      evidence: 'probeAll', nextAction: 'Seats lokal anmelden (opencode/codex/grok login)' });
    console.log(C.r('  Kein einsatzbereiter Seat — Council nicht moeglich. Melde die Seats lokal an.'));
    return;
  }

  busWrite({ agent: 'USER', task: request, status: 'council_open', nextAction: `broadcast an ${ready.join(',')}` });
  const transcript = [];
  for (let round = 1; round <= rounds; round++) {
    console.log(C.b(`\n  -- Runde ${round} ${round === 1 ? '(Vorschlaege)' : '(Kreuz-Review)'} --`));
    for (const seat of ready) {
      const a = cfg.agents[seat];
      if (a.costNote) console.log(C.y(`    ! ${seat}: ${a.costNote}`));
      const prompt = round === 1 ? councilProposePrompt(request)
        : councilReviewPrompt(request,
            transcript.filter(t => t.round === round - 1).map(t => `[${t.seat}]\n${t.text}`).join('\n\n'));
      process.stdout.write(`    ${seat} …`);
      const inv = invokeAgent(seat, cfg, prompt);
      if (inv.ok) {
        console.log(C.g(`OK ${inv.ms}ms`));
        transcript.push({ round, seat, text: inv.output });
        busWrite({ agent: seat, role: 'Teammitglied (gleichberechtigt)', task: `council r${round}`,
          result: inv.output.slice(0, 4000), evidence: `real CLI (${a.invoke.cmd}) exit 0 ${inv.ms}ms`,
          status: 'done', nextAction: round < rounds ? 'review' : 'converge' });
      } else {
        console.log(C.r(inv.status));
        transcript.push({ round, seat, text: `(keine Antwort: ${inv.status} — ${inv.reason})` });
        busWrite({ agent: seat, role: 'Teammitglied', task: `council r${round}`, result: '',
          evidence: `real CLI failed: ${inv.reason}`, status: inv.status.toLowerCase(), nextAction: 'Seat pruefen' });
      }
    }
  }
  const answered = transcript.filter(t => !t.text.startsWith('(keine Antwort')).length;
  const task = { id, ts: nowISO(), mode: 'council', request, participants: ready, blocked, rounds, probes, transcript,
    status: answered === 0 ? 'blocked' : ready.length >= 2 ? 'diskussion-mehrere-seats' : 'einzel-seat' };
  writeFileSync(join(TASKS, id + '.json'), JSON.stringify(task, null, 2));
  console.log('');
  console.log(C.b('  Council gespeichert: ') + `ai-team/state/tasks/${id}.json`);
  console.log(C.d('  Verlauf ansehen: ai-team bus'));
  if (ready.length < 2)
    console.log(C.y(`  Hinweis: nur ${ready.length} Seat live — echte Team-Diskussion entsteht erst mit >=2 angemeldeten Seats (lokal auf deinem PC).`));
  return task;
}

// ---- main ----------------------------------------------------------------
function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const cfg = loadConfig();
  switch (cmd) {
    case 'start': return cmdStart(cfg);
    case 'agents': return cmdAgents(cfg);
    case 'status': return cmdStatus(cfg);
    case 'bus': return cmdBus(parseInt(rest[0] || '30', 10));
    case 'probe': {
      const id = rest[0];
      if (!id || !cfg.agents[id]) die(`unknown agent '${id}'. known: ${Object.keys(cfg.agents).join(', ')}`);
      console.log(JSON.stringify(probeAgent(id, cfg), null, 2));
      return;
    }
    case 'task': {
      const request = rest.join(' ').trim();
      if (!request) die('task needs text: ai-team task "<auftrag>"');
      return void runTask(request, cfg);
    }
    case 'council': {
      const request = rest.filter(x => !x.startsWith('--')).join(' ').trim();
      const roundsArg = rest.find(x => x.startsWith('--rounds='));
      const rounds = roundsArg ? Math.max(1, Math.min(3, parseInt(roundsArg.split('=')[1], 10) || 1)) : 1;
      if (!request) die('council needs text: ai-team council "<aufgabe>" [--rounds=2]');
      return void runCouncil(request, cfg, { rounds });
    }
    case undefined:
    case 'help':
    case '--help':
    case '-h': return help();
    default: die(`unknown command '${cmd}'. try: ai-team help`);
  }
}
main();
