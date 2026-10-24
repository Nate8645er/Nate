// Ghost Protocol: Neon Maze — engine, story, AI, UI.
// Solo story adventure: 6 chapters, 4 hunter AIs, 6 bosses, 3 endings.
// Fixed-timestep simulation, seeded RNG, all strings external (strings.js).

import { LANGS, makeT } from "./strings.js";
import { CHAPTERS, QUEST_TARGET } from "./levels.js";
import {
  TILE, makeHero, makeHunter, makeDrone, makeMine, makeNpc, makeBoss, makeSegment,
  makeItems, makeTileset, makeBackdrop, makeScanlines
} from "./sprites.js";
import { GameAudio } from "./audio.js";

// ---------- utils ----------
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const clamp = (v, a, b) => v < a ? a : v > b ? b : v;
const dist2 = (ax, ay, bx, by) => (ax - bx) * (ax - bx) + (ay - by) * (ay - by);
const lerp = (a, b, t) => a + (b - a) * t;

// ---------- balance (all tuning lives here as data) ----------
const BAL = {
  playerSpeed: 118,          // px/s
  playerHp: 100, playerEnergy: 100,
  energyRegen: 11,           // per s
  hitboxScale: 0.6,          // player hitbox smaller than sprite (honest near-misses)
  invulnAfterHit: 1.2,       // s
  pulse: { cost: 6, dmg: 10, speed: 320, cd: 0.25, life: 1.4 },
  dash: { cost: 14, dur: 0.17, mult: 3.3, cd: 0.85 },
  emp: { cost: 30, radius: 3.4, stun: 2.6, cd: 6 },
  cloak: { cost: 32, dur: 3.2, cd: 8 },
  slow: { cost: 26, factor: 0.45, dur: 4.0, cd: 9 },
  teleport: { cost: 24, range: 3, cd: 4 },
  shield: { cost: 28, dur: 2.4, cd: 9 },
  magnetRadius: 2.6,
  hunterSpeed: { blaze: 92, phantom: 74, widow: 66, glitch: 80 },
  hunterVision: 6.5, hunterHearing: 2.6,
  hunterTouchDmg: 25, droneTouchDmg: 10, droneHp: 20,
  laserDmg: 16, mineDmg: 22, boltDmg: 12,
  alertPerFrag: 0.16, alertDecay: 0.008,
  xp: { frag: 25, drone: 10, stun: 4, boss: 150, secret: 20 },
  bossHp: { guardian: 340, hacker: 380, queen: 440, leviathan: 500, omega: 540, architect: 680 },
  checkpointInvuln: 1.2
};
const XP_NEXT = (lvl) => Math.round(100 * Math.pow(lvl, 1.35));

const SKILLS = {
  ghost: ["g1", "g2", "g3", "g4"],
  surge: ["s1", "s2", "s3", "s4"],
  chrono: ["c1", "c2", "c3", "c4"]
};
const ABILITY_ORDER = ["dash", "hack", "emp", "shield", "cloak", "magnet", "slow", "teleport"];
const ABILITY_KEYS = { dash: "SHIFT", hack: "E", emp: "Q", shield: "R", cloak: "C", magnet: "G", slow: "F", teleport: "T" };

const ACH_IDS = ["first_frag", "first_hack", "boss1", "boss6", "all_frags_ch", "secret3",
  "no_dmg_boss", "all_abilities", "quests", "end_any", "end_true", "speed1"];

const DEFAULT_BINDS = {
  up: ["KeyW", "ArrowUp"], down: ["KeyS", "ArrowDown"],
  left: ["KeyA", "ArrowLeft"], right: ["KeyD", "ArrowRight"],
  pulse: ["Space"], dash: ["ShiftLeft", "ShiftRight"], interact: ["KeyE"],
  emp: ["KeyQ"], cloak: ["KeyC"], slow: ["KeyF"], teleport: ["KeyT"],
  shield: ["KeyR"], magnet: ["KeyG"], pause: ["Escape"],
  skills: ["KeyK"], quests: ["KeyJ"], inventory: ["KeyI"]
};
const PAD_MAP = { 0: "pulse", 1: "dash", 2: "interact", 3: "emp", 4: "cloak", 5: "shield", 6: "teleport", 7: "slow", 8: "skills", 9: "pause", 12: "up", 13: "down", 14: "left", 15: "right" };

const TOTAL_FRAGS = CHAPTERS.reduce((s, ch) => s + ch.maps.reduce((m, map) =>
  m + map.grid.join("").split("F").length - 1, 0), 0);

// ---------- input ----------
class Input {
  constructor(binds) {
    this.binds = binds;
    this.held = new Set();          // actions currently held
    this.pressed = new Set();       // actions pressed since last consume
    this.codesPressed = new Set();  // raw codes (menus, rebind)
    this.captureCode = null;        // rebind capture callback
    this.touch = { stick: null, vec: [0, 0], buttons: new Set(), taps: [] };
    this.padHeldPrev = new Set();
    this.mouse = { x: 0, y: 0, clicked: false };
    addEventListener("keydown", (e) => {
      if (e.repeat) return;
      if (this.captureCode) { this.captureCode(e.code); e.preventDefault(); return; }
      this.codesPressed.add(e.code);
      const a = this.actionFor(e.code);
      if (a) { this.held.add(a); this.pressed.add(a); }
      if (["Space", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Tab"].includes(e.code)) e.preventDefault();
    });
    addEventListener("keyup", (e) => {
      const a = this.actionFor(e.code);
      if (a) this.held.delete(a);
    });
    addEventListener("mousemove", (e) => { this.mouse.x = e.clientX; this.mouse.y = e.clientY; });
    addEventListener("mousedown", () => { this.mouse.clicked = true; });
  }
  actionFor(code) {
    for (const a in this.binds) if (this.binds[a].includes(code)) return a;
    return null;
  }
  pollPad() {
    const pads = navigator.getGamepads ? navigator.getGamepads() : [];
    const now = new Set();
    for (const gp of pads) {
      if (!gp) continue;
      gp.buttons.forEach((b, i) => {
        const a = PAD_MAP[i];
        if (a && (b.pressed || b.value > 0.5)) now.add(a);
      });
      const ax = gp.axes[0] || 0, ay = gp.axes[1] || 0;
      if (Math.abs(ax) > 0.3 || Math.abs(ay) > 0.3) this.padVec = [ax, ay];
      else this.padVec = null;
    }
    for (const a of now) { if (!this.padHeldPrev.has(a)) this.pressed.add(a); this.held.add(a); }
    for (const a of this.padHeldPrev) if (!now.has(a)) this.held.delete(a);
    this.padHeldPrev = now;
  }
  moveVec() {
    let dx = 0, dy = 0;
    if (this.held.has("left")) dx -= 1;
    if (this.held.has("right")) dx += 1;
    if (this.held.has("up")) dy -= 1;
    if (this.held.has("down")) dy += 1;
    if (this.padVec) { dx += this.padVec[0]; dy += this.padVec[1]; }
    if (this.touch.vec[0] || this.touch.vec[1]) { dx += this.touch.vec[0]; dy += this.touch.vec[1]; }
    const m = Math.hypot(dx, dy);
    if (m > 1) { dx /= m; dy /= m; }
    return [dx, dy];
  }
  consume() { this.pressed.clear(); this.codesPressed.clear(); this.mouse.clicked = false; }
}

// ---------- game ----------
export class Game {
  constructor(canvas, devEl) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.devEl = devEl;
    this.dev = new URLSearchParams(location.search).has("dev");
    this.settings = this.loadJSON("gpnm_settings", {
      lang: (navigator.language || "de").startsWith("de") ? "de" : "en",
      music: 0.8, sfx: 0.8, crt: true, shake: true, flash: true, textScale: 1,
      binds: null
    });
    if (!this.settings.binds) this.settings.binds = JSON.parse(JSON.stringify(DEFAULT_BINDS));
    this.ach = this.loadJSON("gpnm_ach", {});
    this.t = makeT(this.settings.lang);
    this.input = new Input(this.settings.binds);
    this.audio = new GameAudio();
    this.audio.setVolumes(this.settings.music, this.settings.sfx);

    // sprites
    this.sprHero = makeHero();
    this.sprHunters = { blaze: makeHunter("blaze"), phantom: makeHunter("phantom"), widow: makeHunter("widow"), glitch: makeHunter("glitch") };
    this.sprDrone = makeDrone();
    this.sprMine = makeMine();
    this.sprNpc = makeNpc(0);
    this.sprSegment = makeSegment();
    this.sprBosses = {};
    for (const b of ["guardian", "hacker", "queen", "leviathan", "omega", "architect"]) this.sprBosses[b] = makeBoss(b);
    this.items = makeItems("#00e5ff");
    this.backdrops = {};
    this.scan = makeScanlines(64, 4);
    this.optImages = {}; // optional generated images (assets/img_*.jpg) — used when present
    this.tryLoadImages();

    this.screen = "menu";
    this.menuIdx = 0;
    this.toasts = [];
    this.shakeT = 0; this.shakeMag = 0;
    this.run = null;
    this.level = null;
    this.frame = 0;
    this.fps = 0;
    this.setupTouch();
    this.menuBackdrop = this.getBackdrop(1);
    this.confirmDelete = -1;
  }

  // optional AI-generated cinematics: loaded only when listed in assets/manifest.json
  async tryLoadImages() {
    try {
      const res = await fetch("./assets/manifest.json");
      if (!res.ok) return;
      const man = await res.json();
      this.assetManifest = man;
      this.audio.sfxUrls = man.sfx || {};
      for (const [n, url] of Object.entries(man.images || {})) {
        const img = new Image();
        img.crossOrigin = "anonymous";
        img.onload = () => { this.optImages[n] = img; };
        img.src = url;
      }
    } catch { /* manifest optional */ }
  }
  getBackdrop(chapter, mode = "chapter") {
    const key = mode === "chapter" ? "ch" + chapter : mode;
    if (mode === "delete" && this.optImages.end_delete) return this.optImages.end_delete;
    if (mode === "merge" && this.optImages.end_merge) return this.optImages.end_merge;
    if (mode === "save" && this.optImages.end_save) return this.optImages.end_save;
    if (mode === "chapter" && this.optImages[key]) return this.optImages[key];
    if (!this.backdrops[key]) {
      const ch = CHAPTERS[clamp(chapter - 1, 0, 5)];
      this.backdrops[key] = makeBackdrop(chapter, ch.accent, ch.tint, mulberry32(chapter * 77 + (mode === "chapter" ? 0 : mode.length)), mode);
    }
    return this.backdrops[key];
  }

  loadJSON(k, d) {
    try {
      const v = localStorage.getItem(k);
      if (!v) return d === null ? null : JSON.parse(JSON.stringify(d));
      const parsed = JSON.parse(v);
      return d === null ? parsed : Object.assign(JSON.parse(JSON.stringify(d)), parsed);
    } catch { return d === null ? null : JSON.parse(JSON.stringify(d)); }
  }
  saveJSON(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage full/blocked */ } }

  toast(text, color = "#e0f7ff") { this.toasts.push({ text, color, t: 3.6 }); if (this.toasts.length > 4) this.toasts.shift(); }
  unlock(id) {
    if (this.ach[id]) return;
    this.ach[id] = true;
    this.saveJSON("gpnm_ach", this.ach);
    this.toast(`${this.t("ach.unlocked")}: ${this.t("ach." + id + ".name")}`, "#ffc400");
    this.audio.playSfx("achieve");
  }
  shake(mag, dur) { if (!this.settings.shake) return; this.shakeMag = mag; this.shakeT = dur; }

  // ---------- run / save ----------
  newRun() {
    this.run = {
      chapter: 1, mapIdx: 0,
      hp: BAL.playerHp, energy: BAL.playerEnergy,
      xp: 0, level: 1, sp: 0, skills: {},
      abilities: { pulse: true },
      keys: 0, cells: 0, lore: [],
      fragTotal: 0, fragByCh: {}, fragChAll: {},
      quests: {}, storyFlags: { coinBuff: 0, secrets: 0, abilityUsed: {}, adapt: null },
      abilityUse: { dash: 0, emp: 0, cloak: 0, slow: 0 },
      playtime: 0, ch1Time: 0,
      checkpoint: null
    };
  }
  serializeRun() { return JSON.parse(JSON.stringify(this.run)); }
  saveSlot(slot) {
    const data = { run: this.serializeRun(), ts: this.run.playtime, saved: true };
    this.saveJSON(slot === "auto" ? "gpnm_auto" : "gpnm_slot" + slot, data);
  }
  loadSlot(slot) {
    const data = this.loadJSON(slot === "auto" ? "gpnm_auto" : "gpnm_slot" + slot, null);
    if (!data || !data.run) return false;
    this.run = data.run;
    this.startChapterMusic();
    this.loadLevel(this.run.mapIdx, true);
    this.screen = "play";
    return true;
  }
  slotInfo(slot) {
    const data = this.loadJSON(slot === "auto" ? "gpnm_auto" : "gpnm_slot" + slot, null);
    if (!data || !data.run) return null;
    return { chapter: data.run.chapter, playtime: data.run.playtime };
  }
  autosave() { this.saveSlot("auto"); }

  // ---------- level ----------
  chapterDef() { return CHAPTERS[this.run.chapter - 1]; }
  loadLevel(mapIdx, fromSave = false) {
    const ch = this.chapterDef();
    this.run.mapIdx = mapIdx;
    const mdef = ch.maps[mapIdx];
    const grid = mdef.grid.map(r => r.split(""));
    const h = grid.length, w = grid[0].length;
    const rng = mulberry32(this.run.chapter * 100 + mapIdx * 10 + 7);
    const L = {
      def: mdef, grid, w, h, arena: !!mdef.arena,
      rng, vrng: mulberry32(this.run.chapter * 991 + mapIdx),
      hunters: [], drones: [], mines: [], bolts: [], ebolts: [], pickups: [],
      lasers: [], sLasers: [], portals: {}, particles: [],
      npc: null, terminals: [], relays: [], blossoms: [], echoes: [],
      exit: null, exitOpen: false, quota: mdef.quota || 0, frags: 0, fragsHere: 0,
      alert: 0, lastKnown: null, boss: null, secretCells: [],
      switchOn: true, checkpointCells: [], revealed: new Set(),
      time: 0
    };
    const qType = QUEST_TARGET[this.run.chapter];
    let px = TILE * 2, py = TILE * 2;
    const hunterTypes = mdef.hunters || [];
    let hIdx = 0;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const c = grid[y][x];
      const cx = x * TILE + TILE / 2, cy = y * TILE + TILE / 2;
      switch (c) {
        case "P": px = cx; py = cy; grid[y][x] = "."; break;
        case "F": L.pickups.push({ kind: "frag", x: cx, y: cy, ph: rng() * 6 }); grid[y][x] = "."; break;
        case "K": L.pickups.push({ kind: "key", x: cx, y: cy, ph: rng() * 6 }); grid[y][x] = "."; break;
        case "A": L.pickups.push({ kind: "cell", x: cx, y: cy, ph: rng() * 6 }); grid[y][x] = "."; break;
        case "+": L.pickups.push({ kind: "kit", x: cx, y: cy, ph: rng() * 6 }); grid[y][x] = "."; break;
        case "E": {
          const type = hunterTypes[hIdx % Math.max(1, hunterTypes.length)] || "blaze"; hIdx++;
          L.hunters.push(this.makeHunterEnt(type, cx, cy));
          grid[y][x] = ".";
          break;
        }
        case "e": L.drones.push({ x: cx, y: cy, hp: BAL.droneHp, t: rng() * 3, sx: cx, sy: cy, ang: rng() * 6 }); grid[y][x] = "."; break;
        case "N": L.npc = { x: cx, y: cy, id: ch.npc }; grid[y][x] = "."; break;
        case "h": L.terminals.push({ x, y, used: false }); break;
        case "L": L.lasers.push({ x, y, ph: rng() * 2.4 }); grid[y][x] = "."; break;
        case "l": L.sLasers.push({ x, y }); grid[y][x] = "."; break;
        case "S": L.switch = { x, y }; break;
        case "C": L.checkpointCells.push({ x, y, used: false }); break;
        case "X": L.exit = { x, y }; break;
        case "B": L.bossPos = { x: cx, y: cy }; grid[y][x] = "."; break;
        case "%": L.secretCells.push({ x, y }); break;
        case "1": case "2": case "3": case "4": L.portals[c] = { x, y }; break;
        case "Q": {
          if (qType === "blossom") { L.blossoms.push({ x: cx, y: cy, hp: 20 }); }
          else if (qType === "echo") { L.echoes.push({ x: cx, y: cy, ph: rng() * 6 }); }
          else if (qType === "relay") { L.relays.push({ x, y, used: false }); grid[y][x] = "Q"; }
          else if (qType === "zz7") { L.zz7 = { x: cx, y: cy }; }
          else { L.coin = { x: cx, y: cy }; } // ch1 coin
          if (qType !== "relay") grid[y][x] = ".";
          break;
        }
      }
    }
    this.player = {
      x: px, y: py, vx: 0, vy: 0, face: [1, 0],
      dashT: 0, dashCd: 0, pulseCd: 0, empCd: 0, cloakT: 0, cloakCd: 0,
      slowT: 0, slowCd: 0, tpCd: 0, shieldT: 0, shieldCd: 0,
      invuln: BAL.checkpointInvuln, magnetOn: true, anim: 0, hitFlash: 0, bossNoDmg: true
    };
    if (fromSave && this.run.checkpoint && this.run.checkpoint.map === mapIdx) {
      this.player.x = this.run.checkpoint.x; this.player.y = this.run.checkpoint.y;
    }
    // hunter adaptation ("learning enemies"): counter the player's most-used ability
    const use = this.run.abilityUse;
    const top = Object.keys(use).sort((a, b) => use[b] - use[a])[0];
    L.adapt = use[top] >= 6 ? top : null;
    if (L.adapt && this.run.storyFlags.adapt !== L.adapt) {
      this.run.storyFlags.adapt = L.adapt;
      this.toast(this.t("hud.adapt." + L.adapt), "#ff8a80");
    }
    // boss
    if (L.arena) {
      const type = mdef.boss;
      L.boss = {
        type, hp: BAL.bossHp[type], maxHp: BAL.bossHp[type],
        x: L.bossPos.x, y: L.bossPos.y, sx: L.bossPos.x, sy: L.bossPos.y,
        state: "intro", t: 0, phase: 1, stun: 0, vx: 0, vy: 0,
        segs: [], spokes: type === "omega" ? 3 : 0, ang: 0, invertT: 0, introDone: false
      };
      if (type === "leviathan") {
        for (let i = 0; i < 9; i++) L.boss.segs.push({ x: L.bossPos.x - i * 20, y: L.bossPos.y });
      }
    }
    // tileset + static layer
    this.tiles = makeTileset(ch.accent, ch.tint, ch.id, mulberry32(ch.id * 13));
    this.buildStatic(L);
    this.level = L;
    this.camX = px; this.camY = py;
    if (!fromSave) this.autosave();
  }

  makeHunterEnt(type, x, y) {
    return {
      type, x, y, sx: x, sy: y, state: "patrol", stun: 0,
      path: [], pathT: Math.random() * 0.4, target: null, speedMul: 1,
      mineT: 4, tpT: 6, feintT: 0, lungeT: 0, seenT: 0
    };
  }

  buildStatic(L) {
    const c = document.createElement("canvas");
    c.width = L.w * TILE; c.height = L.h * TILE;
    const ctx = c.getContext("2d");
    for (let y = 0; y < L.h; y++) for (let x = 0; x < L.w; x++) {
      const ch = L.grid[y][x];
      ctx.drawImage(ch === "#" || ch === "%" ? this.tiles.wall : this.tiles.floor, x * TILE, y * TILE);
    }
    this.staticLayer = c;
  }
  revealSecret(x, y) {
    const ctx = this.staticLayer.getContext("2d");
    ctx.drawImage(this.tiles.floor, x * TILE, y * TILE);
  }

  solidAt(tx, ty) {
    const L = this.level;
    if (tx < 0 || ty < 0 || tx >= L.w || ty >= L.h) return true;
    const c = L.grid[ty][tx];
    return c === "#" || c === "D" || c === "H";
  }
  walkableForAI(tx, ty) {
    const L = this.level;
    if (tx < 0 || ty < 0 || tx >= L.w || ty >= L.h) return false;
    const c = L.grid[ty][tx];
    return c !== "#" && c !== "D" && c !== "H" && c !== "%";
  }

  moveCircle(ent, dx, dy, r) {
    // axis-separated collision against solid tiles
    const L = this.level;
    const tryAxis = (nx, ny) => {
      const minTx = Math.floor((nx - r) / TILE), maxTx = Math.floor((nx + r) / TILE);
      const minTy = Math.floor((ny - r) / TILE), maxTy = Math.floor((ny + r) / TILE);
      for (let ty = minTy; ty <= maxTy; ty++) for (let tx = minTx; tx <= maxTx; tx++) {
        if (this.solidAt(tx, ty)) return false;
      }
      return true;
    };
    if (dx !== 0 && tryAxis(ent.x + dx, ent.y)) ent.x += dx;
    if (dy !== 0 && tryAxis(ent.x, ent.y + dy)) ent.y += dy;
  }

  // ---------- flow helpers ----------
  startNewGame() {
    this.newRun();
    this.startCutscene([...this.t("cs.intro")], 1, () => this.startChapter(1));
  }
  startChapter(n) {
    this.run.chapter = n;
    this.run.mapIdx = 0;
    const ab = this.chapterDef().newAbilities;
    this.startCutscene([...this.t("cs.ch" + n)], n, () => {
      for (const a of ab) {
        this.run.abilities[a] = true;
        this.toast(`${this.t("hud.newability")}: ${this.t("ability." + a + ".name")} — ${this.t("tut." + a)}`, "#7df9ff");
      }
      if (n === 1) this.toast(this.t("tut.move"), "#9ad8ff");
      this.startChapterMusic();
      this.loadLevel(0);
      this.autosave();
      this.screen = "play";
    });
  }
  startChapterMusic() { this.audio.setMode("explore", this.run.chapter); }
  startCutscene(beats, chapter, after, mode = "chapter") {
    this.cutscene = { beats, idx: 0, chars: 0, chapter, after, mode, t: 0 };
    this.screen = "cutscene";
    this.audio.setMode(mode === "chapter" ? "menu" : "ending", chapter);
  }
  nextMap() {
    const ch = this.chapterDef();
    if (this.run.mapIdx + 1 < ch.maps.length) {
      this.loadLevel(this.run.mapIdx + 1);
      this.autosave();
    } else {
      // chapter done (boss beaten handles its own flow) — safety
      this.advanceChapter();
    }
  }
  advanceChapter() {
    if (this.run.chapter >= 6) { this.screen = "endchoice"; this.endIdx = 1; return; }
    this.startChapter(this.run.chapter + 1);
  }

  // ---------- dialogue / quests ----------
  openDialog(lines, onDone) {
    this.dialog = { lines, idx: 0, chars: 0, onDone };
    this.screen = "dialog";
  }
  npcName(id) { return this.t("npc." + id + ".name"); }
  talkToNpc() {
    const ch = this.chapterDef();
    const id = ch.npc;
    const q = this.run.quests[ch.quest.id] || { state: "inactive", n: 0 };
    this.run.quests[ch.quest.id] = q;
    const nm = this.npcName(id);
    const D = (k) => ({ speaker: nm, text: this.t(k) });
    let lines = [];
    if (q.state === "inactive") {
      if (id === "echo") lines = [D("dlg.echo.1"), D("dlg.echo.2"), D("dlg.echo.3"), D("dlg.echo.q")];
      if (id === "byte") lines = [D("dlg.byte.1"), D("dlg.byte.2"), D("dlg.byte.q")];
      if (id === "pixel") lines = [D("dlg.pixel.1"), D("dlg.pixel.q")];
      if (id === "root") lines = [D("dlg.root.1"), D("dlg.root.q")];
      if (id === "iris") lines = [D("dlg.iris.1"), D("dlg.iris.2")];
      this.openDialog(lines, () => {
        q.state = "active";
        this.toast(`${this.t("q.side")}: ${this.t("quest." + ch.quest.id + ".name")}`, "#b388ff");
        this.checkQuestReady();
        this.screen = "play";
      });
    } else if (q.state === "active") {
      const remind = { echo: "dlg.echo.q", byte: "dlg.byte.q", pixel: "dlg.pixel.q", root: "dlg.root.q", iris: "dlg.iris.2" }[id];
      this.openDialog([D(remind)], () => { this.screen = "play"; });
    } else if (q.state === "ready") {
      const doneKey = { echo: "dlg.echo.qdone", byte: "dlg.byte.qdone", pixel: "dlg.pixel.qdone", root: "dlg.root.qdone", iris: "dlg.iris.qdone" }[id];
      this.openDialog([D(doneKey)], () => {
        q.state = "done";
        this.gainXp(id === "echo" ? 75 : 100);
        if (id === "echo") this.run.storyFlags.coinBuff = 5;
        this.toast(`${this.t("q.done")}: ${this.t("quest." + ch.quest.id + ".name")}`, "#00e676");
        const all = ["ch1", "ch2", "ch3", "ch4", "ch5"].every(k => this.run.quests[k] && this.run.quests[k].state === "done");
        if (all) this.unlock("quests");
        this.screen = "play";
      });
    } else {
      const idle = { echo: "dlg.echo.2", byte: "dlg.byte.1", pixel: "dlg.pixel.1", root: "dlg.root.1", iris: "dlg.iris.1" }[id];
      this.openDialog([D(idle)], () => { this.screen = "play"; });
    }
  }
  checkQuestReady() {
    const ch = this.chapterDef();
    if (!ch.quest) return;
    const q = this.run.quests[ch.quest.id];
    if (q && q.state === "active" && q.n >= ch.quest.count) {
      q.state = "ready";
      this.toast(this.t("q.progress") + ": " + this.t("quest." + ch.quest.id + ".name") + " ✓", "#00e676");
    }
  }
  questProgress(amount = 1) {
    const ch = this.chapterDef();
    if (!ch.quest) return;
    const q = this.run.quests[ch.quest.id] || { state: "inactive", n: 0 };
    this.run.quests[ch.quest.id] = q;
    q.n += amount;
    if (q.state === "inactive" && (ch.quest.type === "fetch" || ch.quest.type === "reach")) q.state = "active";
    this.toast(`${this.t("quest." + ch.quest.id + ".name")}: ${Math.min(q.n, ch.quest.count)}/${ch.quest.count}`, "#b388ff");
    this.checkQuestReady();
  }

  // ---------- hack minigame ----------
  startHack(onWin, onFail) {
    const rng = this.level.rng;
    const dirs = ["up", "down", "left", "right"];
    const seq = [];
    const n = 4 + Math.min(2, this.run.chapter - 2);
    for (let i = 0; i < n; i++) seq.push(dirs[Math.floor(rng() * 4)]);
    this.hackState = { seq, idx: 0, time: 6.5, onWin, onFail };
    this.screen = "hack";
  }

  // ---------- XP ----------
  gainXp(n) {
    this.run.xp += n;
    while (this.run.xp >= XP_NEXT(this.run.level)) {
      this.run.xp -= XP_NEXT(this.run.level);
      this.run.level++;
      this.run.sp++;
      this.run.hp = Math.min(BAL.playerHp, this.run.hp + 40);
      this.run.energy = Math.min(BAL.playerEnergy, this.run.energy + 40);
      this.toast(this.t("hud.levelup"), "#ffc400");
      this.audio.playSfx("levelup");
    }
  }
  skillHas(id) { return !!this.run.skills[id]; }
  skillMod() {
    return {
      dashRange: this.skillHas("g1") ? 1.4 : 1,
      cloakCost: this.skillHas("g2") ? 0.7 : 1,
      cloakDur: this.skillHas("g3") ? 1.5 : 1,
      dashIFrames: this.skillHas("g4"),
      pulseDmg: (this.skillHas("s1") ? 1.5 : 1),
      empRadius: this.skillHas("s2") ? 1.6 : 1,
      shieldDur: this.skillHas("s3") ? 1.5 : 1,
      empBoss: this.skillHas("s4"),
      slowFactor: this.skillHas("c1") ? 0.3 : BAL.slow.factor,
      regen: this.skillHas("c2") ? 1.5 : 1,
      tpRange: this.skillHas("c3") ? 1.5 : 1,
      slowCost: this.skillHas("c4") ? 0.6 : 1
    };
  }

  // ---------- damage ----------
  hurtPlayer(dmg, srcX, srcY) {
    const p = this.player;
    if (p.invuln > 0 || p.shieldT > 0) return;
    if (p.dashT > 0 && this.skillMod().dashIFrames) return;
    this.run.hp -= dmg;
    p.invuln = BAL.invulnAfterHit;
    p.hitFlash = 0.3;
    p.bossNoDmg = false;
    this.audio.playSfx("hurt");
    this.shake(6, 0.3);
    if (srcX !== undefined) {
      const d = Math.max(1, Math.hypot(p.x - srcX, p.y - srcY));
      this.moveCircle(p, (p.x - srcX) / d * 14, (p.y - srcY) / d * 14, 9);
    }
    if (this.run.hp <= 0) {
      this.run.hp = 0;
      this.screen = "gameover";
      this.audio.setMode("menu", this.run.chapter);
    }
  }

  spawnParticles(x, y, color, n, speed = 60) {
    const L = this.level;
    for (let i = 0; i < n; i++) {
      if (L.particles.length > 380) break;
      const a = L.vrng() * Math.PI * 2, s = speed * (0.4 + L.vrng());
      L.particles.push({ x, y, vx: Math.cos(a) * s, vy: Math.sin(a) * s, t: 0.5 + L.vrng() * 0.5, color });
    }
  }

  // =================================================================
  // UPDATE
  // =================================================================
  update(dt) {
    this.frame++;
    this.input.pollPad();
    for (const t of this.toasts) t.t -= dt;
    this.toasts = this.toasts.filter(t => t.t > 0);
    if (this.shakeT > 0) this.shakeT -= dt;

    switch (this.screen) {
      case "menu": this.updateMenu(dt); break;
      case "saves": this.updateSaves(dt); break;
      case "options": this.updateOptions(dt); break;
      case "achievements": case "credits": this.updateSimpleBack(dt); break;
      case "cutscene": this.updateCutscene(dt); break;
      case "play": this.updatePlay(dt); break;
      case "dialog": this.updateDialog(dt); break;
      case "hack": this.updateHack(dt); break;
      case "pause": this.updatePause(dt); break;
      case "skilltree": this.updateSkilltree(dt); break;
      case "inventory": this.updateInventory(dt); break;
      case "quests": this.updateQuests(dt); break;
      case "gameover": this.updateGameover(dt); break;
      case "endchoice": this.updateEndchoice(dt); break;
    }
    this.input.consume();
  }

  navUpDown(len) {
    const inp = this.input;
    if (inp.pressed.has("up")) { this.menuIdx = (this.menuIdx + len - 1) % len; this.audio.playSfx("ui"); }
    if (inp.pressed.has("down")) { this.menuIdx = (this.menuIdx + 1) % len; this.audio.playSfx("ui"); }
  }
  confirmed() {
    return this.input.codesPressed.has("Enter") || this.input.codesPressed.has("NumpadEnter") ||
      this.input.pressed.has("pulse") || this._tapConfirm;
  }
  backed() {
    return this.input.pressed.has("pause") || this.input.pressed.has("dash") && this.screen !== "play";
  }

  updateMenu(dt) {
    this.audio.setMode("menu", 1);
    const hasAuto = !!this.slotInfo("auto");
    const items = ["menu.newgame", "menu.continue", "menu.saves", "menu.options", "menu.achievements", "menu.credits"];
    this.menuItemsLen = items.length;
    this.navUpDown(items.length);
    this.handleMenuMouse(items.length);
    if (this.confirmed()) {
      this.audio.init(); this.audio.playSfx("ui");
      const sel = items[this.menuIdx];
      if (sel === "menu.newgame") this.startNewGame();
      else if (sel === "menu.continue") { if (hasAuto) this.loadSlot("auto"); }
      else if (sel === "menu.saves") { this.screen = "saves"; this.menuIdx = 0; this.savesMode = "load"; }
      else if (sel === "menu.options") { this.screen = "options"; this.menuIdx = 0; this.prevScreen = "menu"; }
      else if (sel === "menu.achievements") { this.screen = "achievements"; }
      else if (sel === "menu.credits") { this.screen = "credits"; this.creditsY = 0; }
    }
  }
  handleMenuMouse(len) {
    // rows are drawn centered; hit-test generously
    if (!this._menuRects) return;
    const { x, y } = this.input.mouse;
    this._tapConfirm = false;
    for (let i = 0; i < this._menuRects.length && i < len; i++) {
      const r = this._menuRects[i];
      if (x >= r[0] && x <= r[0] + r[2] && y >= r[1] && y <= r[1] + r[3]) {
        if (this.input.mouse.clicked) { this.menuIdx = i; this._tapConfirm = true; }
      }
    }
  }

  updateSaves(dt) {
    const slots = ["auto", 0, 1, 2];
    this.navUpDown(slots.length + 1);
    this.handleMenuMouse(slots.length + 1);
    if (this.backed()) { this.screen = this.run && this.savesFrom === "pause" ? "pause" : "menu"; this.menuIdx = 0; return; }
    if (this.confirmed()) {
      this.audio.playSfx("ui");
      if (this.menuIdx === slots.length) { this.screen = this.run && this.savesFrom === "pause" ? "pause" : "menu"; this.menuIdx = 0; return; }
      const slot = slots[this.menuIdx];
      if (this.savesMode === "save" && slot !== "auto" && this.run) {
        this.saveSlot(slot); this.toast(this.t("hud.saved"), "#00e676"); this.audio.playSfx("save");
      } else if (this.slotInfo(slot)) {
        this.loadSlot(slot);
      }
    }
    if (this.input.codesPressed.has("Delete") || this.input.codesPressed.has("KeyX")) {
      const slot = slots[this.menuIdx];
      if (slot !== undefined && this.menuIdx < slots.length) {
        if (this.confirmDelete === this.menuIdx) {
          localStorage.removeItem(slot === "auto" ? "gpnm_auto" : "gpnm_slot" + slot);
          this.confirmDelete = -1; this.audio.playSfx("uiback");
        } else { this.confirmDelete = this.menuIdx; this.toast(this.t("menu.confirmDelete"), "#ff8a80"); }
      }
    }
  }

  updateOptions(dt) {
    // rows: music, sfx, crt, shake, flash, textsize, lang, [binds...], reset, back
    const bindActs = Object.keys(DEFAULT_BINDS);
    const base = 7;
    const total = base + bindActs.length + 2;
    this.navUpDown(total);
    this.handleMenuMouse(total);
    const i = this.menuIdx;
    const left = this.input.pressed.has("left"), right = this.input.pressed.has("right");
    const adj = (v, d, lo, hi, step) => clamp(v + d * step, lo, hi);
    if (left || right) {
      const d = right ? 1 : -1;
      if (i === 0) this.settings.music = adj(this.settings.music, d, 0, 1, 0.1);
      if (i === 1) this.settings.sfx = adj(this.settings.sfx, d, 0, 1, 0.1);
      if (i === 2) this.settings.crt = !this.settings.crt;
      if (i === 3) this.settings.shake = !this.settings.shake;
      if (i === 4) this.settings.flash = !this.settings.flash;
      if (i === 5) this.settings.textScale = adj(this.settings.textScale, d, 0.8, 1.4, 0.1);
      if (i === 6) {
        const li = (LANGS.indexOf(this.settings.lang) + LANGS.length + d) % LANGS.length;
        this.settings.lang = LANGS[li]; this.t = makeT(this.settings.lang);
      }
      this.audio.setVolumes(this.settings.music, this.settings.sfx);
      this.audio.playSfx("ui");
      this.saveJSON("gpnm_settings", this.settings);
    }
    if (this.confirmed()) {
      if (i >= base && i < base + bindActs.length) {
        const act = bindActs[i - base];
        this.rebinding = act;
        this.input.captureCode = (code) => {
          if (code !== "Escape") this.settings.binds[act] = [code, ...(DEFAULT_BINDS[act].slice(1))];
          this.input.captureCode = null;
          this.rebinding = null;
          this.saveJSON("gpnm_settings", this.settings);
        };
      } else if (i === base + bindActs.length) {
        this.settings.binds = JSON.parse(JSON.stringify(DEFAULT_BINDS));
        this.input.binds = this.settings.binds;
        this.saveJSON("gpnm_settings", this.settings);
        this.audio.playSfx("uiback");
      } else if (i === base + bindActs.length + 1 || i === 2 || i === 3 || i === 4) {
        if (i === 2) this.settings.crt = !this.settings.crt;
        else if (i === 3) this.settings.shake = !this.settings.shake;
        else if (i === 4) this.settings.flash = !this.settings.flash;
        else { this.screen = this.prevScreen || "menu"; this.menuIdx = 0; }
        this.saveJSON("gpnm_settings", this.settings);
      }
    }
    if (this.backed()) { this.screen = this.prevScreen || "menu"; this.menuIdx = 0; }
  }

  updateSimpleBack(dt) {
    if (this.screen === "credits") this.creditsY += dt * 28;
    if (this.confirmed() || this.backed()) { this.screen = this.run && this.creditsAfterEnding ? "menu" : "menu"; this.creditsAfterEnding = false; this.menuIdx = 0; }
  }

  updateCutscene(dt) {
    const cs = this.cutscene;
    cs.t += dt;
    cs.chars += dt * 42;
    const cur = cs.beats[cs.idx] || "";
    if (this.confirmed() || this.input.pressed.has("interact") || this._tapConfirm) {
      this.audio.playSfx("ui");
      if (cs.chars < cur.length) cs.chars = cur.length;
      else { cs.idx++; cs.chars = 0; }
    }
    if (this.input.pressed.has("pause")) cs.idx = cs.beats.length;
    if (cs.idx >= cs.beats.length) {
      const after = cs.after;
      this.cutscene = null;
      after();
    }
    // any tap advances (mobile)
    this._tapConfirm = false;
  }

  updateDialog(dt) {
    const d = this.dialog;
    d.chars += dt * 46;
    const cur = d.lines[d.idx];
    if (this.confirmed() || this.input.pressed.has("interact")) {
      this.audio.playSfx("ui");
      if (d.chars < cur.text.length) d.chars = cur.text.length;
      else { d.idx++; d.chars = 0; }
    }
    if (d.idx >= d.lines.length) {
      const cb = d.onDone;
      this.dialog = null;
      cb();
    }
  }

  updateHack(dt) {
    const h = this.hackState;
    h.time -= dt;
    for (const dir of ["up", "down", "left", "right"]) {
      if (this.input.pressed.has(dir)) {
        if (h.seq[h.idx] === dir) {
          h.idx++;
          this.audio.playSfx("ui");
          if (h.idx >= h.seq.length) {
            this.audio.playSfx("hack_ok");
            this.unlock("first_hack");
            this.screen = "play";
            const cb = h.onWin; this.hackState = null; cb();
            return;
          }
        } else {
          this.audio.playSfx("hack_fail");
          this.level.alert = Math.min(1, this.level.alert + 0.15);
          h.idx = 0; h.time = Math.min(h.time, 3.5);
        }
      }
    }
    if (h.time <= 0) {
      this.audio.playSfx("hack_fail");
      this.toast(this.t("hack.fail"), "#ff8a80");
      this.level.alert = Math.min(1, this.level.alert + 0.2);
      this.screen = "play";
      const cb = h.onFail; this.hackState = null; if (cb) cb();
    }
    if (this.input.pressed.has("pause")) { this.screen = "play"; this.hackState = null; }
  }

  updatePause(dt) {
    const items = ["pause.resume", "pause.skills", "pause.inventory", "pause.quests", "menu.saves", "pause.options", "pause.tomenu"];
    this.navUpDown(items.length);
    this.handleMenuMouse(items.length);
    if (this.backed()) { this.screen = "play"; return; }
    if (this.confirmed()) {
      this.audio.playSfx("ui");
      const sel = items[this.menuIdx];
      if (sel === "pause.resume") this.screen = "play";
      if (sel === "pause.skills") { this.screen = "skilltree"; this.skIdx = 0; }
      if (sel === "pause.inventory") { this.screen = "inventory"; this.invIdx = 0; }
      if (sel === "pause.quests") this.screen = "quests";
      if (sel === "menu.saves") { this.screen = "saves"; this.menuIdx = 0; this.savesMode = "save"; this.savesFrom = "pause"; }
      if (sel === "pause.options") { this.screen = "options"; this.menuIdx = 0; this.prevScreen = "pause"; }
      if (sel === "pause.tomenu") { this.autosave(); this.screen = "menu"; this.menuIdx = 0; this.audio.setMode("menu", 1); }
    }
  }

  updateSkilltree(dt) {
    const all = [...SKILLS.ghost, ...SKILLS.surge, ...SKILLS.chrono];
    const cols = 3, rows = 4;
    let c = Math.floor(this.skIdx / rows), r = this.skIdx % rows;
    if (this.input.pressed.has("left")) c = (c + cols - 1) % cols;
    if (this.input.pressed.has("right")) c = (c + 1) % cols;
    if (this.input.pressed.has("up")) r = (r + rows - 1) % rows;
    if (this.input.pressed.has("down")) r = (r + 1) % rows;
    this.skIdx = c * rows + r;
    if (this.confirmed()) {
      const id = all[this.skIdx];
      const branch = id[0] === "g" ? SKILLS.ghost : id[0] === "s" ? SKILLS.surge : SKILLS.chrono;
      const pos = branch.indexOf(id);
      const prereq = pos === 0 || this.run.skills[branch[pos - 1]];
      if (!this.run.skills[id] && prereq && this.run.sp > 0) {
        this.run.skills[id] = true;
        this.run.sp--;
        this.audio.playSfx("levelup");
      } else this.audio.playSfx("uiback");
    }
    if (this.backed() || this.input.pressed.has("skills")) this.screen = this.pauseReturn || "play";
  }

  updateInventory(dt) {
    if (this.input.pressed.has("interact") && this.run.cells > 0) {
      this.run.cells--;
      this.run.energy = Math.min(BAL.playerEnergy, this.run.energy + 30);
      this.audio.playSfx("pickup");
    }
    this.invScroll = (this.invScroll || 0);
    if (this.input.pressed.has("up")) this.invScroll = Math.max(0, this.invScroll - 1);
    if (this.input.pressed.has("down")) this.invScroll = Math.min(Math.max(0, this.run.lore.length - 6), this.invScroll + 1);
    if (this.backed() || this.input.pressed.has("inventory") || this.confirmed() && this.run.cells === 0) this.screen = "play";
  }
  updateQuests(dt) {
    if (this.backed() || this.confirmed() || this.input.pressed.has("quests")) this.screen = "play";
  }
  updateGameover(dt) {
    const items = ["gameover.respawn", "gameover.tomenu"];
    this.navUpDown(items.length);
    this.handleMenuMouse(items.length);
    if (this.confirmed()) {
      if (this.menuIdx === 0) {
        this.run.hp = BAL.playerHp;
        this.run.energy = BAL.playerEnergy;
        this.startChapterMusic();
        this.loadLevel(this.run.checkpoint && this.run.checkpoint.map === this.run.mapIdx ? this.run.mapIdx : this.run.mapIdx, true);
        this.screen = "play";
      } else { this.screen = "menu"; this.menuIdx = 0; }
    }
  }

  updateEndchoice(dt) {
    const mergeOk = this.run.fragTotal >= Math.ceil(TOTAL_FRAGS * 0.75);
    if (this.input.pressed.has("left")) { this.endIdx = (this.endIdx + 2) % 3; this.audio.playSfx("ui"); }
    if (this.input.pressed.has("right")) { this.endIdx = (this.endIdx + 1) % 3; this.audio.playSfx("ui"); }
    this.handleMenuMouse(3);
    if (this._tapConfirm) this.endIdx = this.menuIdx;
    if (this.confirmed()) {
      const pick = ["delete", "save", "merge"][this.endIdx];
      if (pick === "merge" && !mergeOk) { this.audio.playSfx("uiback"); return; }
      this.unlock("end_any");
      if (pick === "merge") this.unlock("end_true");
      const mode = pick;
      this.startCutscene([...this.t("cs.end." + pick)], 6, () => {
        this.creditsAfterEnding = true;
        this.creditsY = 0;
        this.screen = "credits";
        this.audio.setMode("menu", 1);
        localStorage.removeItem("gpnm_auto");
      }, mode);
    }
  }

  // ---------- PLAY ----------
  updatePlay(dt) {
    const L = this.level, p = this.player, run = this.run, inp = this.input;
    const mod = this.skillMod();
    run.playtime += dt;
    if (run.chapter === 1) run.ch1Time += dt;
    L.time += dt;

    // world time scale (slow-mo)
    const wdt = p.slowT > 0 ? dt * mod.slowFactor : dt;

    // --- menus from play
    if (inp.pressed.has("pause")) { this.screen = "pause"; this.menuIdx = 0; return; }
    if (inp.pressed.has("skills")) { this.screen = "skilltree"; this.skIdx = 0; this.pauseReturn = "play"; return; }
    if (inp.pressed.has("inventory")) { this.screen = "inventory"; return; }
    if (inp.pressed.has("quests")) { this.screen = "quests"; return; }

    // --- timers
    p.invuln = Math.max(0, p.invuln - dt);
    p.hitFlash = Math.max(0, p.hitFlash - dt);
    p.pulseCd = Math.max(0, p.pulseCd - dt);
    p.dashCd = Math.max(0, p.dashCd - dt);
    p.empCd = Math.max(0, p.empCd - dt);
    p.cloakCd = Math.max(0, p.cloakCd - dt);
    p.slowCd = Math.max(0, p.slowCd - dt);
    p.tpCd = Math.max(0, p.tpCd - dt);
    p.shieldCd = Math.max(0, p.shieldCd - dt);
    p.cloakT = Math.max(0, p.cloakT - dt);
    p.shieldT = Math.max(0, p.shieldT - dt);
    if (p.slowT > 0) {
      p.slowT -= dt;
      run.energy -= 8 * dt * mod.slowCost;
      if (run.energy <= 0) { run.energy = 0; p.slowT = 0; }
    }

    // --- energy regen
    run.energy = Math.min(BAL.playerEnergy, run.energy + BAL.energyRegen * mod.regen * dt);

    // --- movement
    const [mx, my] = inp.moveVec();
    const inv = L.boss && L.boss.invertT > 0 ? -1 : 1;
    let speed = BAL.playerSpeed;
    if (p.dashT > 0) { p.dashT -= dt; speed *= BAL.dash.mult; }
    const vx = mx * inv * speed * dt, vy = my * inv * speed * dt;
    if (mx || my) {
      p.face = [mx * inv, my * inv];
      p.anim += dt * 10;
    }
    this.moveCircle(p, vx, vy, TILE * 0.5 * BAL.hitboxScale + 3);

    // --- abilities
    const useAbility = (name) => { run.storyFlags.abilityUsed[name] = true;
      if (Object.keys(run.storyFlags.abilityUsed).length >= 8) this.unlock("all_abilities"); };
    if (inp.pressed.has("dash") && run.abilities.dash && p.dashCd <= 0 && run.energy >= BAL.dash.cost) {
      run.energy -= BAL.dash.cost;
      p.dashT = BAL.dash.dur * mod.dashRange;
      p.dashCd = BAL.dash.cd;
      run.abilityUse.dash++;
      useAbility("dash");
      this.audio.playSfx("dash");
      this.spawnParticles(p.x, p.y, "#7df9ff", 8, 40);
    }
    if (inp.pressed.has("emp") && run.abilities.emp && p.empCd <= 0 && run.energy >= BAL.emp.cost) {
      run.energy -= BAL.emp.cost;
      p.empCd = BAL.emp.cd;
      run.abilityUse.emp++;
      useAbility("emp");
      this.audio.playSfx("emp");
      this.shake(8, 0.3);
      const r = BAL.emp.radius * mod.empRadius * TILE;
      this.spawnParticles(p.x, p.y, "#40c4ff", 40, 160);
      const adaptMul = L.adapt === "emp" ? 0.5 : 1;
      for (const hu of L.hunters) if (dist2(hu.x, hu.y, p.x, p.y) < r * r) { hu.stun = Math.max(hu.stun, BAL.emp.stun * adaptMul); this.gainXp(BAL.xp.stun); }
      L.drones = L.drones.filter(d => {
        if (dist2(d.x, d.y, p.x, p.y) < r * r) { this.spawnParticles(d.x, d.y, "#ff1744", 12); this.gainXp(BAL.xp.drone); this.audio.playSfx("boom", { vol: 0.5 }); return false; }
        return true;
      });
      L.mines = L.mines.filter(m => dist2(m.x, m.y, p.x, p.y) >= r * r);
      if (L.boss && mod.empBoss && dist2(L.boss.x, L.boss.y, p.x, p.y) < r * r) L.boss.stun = Math.max(L.boss.stun, 1);
    }
    if (inp.pressed.has("cloak") && run.abilities.cloak && p.cloakCd <= 0 && run.energy >= BAL.cloak.cost * mod.cloakCost) {
      run.energy -= BAL.cloak.cost * mod.cloakCost;
      p.cloakT = BAL.cloak.dur * mod.cloakDur;
      p.cloakCd = BAL.cloak.cd;
      run.abilityUse.cloak++;
      useAbility("cloak");
      this.audio.playSfx("cloak");
      for (const hu of L.hunters) if (hu.state === "chase") hu.state = "search";
    }
    if (inp.pressed.has("slow") && run.abilities.slow && p.slowCd <= 0 && run.energy >= BAL.slow.cost * mod.slowCost) {
      run.energy -= BAL.slow.cost * mod.slowCost * 0.5;
      p.slowT = BAL.slow.dur;
      p.slowCd = BAL.slow.cd;
      run.abilityUse.slow++;
      useAbility("slow");
      this.audio.playSfx("slow");
    }
    if (inp.pressed.has("shield") && run.abilities.shield && p.shieldCd <= 0 && run.energy >= BAL.shield.cost) {
      run.energy -= BAL.shield.cost;
      p.shieldT = BAL.shield.dur * mod.shieldDur;
      p.shieldCd = BAL.shield.cd;
      useAbility("shield");
      this.audio.playSfx("shield");
    }
    if (inp.pressed.has("teleport") && run.abilities.teleport && p.tpCd <= 0 && run.energy >= BAL.teleport.cost) {
      const range = BAL.teleport.range * mod.tpRange * TILE;
      const fm = Math.hypot(p.face[0], p.face[1]) || 1;
      const dx = p.face[0] / fm, dy = p.face[1] / fm;
      let bestX = p.x, bestY = p.y;
      for (let d = range; d > TILE * 0.5; d -= 8) {
        const nx = p.x + dx * d, ny = p.y + dy * d;
        const tx = Math.floor(nx / TILE), ty = Math.floor(ny / TILE);
        if (!this.solidAt(tx, ty)) { bestX = nx; bestY = ny; break; }
      }
      if (bestX !== p.x || bestY !== p.y) {
        run.energy -= BAL.teleport.cost;
        p.tpCd = BAL.teleport.cd;
        useAbility("teleport");
        this.spawnParticles(p.x, p.y, "#40c4ff", 14, 90);
        p.x = bestX; p.y = bestY;
        this.spawnParticles(p.x, p.y, "#40c4ff", 14, 90);
        this.audio.playSfx("teleport");
      }
    }
    if (inp.pressed.has("magnet") && run.abilities.magnet) {
      p.magnetOn = !p.magnetOn;
      useAbility("magnet");
      this.audio.playSfx("ui");
      this.toast(`${this.t("ability.magnet.name")}: ${p.magnetOn ? this.t("opt.on") : this.t("opt.off")}`);
    }
    if (inp.held.has("pulse") && p.pulseCd <= 0 && run.energy >= BAL.pulse.cost) {
      run.energy -= BAL.pulse.cost;
      p.pulseCd = BAL.pulse.cd;
      const fm = Math.hypot(p.face[0], p.face[1]) || 1;
      L.bolts.push({ x: p.x, y: p.y, vx: p.face[0] / fm * BAL.pulse.speed, vy: p.face[1] / fm * BAL.pulse.speed, t: BAL.pulse.life });
      useAbility("pulse");
      this.audio.playSfx("shot", { vol: 0.6 });
    }

    // --- tile interactions
    const ptx = Math.floor(p.x / TILE), pty = Math.floor(p.y / TILE);
    const tileHere = L.grid[pty] && L.grid[pty][ptx];
    // secret reveal
    if (tileHere === "%") {
      L.grid[pty][ptx] = ".";
      this.revealSecret(ptx, pty);
      run.storyFlags.secrets++;
      this.gainXp(BAL.xp.secret);
      this.toast(this.t("hud.secret"), "#ffc400");
      this.audio.playSfx("save");
      if (run.storyFlags.secrets >= 3) this.unlock("secret3");
    }
    // checkpoint
    for (const cp of L.checkpointCells) {
      if (cp.x === ptx && cp.y === pty && !cp.used) {
        cp.used = true;
        run.checkpoint = { map: run.mapIdx, x: p.x, y: p.y };
        run.hp = Math.min(BAL.playerHp, run.hp + 25);
        this.autosave();
        this.toast(this.t("hud.checkpoint"), "#00e5ff");
        this.audio.playSfx("save");
      }
    }
    // portals
    for (const k of ["1", "2", "3", "4"]) {
      const po = L.portals[k];
      if (po && po.x === ptx && po.y === pty && (this._portalCd || 0) <= 0) {
        const pair = { "1": "2", "2": "1", "3": "4", "4": "3" }[k];
        const q = L.portals[pair];
        if (q) {
          p.x = q.x * TILE + TILE / 2; p.y = q.y * TILE + TILE / 2;
          this._portalCd = 1;
          this.audio.playSfx("portal");
          this.spawnParticles(p.x, p.y, "#e040fb", 20, 120);
        }
      }
    }
    this._portalCd = Math.max(0, (this._portalCd || 0) - dt);
    // lasers hurt
    const laserHurt = (lx, ly) => {
      if (p.dashT > 0) return; // dash phases through lasers
      if (Math.floor(p.x / TILE) === lx && Math.floor(p.y / TILE) === ly) this.hurtPlayer(BAL.laserDmg, lx * TILE + 16, ly * TILE + 16);
    };
    for (const la of L.lasers) {
      const phase = (L.time + la.ph) % 2.4;
      la.on = phase > 1.5;
      la.warn = phase > 0.9 && phase <= 1.5;
      if (la.on) laserHurt(la.x, la.y);
    }
    for (const la of L.sLasers) if (L.switchOn) laserHurt(la.x, la.y);
    // exit
    L.exitOpen = !L.arena && L.fragsHere >= L.quota;
    if (L.exit && ptx === L.exit.x && pty === L.exit.y) {
      if (L.exitOpen) {
        if (run.chapter === 1 && run.mapIdx === 1 && run.ch1Time < 360) this.unlock("speed1");
        this.audio.playSfx("door");
        this.nextMap();
        return;
      } else if (!this._exitHintT || this._exitHintT <= 0) {
        this.toast(this.t("hud.exitLocked"), "#ff8a80");
        this._exitHintT = 3;
      }
    }
    this._exitHintT = Math.max(0, (this._exitHintT || 0) - dt);

    // --- interact (E)
    this.interactHint = null;
    const near = (tx, ty, r = 1.2) => dist2(p.x, p.y, tx * TILE + 16, ty * TILE + 16) < (TILE * r) * (TILE * r);
    // doors
    for (let ty = pty - 1; ty <= pty + 1; ty++) for (let tx = ptx - 1; tx <= ptx + 1; tx++) {
      const c = L.grid[ty] && L.grid[ty][tx];
      if (c === "D" && near(tx, ty)) {
        this.interactHint = run.keys > 0 ? this.t("hud.doorOpen") : this.t("hud.needKey");
        if (inp.pressed.has("interact")) {
          if (run.keys > 0) {
            run.keys--;
            L.grid[ty][tx] = ".";
            this.revealSecret(tx, ty);
            this.audio.playSfx("door");
            this.toast(this.t("hud.doorOpen"), "#ffd740");
          } else this.audio.playSfx("uiback");
        }
      }
      if (c === "H" && near(tx, ty) && run.abilities.hack) {
        this.interactHint = this.t("hud.hack");
        if (inp.pressed.has("interact")) {
          this.startHack(() => {
            L.grid[ty][tx] = ".";
            this.revealSecret(tx, ty);
            this.audio.playSfx("door");
          });
          return;
        }
      }
    }
    // npc
    if (L.npc && dist2(p.x, p.y, L.npc.x, L.npc.y) < (TILE * 1.4) ** 2) {
      this.interactHint = this.t("hud.talk");
      if (inp.pressed.has("interact")) { this.talkToNpc(); return; }
    }
    // zz7
    if (L.zz7 && dist2(p.x, p.y, L.zz7.x, L.zz7.y) < (TILE * 1.4) ** 2) {
      this.interactHint = this.t("hud.talk");
      if (inp.pressed.has("interact")) {
        const nm = this.npcName("zz7");
        this.openDialog([{ speaker: nm, text: this.t("dlg.zz7.1") }], () => {
          L.zz7 = null;
          this.questProgress();
          this.screen = "play";
        });
        return;
      }
    }
    // lore terminals
    for (const tm of L.terminals) {
      if (near(tm.x, tm.y) && !tm.used) {
        this.interactHint = this.t("hud.read");
        if (inp.pressed.has("interact")) {
          tm.used = true;
          const pool = this.t("frag.ch" + run.chapter);
          const line = pool[Math.floor(L.rng() * pool.length)];
          this.openDialog([{ speaker: "TERMINAL", text: line }], () => { this.screen = "play"; });
          return;
        }
      }
    }
    // relays (ch2 quest)
    for (const rl of L.relays) {
      if (near(rl.x, rl.y) && !rl.used) {
        this.interactHint = this.t("hud.hack");
        if (inp.pressed.has("interact")) {
          this.startHack(() => {
            rl.used = true;
            L.grid[rl.y][rl.x] = ".";
            this.revealSecret(rl.x, rl.y);
            this.questProgress();
          });
          return;
        }
      }
    }
    // switch
    if (L.switch && near(L.switch.x, L.switch.y)) {
      this.interactHint = this.t("hud.switch");
      if (inp.pressed.has("interact")) {
        L.switchOn = !L.switchOn;
        this.audio.playSfx("door");
      }
    }
    // boss arena hacker terminals
    if (L.boss && L.boss.type === "hacker") {
      for (const tm of L.terminals) {
        if (near(tm.x, tm.y) && !tm.used) {
          this.interactHint = this.t("hud.hack");
          if (inp.pressed.has("interact")) {
            this.startHack(() => {
              tm.used = true;
              L.boss.stun = 3;
              L.boss.hp -= 40;
              this.spawnParticles(L.boss.x, L.boss.y, "#7c4dff", 24, 140);
              this.audio.playSfx("boom");
            });
            return;
          }
        }
      }
    }

    // --- pickups & quest touchables
    const mag = run.abilities.magnet && p.magnetOn ? BAL.magnetRadius * TILE : 0;
    for (const pk of L.pickups) {
      if (mag && dist2(pk.x, pk.y, p.x, p.y) < mag * mag) {
        const d = Math.max(1, Math.hypot(p.x - pk.x, p.y - pk.y));
        pk.x += (p.x - pk.x) / d * 130 * dt;
        pk.y += (p.y - pk.y) / d * 130 * dt;
      }
    }
    L.pickups = L.pickups.filter(pk => {
      if (dist2(pk.x, pk.y, p.x, p.y) > (TILE * 0.7) ** 2) return true;
      if (pk.kind === "frag") {
        run.fragTotal++;
        L.fragsHere++;
        run.fragByCh[run.chapter] = (run.fragByCh[run.chapter] || 0) + 1;
        this.gainXp(BAL.xp.frag);
        L.alert = Math.min(1, L.alert + BAL.alertPerFrag);
        const pool = this.t("frag.ch" + run.chapter);
        const li = Math.min(run.fragByCh[run.chapter] - 1, pool.length - 1);
        if (!run.lore.includes(run.chapter + ":" + li)) run.lore.push(run.chapter + ":" + li);
        this.toast(pool[li], "#ffe082");
        this.audio.playSfx("frag");
        this.unlock("first_frag");
        if (L.fragsHere >= L.quota && !this._exitToldOpen) { this._exitToldOpen = true; this.toast(this.t("hud.exitOpen"), "#00e676"); }
        // all frags of chapter?
        const chFrags = CHAPTERS[run.chapter - 1].maps.reduce((s, m) => s + m.grid.join("").split("F").length - 1, 0);
        if (run.fragByCh[run.chapter] >= chFrags) this.unlock("all_frags_ch");
      } else if (pk.kind === "key") { run.keys++; this.toast(this.t("hud.keyGet"), "#ffd740"); this.audio.playSfx("pickup"); }
      else if (pk.kind === "cell") { run.energy = Math.min(BAL.playerEnergy, run.energy + 30); run.cells++; this.toast(this.t("hud.cellGet"), "#00e676"); this.audio.playSfx("pickup"); }
      else if (pk.kind === "kit") { run.hp = Math.min(BAL.playerHp, run.hp + 30); this.toast(this.t("hud.hpGet"), "#ff8a80"); this.audio.playSfx("pickup"); }
      return false;
    });
    if (L.coin && dist2(L.coin.x, L.coin.y, p.x, p.y) < (TILE * 0.8) ** 2) {
      L.coin = null;
      this.toast(this.t("hud.questItem"), "#ffc400");
      this.audio.playSfx("frag");
      this.questProgress();
    }
    L.echoes = L.echoes.filter(e => {
      if (dist2(e.x, e.y, p.x, p.y) < (TILE * 0.8) ** 2) {
        this.spawnParticles(e.x, e.y, "#40c4ff", 16, 90);
        this.audio.playSfx("portal");
        this.questProgress();
        return false;
      }
      return true;
    });

    // --- player bolts
    L.bolts = L.bolts.filter(b => {
      b.t -= dt;
      b.x += b.vx * dt; b.y += b.vy * dt;
      const tx = Math.floor(b.x / TILE), ty = Math.floor(b.y / TILE);
      if (b.t <= 0 || this.solidAt(tx, ty)) { this.spawnParticles(b.x, b.y, "#7df9ff", 4, 50); return false; }
      const dmg = BAL.pulse.dmg * mod.pulseDmg + (run.storyFlags.coinBuff || 0);
      for (const d of L.drones) {
        if (dist2(b.x, b.y, d.x, d.y) < 16 * 16) {
          d.hp -= dmg;
          this.spawnParticles(d.x, d.y, "#ff5a70", 6, 70);
          this.audio.playSfx("hit", { vol: 0.5 });
          return false;
        }
      }
      for (const bl of L.blossoms) {
        if (dist2(b.x, b.y, bl.x, bl.y) < 18 * 18) {
          bl.hp -= dmg;
          this.spawnParticles(bl.x, bl.y, "#d500f9", 8, 80);
          this.audio.playSfx("hit", { vol: 0.5 });
          return false;
        }
      }
      if (L.boss && L.boss.state !== "intro" && dist2(b.x, b.y, L.boss.x, L.boss.y) < 34 * 34) {
        let mult = 1;
        if (L.boss.type === "guardian" && L.boss.state === "stunned") mult = 2;
        L.boss.hp -= dmg * mult;
        this.spawnParticles(b.x, b.y, "#ffffff", 6, 80);
        this.audio.playSfx("hit", { vol: 0.6 });
        return false;
      }
      if (L.boss && L.boss.type === "leviathan") {
        for (const s of L.boss.segs) {
          if (dist2(b.x, b.y, s.x, s.y) < 18 * 18) { this.spawnParticles(b.x, b.y, "#76ff03", 4, 60); return false; }
        }
      }
      return true;
    });
    L.drones = L.drones.filter(d => {
      if (d.hp <= 0) { this.gainXp(BAL.xp.drone); this.spawnParticles(d.x, d.y, "#ff1744", 14, 110); this.audio.playSfx("boom", { vol: 0.5 }); return false; }
      return true;
    });
    L.blossoms = L.blossoms.filter(bl => {
      if (bl.hp <= 0) { this.spawnParticles(bl.x, bl.y, "#d500f9", 20, 120); this.audio.playSfx("boom", { vol: 0.5 }); this.questProgress(); return false; }
      return true;
    });

    // --- drones AI (wdt: slowed by slow-mo)
    for (const d of L.drones) {
      d.t -= wdt;
      d.ang += wdt * 1.2;
      // hover around spawn, shoot if LOS in ch3+
      d.x = d.sx + Math.cos(d.ang) * 18;
      d.y = d.sy + Math.sin(d.ang * 0.8) * 18;
      if (dist2(d.x, d.y, p.x, p.y) < (TILE * 0.7) ** 2) this.hurtPlayer(BAL.droneTouchDmg, d.x, d.y);
      if (run.chapter >= 3 && d.t <= 0 && dist2(d.x, d.y, p.x, p.y) < (TILE * 6) ** 2 && this.los(d.x, d.y, p.x, p.y) && p.cloakT <= 0) {
        d.t = 2.4;
        const dd = Math.max(1, Math.hypot(p.x - d.x, p.y - d.y));
        L.ebolts.push({ x: d.x, y: d.y, vx: (p.x - d.x) / dd * 150, vy: (p.y - d.y) / dd * 150, t: 3 });
        this.audio.playSfx("eshot", { vol: 0.4, pan: clamp((d.x - p.x) / 300, -1, 1) });
      }
    }
    // --- enemy bolts
    L.ebolts = L.ebolts.filter(b => {
      b.t -= wdt;
      if (b.home && L.boss) {
        const dd = Math.max(1, Math.hypot(p.x - b.x, p.y - b.y));
        b.vx = lerp(b.vx, (p.x - b.x) / dd * 170, wdt * 2);
        b.vy = lerp(b.vy, (p.y - b.y) / dd * 170, wdt * 2);
      }
      b.x += b.vx * wdt; b.y += b.vy * wdt;
      const tx = Math.floor(b.x / TILE), ty = Math.floor(b.y / TILE);
      if (b.t <= 0 || this.solidAt(tx, ty)) return false;
      if (dist2(b.x, b.y, p.x, p.y) < (TILE * 0.45) ** 2) { this.hurtPlayer(BAL.boltDmg, b.x, b.y); return false; }
      return true;
    });

    // --- mines
    L.mines = L.mines.filter(m => {
      if (dist2(m.x, m.y, p.x, p.y) < (TILE * 0.6) ** 2) {
        this.hurtPlayer(BAL.mineDmg, m.x, m.y);
        this.spawnParticles(m.x, m.y, "#ff00aa", 16, 130);
        this.audio.playSfx("mine");
        return false;
      }
      return true;
    });

    // --- hunters
    L.alert = Math.max(0, L.alert - BAL.alertDecay * dt);
    this.audio.setIntensity(Math.max(L.alert, L.hunters.some(h => h.state === "chase") ? 0.7 : 0));
    for (const hu of L.hunters) this.updateHunter(hu, wdt, dt);

    // --- boss
    if (L.boss) this.updateBoss(wdt, dt);

    // --- particles
    L.particles = L.particles.filter(pa => {
      pa.t -= dt;
      pa.x += pa.vx * dt; pa.y += pa.vy * dt;
      pa.vx *= 0.96; pa.vy *= 0.96;
      return pa.t > 0;
    });

    // --- camera
    const vw = innerWidth, vh = innerHeight;
    this.camX = lerp(this.camX, p.x, 1 - Math.pow(0.001, dt));
    this.camY = lerp(this.camY, p.y, 1 - Math.pow(0.001, dt));
    this.camX = clamp(this.camX, Math.min(vw / 2, L.w * TILE / 2), Math.max(L.w * TILE - vw / 2, L.w * TILE / 2));
    this.camY = clamp(this.camY, Math.min(vh / 2, L.h * TILE / 2), Math.max(L.h * TILE - vh / 2, L.h * TILE / 2));
  }

  los(ax, ay, bx, by) {
    // tile raycast
    const steps = Math.ceil(Math.hypot(bx - ax, by - ay) / (TILE / 2));
    for (let i = 1; i < steps; i++) {
      const x = ax + (bx - ax) * i / steps, y = ay + (by - ay) * i / steps;
      if (this.solidAt(Math.floor(x / TILE), Math.floor(y / TILE))) return false;
    }
    return true;
  }

  bfsPath(fromX, fromY, toX, toY) {
    const L = this.level;
    const sx = clamp(Math.floor(fromX / TILE), 0, L.w - 1), sy = clamp(Math.floor(fromY / TILE), 0, L.h - 1);
    const tx = clamp(Math.floor(toX / TILE), 0, L.w - 1), ty = clamp(Math.floor(toY / TILE), 0, L.h - 1);
    if (sx === tx && sy === ty) return [];
    const prev = new Map();
    const key = (x, y) => y * L.w + x;
    const q = [[sx, sy]];
    prev.set(key(sx, sy), -1);
    let found = false;
    for (let i = 0; i < q.length && !found; i++) {
      const [x, y] = q[i];
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy;
        if (!this.walkableForAI(nx, ny) || prev.has(key(nx, ny))) continue;
        prev.set(key(nx, ny), key(x, y));
        if (nx === tx && ny === ty) { found = true; break; }
        q.push([nx, ny]);
      }
    }
    if (!prev.has(key(tx, ty))) return [];
    const path = [];
    let cur = key(tx, ty);
    while (cur !== -1 && cur !== key(sx, sy)) {
      path.push([cur % L.w, Math.floor(cur / L.w)]);
      cur = prev.get(cur);
    }
    path.reverse();
    return path.map(([x, y]) => [x * TILE + TILE / 2, y * TILE + TILE / 2]);
  }

  updateHunter(hu, wdt, dt) {
    const L = this.level, p = this.player, run = this.run;
    if (hu.stun > 0) { hu.stun -= dt; return; }
    const adapt = L.adapt;
    let speed = BAL.hunterSpeed[hu.type] * (1 + L.alert * 0.35);
    if (adapt === "dash") speed *= 1.08;
    const slowResist = hu.type === "glitch" ? 0.5 : adapt === "slow" ? 0.4 : 0;
    const edt = p.slowT > 0 ? dt * (this.skillMod().slowFactor + (1 - this.skillMod().slowFactor) * slowResist) : dt;

    const seeR = BAL.hunterVision * TILE * (1 + L.alert * 0.3);
    const hearR = BAL.hunterHearing * TILE * (adapt === "cloak" ? 1.8 : 1);
    const canSee = p.cloakT <= 0 && dist2(hu.x, hu.y, p.x, p.y) < seeR * seeR && this.los(hu.x, hu.y, p.x, p.y);
    const canHear = dist2(hu.x, hu.y, p.x, p.y) < hearR * hearR;

    if (canSee || (canHear && p.cloakT <= 0)) {
      if (hu.state !== "chase") { this.audio.playSfx("alert", { vol: 0.5, pan: clamp((hu.x - p.x) / 400, -1, 1) }); }
      hu.state = "chase";
      hu.seenT = 3.5;
      L.lastKnown = { x: p.x, y: p.y }; // group behavior: shared last-known position
    } else if (hu.state === "chase") {
      hu.seenT -= dt;
      if (hu.seenT <= 0) hu.state = "search";
    }

    // personality quirks
    if (hu.type === "blaze" && hu.state === "chase" && canSee) hu.speedMul = 1.5;
    else hu.speedMul = 1;
    if (hu.type === "phantom" && hu.state === "chase") {
      hu.tpT -= dt;
      if (hu.tpT <= 0) {
        hu.tpT = 7;
        // blink near the player's predicted position
        const aheadX = p.x + p.face[0] * TILE * 3, aheadY = p.y + p.face[1] * TILE * 3;
        const tx = clamp(Math.floor(aheadX / TILE), 1, L.w - 2), ty = clamp(Math.floor(aheadY / TILE), 1, L.h - 2);
        if (this.walkableForAI(tx, ty)) {
          this.spawnParticles(hu.x, hu.y, "#b388ff", 10, 80);
          hu.x = tx * TILE + TILE / 2; hu.y = ty * TILE + TILE / 2;
          this.spawnParticles(hu.x, hu.y, "#b388ff", 10, 80);
          this.audio.playSfx("teleport", { vol: 0.4 });
          hu.path = [];
        }
      }
    }
    if (hu.type === "widow") {
      hu.mineT -= dt;
      if (hu.mineT <= 0 && L.mines.length < 6) {
        hu.mineT = 5;
        L.mines.push({ x: hu.x, y: hu.y });
      }
    }
    if (hu.type === "glitch") {
      hu.feintT -= dt;
      if (hu.feintT <= 0) { hu.feintT = 4 + L.rng() * 3; hu.lungeT = 1.6; }
      if (hu.lungeT > 0) {
        hu.lungeT -= dt;
        hu.speedMul = hu.lungeT > 0.8 ? -0.6 : 1.9; // fake retreat, then lunge
      }
    }

    // pathing
    hu.pathT -= dt;
    if (hu.pathT <= 0) {
      hu.pathT = 0.5;
      let goal = null;
      if (hu.state === "chase") goal = [p.x, p.y];
      else if (hu.state === "search" && L.lastKnown) goal = [L.lastKnown.x, L.lastKnown.y];
      else {
        // patrol: wander to random floor tile
        if (!hu.path.length) {
          for (let tries = 0; tries < 8; tries++) {
            const tx = 1 + Math.floor(L.rng() * (L.w - 2)), ty = 1 + Math.floor(L.rng() * (L.h - 2));
            if (this.walkableForAI(tx, ty)) { goal = [tx * TILE + 16, ty * TILE + 16]; break; }
          }
        }
      }
      if (goal) hu.path = this.bfsPath(hu.x, hu.y, goal[0], goal[1]);
    }
    if (hu.path.length) {
      const [gx, gy] = hu.path[0];
      const d = Math.hypot(gx - hu.x, gy - hu.y);
      const sp = Math.max(20, speed * hu.speedMul);
      if (d < 4) hu.path.shift();
      else {
        let mx = (gx - hu.x) / d, my = (gy - hu.y) / d;
        if (hu.type === "glitch") { // jitter
          const j = Math.sin(L.time * 13 + hu.sx) * 0.35;
          const tmp = mx; mx = mx - my * j; my = my + tmp * j;
        }
        hu.x += mx * sp * edt;
        hu.y += my * sp * edt;
      }
    }
    if (hu.state === "search" && L.lastKnown && dist2(hu.x, hu.y, L.lastKnown.x, L.lastKnown.y) < TILE * TILE) {
      hu.state = "patrol";
    }
    // touch damage
    if (dist2(hu.x, hu.y, p.x, p.y) < (TILE * 0.62) ** 2) this.hurtPlayer(BAL.hunterTouchDmg, hu.x, hu.y);
  }

  updateBoss(wdt, dt) {
    const L = this.level, B = L.boss, p = this.player, run = this.run;
    if (B.state === "intro") {
      if (!B.introDone) {
        B.introDone = true;
        this.audio.setMode("boss", run.chapter);
        this.openDialog([{ speaker: this.t("boss." + B.type + ".name"), text: this.t("boss." + B.type + ".intro") }],
          () => { B.state = "fight"; this.screen = "play"; });
      }
      return;
    }
    if (B.hp <= 0 && B.state !== "dead") {
      B.state = "dead";
      this.audio.playSfx("bossdie");
      this.shake(14, 0.8);
      this.spawnParticles(B.x, B.y, "#ffffff", 60, 200);
      this.gainXp(BAL.xp.boss);
      if (B.type === "guardian") this.unlock("boss1");
      if (B.type === "architect") this.unlock("boss6");
      if (p.bossNoDmg) this.unlock("no_dmg_boss");
      this.openDialog([{ speaker: this.t("boss." + B.type + ".name"), text: this.t("boss." + B.type + ".defeat") }], () => {
        if (B.type === "architect") { this.screen = "endchoice"; this.endIdx = 1; }
        else { this.advanceChapter(); }
      });
      return;
    }
    if (B.state === "dead") return;
    if (B.stun > 0) { B.stun -= dt; B.state = B.state === "charge" ? "stunned" : B.state; }
    B.t += wdt;
    B.ang += wdt;
    B.invertT = Math.max(0, B.invertT - dt);
    const phase = B.hp < B.maxHp * 0.5 ? 2 : 1;
    B.phase = phase;
    const aim = () => {
      const d = Math.max(1, Math.hypot(p.x - B.x, p.y - B.y));
      return [(p.x - B.x) / d, (p.y - B.y) / d];
    };
    const shoot = (vx, vy, speed, home = false) => {
      L.ebolts.push({ x: B.x, y: B.y, vx: vx * speed, vy: vy * speed, t: 4, home });
      this.audio.playSfx("eshot", { vol: 0.5 });
    };
    const ring = (n, speed, offset = 0) => {
      for (let i = 0; i < n; i++) {
        const a = offset + i * Math.PI * 2 / n;
        shoot(Math.cos(a), Math.sin(a), speed);
      }
    };
    const touchDmg = (r, dmg) => {
      if (dist2(B.x, B.y, p.x, p.y) < r * r) this.hurtPlayer(dmg, B.x, B.y);
    };

    if (B.stun > 0) return;

    switch (B.type) {
      case "guardian": {
        if (B.state === "fight" && B.t > 1.6) { B.state = "telegraph"; B.t = 0; }
        else if (B.state === "telegraph" && B.t > 0.65) {
          B.state = "charge"; B.t = 0;
          const [dx, dy] = aim();
          B.vx = dx * 340; B.vy = dy * 340;
          this.audio.playSfx("dash", { vol: 0.7 });
        } else if (B.state === "charge") {
          B.x += B.vx * wdt; B.y += B.vy * wdt;
          const tx = Math.floor(B.x / TILE), ty = Math.floor(B.y / TILE);
          if (this.solidAt(tx, ty)) {
            B.x -= B.vx * wdt; B.y -= B.vy * wdt;
            B.state = "stunned"; B.t = 0;
            this.shake(10, 0.4);
            this.audio.playSfx("boom");
            if (phase === 2) ring(8, 130);
          }
        } else if (B.state === "stunned" && B.t > 1.4) { B.state = "fight"; B.t = 0; }
        touchDmg(36, 30);
        break;
      }
      case "hacker": {
        if (B.t > (phase === 2 ? 2.2 : 3)) {
          B.t = 0;
          B.cycle = (B.cycle || 0) + 1;
          if (B.cycle % 4 === 0) {
            B.invertT = 2.5;
            this.audio.playSfx("invert");
            this.toast("!! INVERT !!", "#ff4dff");
          } else if (B.cycle % 2 === 0) {
            // teleport
            for (let tries = 0; tries < 12; tries++) {
              const tx = 2 + Math.floor(L.rng() * (L.w - 4)), ty = 2 + Math.floor(L.rng() * (L.h - 4));
              if (this.walkableForAI(tx, ty) && dist2(tx * TILE, ty * TILE, p.x, p.y) > (TILE * 4) ** 2) {
                this.spawnParticles(B.x, B.y, "#7c4dff", 20, 120);
                B.x = tx * TILE + 16; B.y = ty * TILE + 16;
                this.spawnParticles(B.x, B.y, "#7c4dff", 20, 120);
                this.audio.playSfx("teleport");
                break;
              }
            }
          } else {
            const [dx, dy] = aim();
            shoot(dx, dy, 160, true);
            if (phase === 2) { shoot(dy, -dx, 150, true); shoot(-dy, dx, 150, true); }
          }
        }
        touchDmg(34, 24);
        break;
      }
      case "queen": {
        if (B.t > (phase === 2 ? 4.5 : 6)) {
          B.t = 0;
          if (L.drones.length < 4) {
            const a = L.rng() * Math.PI * 2;
            L.drones.push({ x: B.x + Math.cos(a) * 50, y: B.y + Math.sin(a) * 50, hp: BAL.droneHp, t: 1, sx: B.x + Math.cos(a) * 50, sy: B.y + Math.sin(a) * 50, ang: a });
            this.spawnParticles(B.x, B.y, "#ff9100", 14, 100);
            this.audio.playSfx("alert", { vol: 0.4 });
          }
          ring(phase === 2 ? 10 : 6, 120, B.ang);
        }
        // slow drift toward player
        const [dx, dy] = aim();
        B.x += dx * 26 * wdt; B.y += dy * 26 * wdt;
        touchDmg(38, 28);
        break;
      }
      case "leviathan": {
        // head steers toward player continuously
        const [dx, dy] = aim();
        const sp = phase === 2 ? 150 : 116;
        B.vx = lerp(B.vx || 0, dx * sp, wdt * 1.4);
        B.vy = lerp(B.vy || 0, dy * sp, wdt * 1.4);
        B.x += B.vx * wdt; B.y += B.vy * wdt;
        B.x = clamp(B.x, TILE * 1.6, L.w * TILE - TILE * 1.6);
        B.y = clamp(B.y, TILE * 1.6, L.h * TILE - TILE * 1.6);
        // segments follow
        let px2 = B.x, py2 = B.y;
        for (const s of B.segs) {
          const d = Math.max(1, Math.hypot(px2 - s.x, py2 - s.y));
          if (d > 20) { s.x += (px2 - s.x) / d * (d - 20); s.y += (py2 - s.y) / d * (d - 20); }
          px2 = s.x; py2 = s.y;
          if (p.cloakT <= 0 && dist2(s.x, s.y, p.x, p.y) < (TILE * 0.55) ** 2) this.hurtPlayer(16, s.x, s.y);
        }
        touchDmg(30, 30);
        break;
      }
      case "omega": {
        B.spokes = phase === 2 ? 4 : 3;
        B.spokeSpeed = phase === 2 ? 1.1 : 0.7;
        B.ang += wdt * B.spokeSpeed;
        // spoke damage — radial lasers
        const rel = Math.atan2(p.y - B.y, p.x - B.x);
        const rr = Math.hypot(p.x - B.x, p.y - B.y);
        if (rr < TILE * 8 && p.dashT <= 0) {
          for (let i = 0; i < B.spokes; i++) {
            const a = B.ang + i * Math.PI * 2 / B.spokes;
            let diff = Math.abs(((rel - a) % (Math.PI * 2) + Math.PI * 3) % (Math.PI * 2) - Math.PI);
            if (diff < 0.09) this.hurtPlayer(14, B.x, B.y);
          }
        }
        if (B.t > 2.4) { B.t = 0; const [dx, dy] = aim(); shoot(dx, dy, 170); shoot(dx * 0.9 + dy * 0.2, dy * 0.9 - dx * 0.2, 170); }
        touchDmg(40, 26);
        break;
      }
      case "architect": {
        const ph3 = B.hp < B.maxHp * 0.33;
        if (ph3) {
          B.spokes = 3;
          B.ang += wdt * 0.9;
          const rel = Math.atan2(p.y - B.y, p.x - B.x);
          const rr = Math.hypot(p.x - B.x, p.y - B.y);
          if (rr < TILE * 7 && p.dashT <= 0) {
            for (let i = 0; i < 3; i++) {
              const a = B.ang + i * Math.PI * 2 / 3;
              let diff = Math.abs(((rel - a) % (Math.PI * 2) + Math.PI * 3) % (Math.PI * 2) - Math.PI);
              if (diff < 0.08) this.hurtPlayer(14, B.x, B.y);
            }
          }
          if (B.t > 5 && L.drones.length < 3) { B.t = 0; L.drones.push({ x: B.x + 40, y: B.y, hp: BAL.droneHp, t: 1, sx: B.x + 40, sy: B.y, ang: 0 }); }
        } else if (B.hp < B.maxHp * 0.66) {
          if (B.t > 2.4) {
            B.t = 0;
            B.cycle = (B.cycle || 0) + 1;
            if (B.cycle % 3 === 0) { B.invertT = 2; this.audio.playSfx("invert"); this.toast("!! INVERT !!", "#ff4dff"); }
            else { const [dx, dy] = aim(); shoot(dx, dy, 165, true); }
          }
        } else {
          if (B.state === "fight" && B.t > 1.8) { B.state = "telegraph"; B.t = 0; }
          else if (B.state === "telegraph" && B.t > 0.6) {
            B.state = "charge"; B.t = 0;
            const [dx, dy] = aim();
            B.vx = dx * 330; B.vy = dy * 330;
          } else if (B.state === "charge") {
            B.x += B.vx * wdt; B.y += B.vy * wdt;
            const tx = Math.floor(B.x / TILE), ty = Math.floor(B.y / TILE);
            if (this.solidAt(tx, ty)) {
              B.x -= B.vx * wdt; B.y -= B.vy * wdt;
              B.state = "fight"; B.t = 0;
              this.shake(10, 0.4);
              ring(6, 140);
            }
          }
        }
        touchDmg(40, 30);
        break;
      }
    }
  }

  // =================================================================
  // RENDER
  // =================================================================
  render() {
    const ctx = this.ctx, W = innerWidth, H = innerHeight;
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#04040a";
    ctx.fillRect(0, 0, W, H);
    switch (this.screen) {
      case "menu": this.renderMenu(); break;
      case "saves": this.renderSaves(); break;
      case "options": this.renderOptions(); break;
      case "achievements": this.renderAchievements(); break;
      case "credits": this.renderCredits(); break;
      case "cutscene": this.renderCutscene(); break;
      case "play": case "dialog": case "hack": case "gameover":
        this.renderPlay();
        if (this.screen === "dialog") this.renderDialog();
        if (this.screen === "hack") this.renderHack();
        if (this.screen === "gameover") this.renderGameover();
        break;
      case "pause": this.renderPlay(); this.renderPause(); break;
      case "skilltree": this.renderPlay(); this.renderSkilltree(); break;
      case "inventory": this.renderPlay(); this.renderInventory(); break;
      case "quests": this.renderPlay(); this.renderQuests(); break;
      case "endchoice": this.renderEndchoice(); break;
    }
    this.renderToasts();
    if (this.settings.crt) this.renderCRT();
  }

  fontPx(base) { return Math.round(base * this.settings.textScale); }
  text(str, x, y, size, color = "#e0f7ff", align = "left", glow = null) {
    const ctx = this.ctx;
    ctx.font = `bold ${this.fontPx(size)}px 'Courier New', monospace`;
    ctx.textAlign = align;
    if (glow) { ctx.shadowColor = glow; ctx.shadowBlur = 12; }
    ctx.fillStyle = color;
    ctx.fillText(str, x, y);
    ctx.shadowBlur = 0;
    ctx.textAlign = "left";
  }
  wrapText(str, x, y, size, maxW, color, lineH) {
    const ctx = this.ctx;
    ctx.font = `bold ${this.fontPx(size)}px 'Courier New', monospace`;
    const words = String(str).split(" ");
    let line = "", yy = y;
    for (const w of words) {
      if (ctx.measureText(line + w).width > maxW && line) {
        this.text(line, x, yy, size, color);
        line = w + " "; yy += lineH;
      } else line += w + " ";
    }
    this.text(line, x, yy, size, color);
    return yy + lineH;
  }
  drawBackdropFit(bd) {
    const ctx = this.ctx, W = innerWidth, H = innerHeight;
    const s = Math.max(W / bd.width, H / bd.height);
    const dw = bd.width * s, dh = bd.height * s;
    ctx.drawImage(bd, (W - dw) / 2, (H - dh) / 2, dw, dh);
  }

  menuList(items, cx, startY, rowH, selIdx) {
    this._menuRects = [];
    items.forEach((label, i) => {
      const y = startY + i * rowH;
      const w = 340, x = cx - w / 2;
      this._menuRects.push([x, y - rowH * 0.65, w, rowH * 0.9]);
      if (i === selIdx) {
        this.ctx.fillStyle = "rgba(0,229,255,0.12)";
        this.ctx.fillRect(x, y - rowH * 0.65, w, rowH * 0.9);
        this.text("▶", x + 8, y, 16, "#00e5ff");
      }
      this.text(label, cx, y, 17, i === selIdx ? "#ffffff" : "#9ad8ff", "center", i === selIdx ? "#00e5ff" : null);
    });
  }

  renderMenu() {
    const W = innerWidth, H = innerHeight;
    this.drawBackdropFit(this.optImages.title || this.menuBackdrop);
    this.ctx.fillStyle = "rgba(2,2,10,0.45)";
    this.ctx.fillRect(0, 0, W, H);
    const t = this.t;
    this.text(t("menu.title"), W / 2, H * 0.2, 44, "#00e5ff", "center", "#00e5ff");
    this.text(t("menu.subtitle"), W / 2, H * 0.2 + this.fontPx(40), 30, "#ff4dff", "center", "#ff4dff");
    this.text(t("menu.tagline"), W / 2, H * 0.2 + this.fontPx(72), 13, "#9ad8ff", "center");
    const hasAuto = !!this.slotInfo("auto");
    const items = ["menu.newgame", "menu.continue", "menu.saves", "menu.options", "menu.achievements", "menu.credits"]
      .map((k, i) => i === 1 && !hasAuto ? t(k) + " —" : t(k));
    this.menuList(items, W / 2, H * 0.44, this.fontPx(34), this.menuIdx);
    this.text("v1.0 — WASD/←→ · ENTER", W / 2, H - 18, 11, "#546e7a", "center");
  }

  renderSaves() {
    const W = innerWidth, H = innerHeight, t = this.t;
    this.drawBackdropFit(this.menuBackdrop);
    this.ctx.fillStyle = "rgba(2,2,10,0.72)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("menu.saves") + (this.savesMode === "save" ? " · " + t("menu.save") : ""), W / 2, H * 0.14, 26, "#00e5ff", "center", "#00e5ff");
    const slots = ["auto", 0, 1, 2];
    const labels = slots.map((s, i) => {
      const info = this.slotInfo(s);
      const name = s === "auto" ? t("menu.autosave") : `${t("menu.slot")} ${s + 1}`;
      if (!info) return `${name}: ${t("menu.empty")}`;
      const mins = Math.floor(info.playtime / 60);
      return `${name}: ${t("menu.chapter")} ${info.chapter} · ${mins}min`;
    });
    labels.push(t("menu.back"));
    this.menuList(labels, W / 2, H * 0.3, this.fontPx(40), this.menuIdx);
    this.text("X/DEL = " + t("menu.delete"), W / 2, H - 24, 12, "#546e7a", "center");
  }

  renderOptions() {
    const W = innerWidth, H = innerHeight, t = this.t, s = this.settings;
    this.drawBackdropFit(this.menuBackdrop);
    this.ctx.fillStyle = "rgba(2,2,10,0.78)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("opt.title"), W / 2, H * 0.1, 26, "#00e5ff", "center", "#00e5ff");
    const bar = (v) => "▮".repeat(Math.round(v * 10)) + "▯".repeat(10 - Math.round(v * 10));
    const onoff = (v) => v ? t("opt.on") : t("opt.off");
    const bindActs = Object.keys(DEFAULT_BINDS);
    const rows = [
      `${t("opt.music")}  ${bar(s.music)}`,
      `${t("opt.sfx")}  ${bar(s.sfx)}`,
      `${t("opt.crt")}  ${onoff(s.crt)}`,
      `${t("opt.shake")}  ${onoff(s.shake)}`,
      `${t("opt.flash")}  ${onoff(s.flash)}`,
      `${t("opt.textsize")}  ${s.textScale.toFixed(1)}`,
      `${t("opt.lang")}  ${s.lang.toUpperCase()}`
    ];
    for (const a of bindActs) {
      const key = this.rebinding === a ? t("opt.pressKey") : (s.binds[a] && s.binds[a][0]) || "—";
      rows.push(`${t("act." + a)}  [${key}]`);
    }
    rows.push(t("opt.resetBinds"));
    rows.push(t("menu.back"));
    const rowH = Math.min(this.fontPx(24), (H * 0.78) / rows.length);
    this._menuRects = [];
    const startY = H * 0.16;
    // scroll if long
    const visible = Math.floor((H * 0.8) / rowH);
    const first = clamp(this.menuIdx - Math.floor(visible / 2), 0, Math.max(0, rows.length - visible));
    for (let i = first; i < Math.min(rows.length, first + visible); i++) {
      const y = startY + (i - first) * rowH;
      const x = W / 2 - 240, w = 480;
      this._menuRects[i] = [x, y - rowH * 0.7, w, rowH * 0.9];
      if (i === this.menuIdx) {
        this.ctx.fillStyle = "rgba(0,229,255,0.12)";
        this.ctx.fillRect(x, y - rowH * 0.7, w, rowH * 0.9);
      }
      this.text(rows[i], W / 2, y, 14, i === this.menuIdx ? "#fff" : "#9ad8ff", "center");
    }
  }

  renderAchievements() {
    const W = innerWidth, H = innerHeight, t = this.t;
    this.drawBackdropFit(this.menuBackdrop);
    this.ctx.fillStyle = "rgba(2,2,10,0.8)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("ach.title"), W / 2, H * 0.1, 26, "#ffc400", "center", "#ffc400");
    const cols = W > 700 ? 2 : 1;
    const cw = Math.min(430, W / cols - 20);
    ACH_IDS.forEach((id, i) => {
      const col = i % cols, row = Math.floor(i / cols);
      const x = W / 2 + (col - cols / 2) * cw + 10, y = H * 0.18 + row * this.fontPx(44);
      const got = !!this.ach[id];
      this.text((got ? "★ " : "☆ ") + t("ach." + id + ".name"), x, y, 15, got ? "#ffc400" : "#607d8b");
      this.text(t("ach." + id + ".desc"), x + 18, y + this.fontPx(16), 11, got ? "#cfd8dc" : "#455a64");
    });
    this.text(t("menu.back") + " [ENTER]", W / 2, H - 24, 13, "#9ad8ff", "center");
  }

  renderCredits() {
    const W = innerWidth, H = innerHeight;
    this.drawBackdropFit(this.creditsAfterEnding ? this.getBackdrop(6, "merge") : this.menuBackdrop);
    this.ctx.fillStyle = "rgba(2,2,10,0.7)";
    this.ctx.fillRect(0, 0, W, H);
    const lines = this.t("credits.lines");
    lines.forEach((ln, i) => {
      const y = H - this.creditsY + i * this.fontPx(30);
      if (y > -40 && y < H + 40) this.text(ln, W / 2, y, i === 0 ? 24 : 15, i === 0 ? "#00e5ff" : "#e0f7ff", "center", i === 0 ? "#00e5ff" : null);
    });
    if (this.creditsY > lines.length * this.fontPx(30) + H) this.creditsY = 0;
  }

  renderCutscene() {
    const cs = this.cutscene, W = innerWidth, H = innerHeight;
    const bd = cs.mode === "chapter" ? this.getBackdrop(cs.chapter) : this.getBackdrop(cs.chapter, cs.mode);
    this.drawBackdropFit(bd);
    // letterbox
    this.ctx.fillStyle = "rgba(0,0,0,0.85)";
    this.ctx.fillRect(0, 0, W, H * 0.12);
    this.ctx.fillRect(0, H * 0.78, W, H * 0.22);
    if (cs.mode === "chapter" && cs.idx === 0) {
      this.text(`${this.t("ch.label")} ${cs.chapter}`, W / 2, H * 0.08, 15, "#9ad8ff", "center");
    }
    const cur = cs.beats[cs.idx] || "";
    const shown = cur.slice(0, Math.floor(cs.chars));
    this.wrapText(shown, W * 0.12, H * 0.84, 16, W * 0.76, "#e0f7ff", this.fontPx(22));
    this.text("ENTER ▸", W - 30, H - 16, 12, "#546e7a", "right");
  }

  // ---- world ----
  renderPlay() {
    const ctx = this.ctx, L = this.level, p = this.player;
    if (!L) return;
    const W = innerWidth, H = innerHeight;
    let ox = Math.round(W / 2 - this.camX), oy = Math.round(H / 2 - this.camY);
    if (this.shakeT > 0) {
      ox += (Math.random() - 0.5) * this.shakeMag * 2;
      oy += (Math.random() - 0.5) * this.shakeMag * 2;
    }
    ctx.save();
    ctx.translate(ox, oy);
    // static layer
    ctx.drawImage(this.staticLayer, 0, 0);
    // dynamic tiles
    for (let y = 0; y < L.h; y++) for (let x = 0; x < L.w; x++) {
      const c = L.grid[y][x];
      if (c === "D") ctx.drawImage(this.tiles.door, x * TILE, y * TILE);
      else if (c === "H") ctx.drawImage(this.tiles.hdoor, x * TILE, y * TILE);
      else if (c === "S") ctx.drawImage(this.tiles.switch, x * TILE, y * TILE);
      else if (c === "h") ctx.drawImage(this.tiles.terminal, x * TILE, y * TILE);
      else if (c === "Q") ctx.drawImage(this.items.relay, x * TILE + 1, y * TILE + 1);
      else if (c === "C") ctx.drawImage(this.tiles.checkpoint, x * TILE, y * TILE);
      else if ("1234".includes(c)) ctx.drawImage(this.tiles.portal, x * TILE, y * TILE);
      else if (c === "X") ctx.drawImage(L.exitOpen || L.arena ? this.tiles.exitOpen : this.tiles.exitClosed, x * TILE, y * TILE);
    }
    // lasers
    for (const la of L.lasers) {
      if (la.on) {
        ctx.fillStyle = "rgba(255,23,68,0.85)";
        ctx.fillRect(la.x * TILE + 12, la.y * TILE, 8, TILE);
        ctx.fillRect(la.x * TILE, la.y * TILE + 12, TILE, 8);
      } else if (la.warn) {
        ctx.fillStyle = "rgba(255,23,68,0.25)";
        ctx.fillRect(la.x * TILE + 13, la.y * TILE, 6, TILE);
        ctx.fillRect(la.x * TILE, la.y * TILE + 13, TILE, 6);
      }
    }
    for (const la of L.sLasers) {
      if (L.switchOn) {
        ctx.fillStyle = "rgba(255,234,0,0.75)";
        ctx.fillRect(la.x * TILE + 12, la.y * TILE, 8, TILE);
        ctx.fillRect(la.x * TILE, la.y * TILE + 12, TILE, 8);
      }
    }
    // pickups
    for (const pk of L.pickups) {
      const spr = this.items[pk.kind === "kit" ? "kit" : pk.kind];
      const bob = Math.sin(L.time * 3 + pk.ph) * 3;
      ctx.drawImage(spr, pk.x - spr.width / 2, pk.y - spr.height / 2 + bob);
    }
    if (L.coin) ctx.drawImage(this.items.coin, L.coin.x - 13, L.coin.y - 13 + Math.sin(L.time * 3) * 3);
    for (const e of L.echoes) ctx.drawImage(this.items.echo, e.x - 14, e.y - 14 + Math.sin(L.time * 2 + e.ph) * 4);
    for (const bl of L.blossoms) ctx.drawImage(this.items.blossom, bl.x - 15, bl.y - 15);
    if (L.zz7) ctx.drawImage(this.items.zz7, L.zz7.x - 22, L.zz7.y - 26);
    // mines
    for (const m of L.mines) ctx.drawImage(this.sprMine, m.x - 12, m.y - 12);
    // npc
    if (L.npc) {
      ctx.drawImage(this.sprNpc, L.npc.x - 22, L.npc.y - 26 + Math.sin(L.time * 2) * 2);
    }
    // drones
    for (const d of L.drones) ctx.drawImage(this.sprDrone, d.x - 18, d.y - 18);
    // hunters
    for (const hu of L.hunters) {
      ctx.save();
      if (hu.stun > 0) ctx.globalAlpha = 0.5 + Math.sin(L.time * 20) * 0.2;
      ctx.drawImage(this.sprHunters[hu.type], hu.x - 24, hu.y - 26);
      ctx.restore();
      if (hu.state === "chase") {
        ctx.fillStyle = "#ff1744";
        ctx.font = "bold 16px monospace";
        ctx.fillText("!", hu.x - 3, hu.y - 30);
      }
    }
    // boss
    if (L.boss && L.boss.state !== "dead") {
      const B = L.boss;
      if (B.type === "leviathan") for (let i = B.segs.length - 1; i >= 0; i--) {
        const s = B.segs[i];
        ctx.drawImage(this.sprSegment, s.x - 22, s.y - 22);
      }
      ctx.save();
      if (B.state === "telegraph") ctx.globalAlpha = 0.6 + Math.sin(L.time * 30) * 0.4;
      if (B.stun > 0 || B.state === "stunned") ctx.globalAlpha = 0.6;
      ctx.drawImage(this.sprBosses[B.type], B.x - 48, B.y - 48);
      ctx.restore();
      // omega/architect spokes
      if ((B.type === "omega" || (B.type === "architect" && B.hp < B.maxHp * 0.33)) && B.spokes) {
        ctx.strokeStyle = "rgba(64,196,255,0.8)";
        ctx.lineWidth = 5;
        const len = TILE * (B.type === "omega" ? 8 : 7);
        for (let i = 0; i < B.spokes; i++) {
          const a = B.ang + i * Math.PI * 2 / B.spokes;
          ctx.beginPath();
          ctx.moveTo(B.x + Math.cos(a) * 40, B.y + Math.sin(a) * 40);
          ctx.lineTo(B.x + Math.cos(a) * len, B.y + Math.sin(a) * len);
          ctx.stroke();
        }
      }
    }
    // bolts
    for (const b of L.bolts) ctx.drawImage(this.items.bolt, b.x - 7, b.y - 7);
    for (const b of L.ebolts) ctx.drawImage(this.items.ebolt, b.x - 7, b.y - 7);
    // player
    ctx.save();
    if (p.cloakT > 0) ctx.globalAlpha = 0.35;
    if (p.invuln > 0 && p.hitFlash <= 0) ctx.globalAlpha = 0.55 + Math.sin(L.time * 25) * 0.25;
    const bob = (Math.abs(Math.sin(p.anim)) * 2);
    ctx.drawImage(this.sprHero, p.x - 24, p.y - 28 - bob);
    ctx.restore();
    if (p.shieldT > 0) {
      ctx.strokeStyle = "rgba(64,196,255,0.7)";
      ctx.lineWidth = 2.5;
      ctx.beginPath(); ctx.arc(p.x, p.y - 4, 24 + Math.sin(L.time * 8) * 2, 0, 7); ctx.stroke();
    }
    if (p.dashT > 0) this.spawnParticles(p.x, p.y, "#7df9ff", 2, 20);
    // particles
    for (const pa of L.particles) {
      ctx.globalAlpha = clamp(pa.t * 2, 0, 1);
      ctx.fillStyle = pa.color;
      ctx.fillRect(pa.x - 2, pa.y - 2, 4, 4);
    }
    ctx.globalAlpha = 1;
    ctx.restore();

    // fog / haze overlay
    const g = ctx.createRadialGradient(W / 2, H / 2, H * 0.25, W / 2, H / 2, H * 0.85);
    g.addColorStop(0, "rgba(0,0,0,0)");
    g.addColorStop(1, "rgba(2,2,14,0.55)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, W, H);
    // slow-mo tint
    if (p.slowT > 0 && this.settings.flash) {
      ctx.fillStyle = "rgba(64,196,255,0.08)";
      ctx.fillRect(0, 0, W, H);
    }
    if (p.hitFlash > 0 && this.settings.flash) {
      ctx.fillStyle = `rgba(255,23,68,${p.hitFlash * 0.45})`;
      ctx.fillRect(0, 0, W, H);
    }
    if (L.boss && L.boss.invertT > 0) {
      ctx.fillStyle = "rgba(255,77,255,0.08)";
      ctx.fillRect(0, 0, W, H);
    }
    this.renderHUD();
    this.renderTouchUI();
  }

  renderHUD() {
    const ctx = this.ctx, L = this.level, p = this.player, run = this.run, t = this.t;
    const W = innerWidth, H = innerHeight;
    // hp / energy
    const bw = Math.min(220, W * 0.3);
    ctx.fillStyle = "rgba(0,0,0,0.5)";
    ctx.fillRect(12, 12, bw + 4, 40);
    ctx.fillStyle = "#3d0a14";
    ctx.fillRect(14, 14, bw, 14);
    ctx.fillStyle = "#ff1744";
    ctx.fillRect(14, 14, bw * clamp(run.hp / BAL.playerHp, 0, 1), 14);
    ctx.fillStyle = "#0a2a3d";
    ctx.fillRect(14, 32, bw, 12);
    ctx.fillStyle = "#00e5ff";
    ctx.fillRect(14, 32, bw * clamp(run.energy / BAL.playerEnergy, 0, 1), 12);
    // level / xp
    this.text(`${t("hud.lvl")} ${run.level}  ${t("hud.sp")} ${run.sp}`, 14, 66, 12, "#ffc400");
    const xpw = bw;
    ctx.fillStyle = "#26210a";
    ctx.fillRect(14, 72, xpw, 5);
    ctx.fillStyle = "#ffc400";
    ctx.fillRect(14, 72, xpw * clamp(run.xp / XP_NEXT(run.level), 0, 1), 5);
    // fragments / keys top-right
    const fragStr = `◆ ${L.fragsHere}/${L.quota}  (${run.fragTotal})`;
    this.text(fragStr, W - 14, 26, 15, "#ffc400", "right", "#ffc400");
    if (run.keys > 0) this.text(`⚿ ${run.keys}`, W - 14, 48, 14, "#ffd740", "right");
    // alert
    if (L.alert > 0.02) {
      const aw = Math.min(180, W * 0.24);
      ctx.fillStyle = "rgba(0,0,0,0.5)";
      ctx.fillRect(W / 2 - aw / 2 - 2, 10, aw + 4, 16);
      ctx.fillStyle = "#33060d";
      ctx.fillRect(W / 2 - aw / 2, 12, aw, 12);
      ctx.fillStyle = L.alert > 0.66 ? "#ff1744" : "#ff9100";
      ctx.fillRect(W / 2 - aw / 2, 12, aw * L.alert, 12);
      this.text(t("hud.alert"), W / 2, 22, 9, "#ffccd2", "center");
    }
    // boss hp
    if (L.boss && L.boss.state !== "dead" && L.boss.state !== "intro") {
      const bbw = Math.min(420, W * 0.6);
      ctx.fillStyle = "rgba(0,0,0,0.55)";
      ctx.fillRect(W / 2 - bbw / 2 - 3, H - 66, bbw + 6, 26);
      ctx.fillStyle = "#33060d";
      ctx.fillRect(W / 2 - bbw / 2, H - 63, bbw, 12);
      ctx.fillStyle = "#ff1744";
      ctx.fillRect(W / 2 - bbw / 2, H - 63, bbw * clamp(L.boss.hp / L.boss.maxHp, 0, 1), 12);
      this.text(t("boss." + L.boss.type + ".name"), W / 2, H - 47, 11, "#ffccd2", "center");
    }
    // quest tracker
    const ch = this.chapterDef();
    let qy = H - 20;
    if (ch.quest) {
      const q = run.quests[ch.quest.id];
      if (q && q.state !== "done") {
        const prog = ch.quest.count > 1 ? ` ${Math.min(q.n, ch.quest.count)}/${ch.quest.count}` : q.state === "ready" ? " ✓" : "";
        this.text(`◇ ${t("quest." + ch.quest.id + ".name")}${prog}`, 14, qy, 11, "#b388ff");
        qy -= this.fontPx(16);
      }
    }
    this.text(`● ${t("quest.main.ch" + run.chapter)}`, 14, qy, 11, "#9ad8ff");
    // ability bar
    const abs = ABILITY_ORDER.filter(a => run.abilities[a]);
    const size = 34, pad = 6;
    let ax = W - 14 - abs.length * (size + pad);
    const cds = {
      dash: p.dashCd / BAL.dash.cd, emp: p.empCd / BAL.emp.cd, cloak: p.cloakCd / BAL.cloak.cd,
      slow: p.slowCd / BAL.slow.cd, teleport: p.tpCd / BAL.teleport.cd, shield: p.shieldCd / BAL.shield.cd,
      hack: 0, magnet: 0
    };
    for (const a of abs) {
      ctx.fillStyle = "rgba(0,0,0,0.55)";
      ctx.fillRect(ax, H - 90, size, size);
      ctx.strokeStyle = a === "magnet" && !p.magnetOn ? "#455a64" : "#00e5ff";
      ctx.strokeRect(ax + 0.5, H - 90 + 0.5, size, size);
      this.text(ABILITY_KEYS[a], ax + size / 2, H - 90 + size / 2 + 5, 13, "#e0f7ff", "center");
      const cd = cds[a] || 0;
      if (cd > 0) {
        ctx.fillStyle = "rgba(0,0,0,0.7)";
        ctx.fillRect(ax, H - 90, size, size * clamp(cd, 0, 1));
      }
      ax += size + pad;
    }
    // interact hint
    if (this.interactHint) this.text(this.interactHint, W / 2, H * 0.62, 14, "#7df9ff", "center", "#00e5ff");
    // minimap
    const mmScale = Math.min(2.6, 90 / L.h);
    const mw = L.w * mmScale, mh = L.h * mmScale;
    const mx = W - mw - 12, my = 60;
    ctx.globalAlpha = 0.75;
    ctx.fillStyle = "#04040c";
    ctx.fillRect(mx - 2, my - 2, mw + 4, mh + 4);
    ctx.fillStyle = "#1a2550";
    for (let y = 0; y < L.h; y++) for (let x = 0; x < L.w; x++) {
      if (L.grid[y][x] !== "#" && L.grid[y][x] !== "%") ctx.fillRect(mx + x * mmScale, my + y * mmScale, mmScale, mmScale);
    }
    if (L.exit) {
      ctx.fillStyle = L.exitOpen ? "#00e676" : "#546e7a";
      ctx.fillRect(mx + L.exit.x * mmScale - 1, my + L.exit.y * mmScale - 1, mmScale + 2, mmScale + 2);
    }
    ctx.fillStyle = "#00e5ff";
    ctx.fillRect(mx + p.x / TILE * mmScale - 1.5, my + p.y / TILE * mmScale - 1.5, 3, 3);
    ctx.fillStyle = "#ff1744";
    for (const hu of L.hunters) ctx.fillRect(mx + hu.x / TILE * mmScale - 1, my + hu.y / TILE * mmScale - 1, 2.5, 2.5);
    ctx.globalAlpha = 1;
  }

  // ---- touch UI ----
  setupTouch() {
    const el = this.canvas;
    const btns = () => this.touchButtons || [];
    el.addEventListener("touchstart", (e) => {
      e.preventDefault();
      this.audio.init();
      for (const tc of e.changedTouches) {
        const x = tc.clientX, y = tc.clientY;
        // menus: tap = click
        if (this.screen !== "play") {
          this.input.mouse.x = x; this.input.mouse.y = y;
          this.input.mouse.clicked = true;
          this._tapConfirm2 = true;
          // also treat as confirm for cutscene/dialog screens
          if (["cutscene", "dialog", "gameover", "hack"].includes(this.screen)) this._tapConfirm = true;
          continue;
        }
        let hit = false;
        for (const b of btns()) {
          if (dist2(x, y, b.x, b.y) < b.r * b.r) {
            this.input.held.add(b.act); this.input.pressed.add(b.act);
            this.input.touch.buttons.add(tc.identifier + ":" + b.act);
            hit = true;
            break;
          }
        }
        if (!hit && x < innerWidth * 0.45) {
          this.input.touch.stick = { id: tc.identifier, ox: x, oy: y };
        }
      }
    }, { passive: false });
    el.addEventListener("touchmove", (e) => {
      e.preventDefault();
      for (const tc of e.changedTouches) {
        const st = this.input.touch.stick;
        if (st && tc.identifier === st.id) {
          const dx = tc.clientX - st.ox, dy = tc.clientY - st.oy;
          const m = Math.hypot(dx, dy);
          const dead = 10, max = 52;
          if (m > dead) {
            const k = Math.min(1, (m - dead) / max);
            this.input.touch.vec = [dx / m * k, dy / m * k];
          } else this.input.touch.vec = [0, 0];
        }
      }
    }, { passive: false });
    const endTouch = (e) => {
      e.preventDefault();
      for (const tc of e.changedTouches) {
        const st = this.input.touch.stick;
        if (st && tc.identifier === st.id) {
          this.input.touch.stick = null;
          this.input.touch.vec = [0, 0];
        }
        for (const key of [...this.input.touch.buttons]) {
          if (key.startsWith(tc.identifier + ":")) {
            this.input.held.delete(key.split(":")[1]);
            this.input.touch.buttons.delete(key);
          }
        }
      }
    };
    el.addEventListener("touchend", endTouch, { passive: false });
    el.addEventListener("touchcancel", endTouch, { passive: false });
  }

  renderTouchUI() {
    if (!("ontouchstart" in window)) { this.touchButtons = []; return; }
    const ctx = this.ctx, W = innerWidth, H = innerHeight, run = this.run, p = this.player;
    const btns = [];
    const add = (x, y, r, act, label, active = true) => { btns.push({ x, y, r, act, label, active }); };
    add(W - 60, H - 70, 34, "pulse", "◉");
    if (run.abilities.dash) add(W - 130, H - 46, 27, "dash", "»");
    add(W - 130, H - 118, 24, "interact", "E");
    const small = [];
    if (run.abilities.emp) small.push(["emp", "Q"]);
    if (run.abilities.shield) small.push(["shield", "R"]);
    if (run.abilities.cloak) small.push(["cloak", "C"]);
    if (run.abilities.slow) small.push(["slow", "F"]);
    if (run.abilities.teleport) small.push(["teleport", "T"]);
    small.forEach(([act, label], i) => add(W - 44 - i * 48, H - 168, 20, act, label));
    add(W - 30, 26, 20, "pause", "▐▌");
    this.touchButtons = btns;
    for (const b of btns) {
      ctx.globalAlpha = 0.4;
      ctx.fillStyle = "#04101c";
      ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, 7); ctx.fill();
      ctx.strokeStyle = "#00e5ff";
      ctx.stroke();
      ctx.globalAlpha = 0.85;
      this.text(b.label, b.x, b.y + 5, 14, "#7df9ff", "center");
      ctx.globalAlpha = 1;
    }
    // stick
    const st = this.input.touch.stick;
    if (st) {
      ctx.globalAlpha = 0.35;
      ctx.strokeStyle = "#00e5ff";
      ctx.beginPath(); ctx.arc(st.ox, st.oy, 44, 0, 7); ctx.stroke();
      ctx.fillStyle = "#00e5ff";
      ctx.beginPath(); ctx.arc(st.ox + this.input.touch.vec[0] * 40, st.oy + this.input.touch.vec[1] * 40, 16, 0, 7); ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  // ---- overlays ----
  panel(x, y, w, h, border = "#00e5ff") {
    const ctx = this.ctx;
    ctx.fillStyle = "rgba(3,6,18,0.92)";
    ctx.fillRect(x, y, w, h);
    ctx.strokeStyle = border;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(x + 0.5, y + 0.5, w, h);
  }

  renderDialog() {
    const d = this.dialog;
    if (!d) return;
    const W = innerWidth, H = innerHeight;
    const cur = d.lines[d.idx];
    if (!cur) return;
    const ph = Math.min(170, H * 0.3);
    this.panel(W * 0.06, H - ph - 16, W * 0.88, ph);
    this.ctx.drawImage(this.sprNpc, W * 0.06 + 12, H - ph - 6, 44, 44);
    this.text(cur.speaker, W * 0.06 + 66, H - ph + 16, 14, "#00e5ff", "left", "#00e5ff");
    this.wrapText(cur.text.slice(0, Math.floor(d.chars)), W * 0.06 + 20, H - ph + 44, 14, W * 0.82, "#e0f7ff", this.fontPx(20));
    this.text("[E] ▸", W * 0.9, H - 30, 12, "#546e7a", "right");
  }

  renderHack() {
    const h = this.hackState;
    if (!h) return;
    const W = innerWidth, H = innerHeight, t = this.t;
    const pw = Math.min(440, W * 0.9), phh = 180;
    const x = W / 2 - pw / 2, y = H / 2 - phh / 2;
    this.panel(x, y, pw, phh, "#7c4dff");
    this.text(t("hack.title"), W / 2, y + 30, 18, "#b388ff", "center", "#7c4dff");
    this.text(t("hack.desc"), W / 2, y + 54, 11, "#9ad8ff", "center");
    const arrows = { up: "▲", down: "▼", left: "◀", right: "▶" };
    const cw = 44;
    let ax = W / 2 - h.seq.length * cw / 2 + cw / 2;
    h.seq.forEach((dir, i) => {
      const done = i < h.idx;
      this.text(arrows[dir], ax, y + 105, 26, done ? "#00e676" : i === h.idx ? "#ffffff" : "#546e7a", "center", done ? "#00e676" : null);
      ax += cw;
    });
    // timer bar
    this.ctx.fillStyle = "#26210a";
    this.ctx.fillRect(x + 20, y + phh - 28, pw - 40, 8);
    this.ctx.fillStyle = h.time < 2 ? "#ff1744" : "#ffc400";
    this.ctx.fillRect(x + 20, y + phh - 28, (pw - 40) * clamp(h.time / 6.5, 0, 1), 8);
  }

  renderPause() {
    const W = innerWidth, H = innerHeight, t = this.t;
    this.ctx.fillStyle = "rgba(2,2,10,0.72)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("pause.title"), W / 2, H * 0.18, 28, "#00e5ff", "center", "#00e5ff");
    const items = ["pause.resume", "pause.skills", "pause.inventory", "pause.quests", "menu.saves", "pause.options", "pause.tomenu"].map(k => t(k));
    this.menuList(items, W / 2, H * 0.3, this.fontPx(36), this.menuIdx);
    const mins = Math.floor(this.run.playtime / 60), secs = Math.floor(this.run.playtime % 60);
    this.text(`${t("menu.chapter")} ${this.run.chapter} · ${t("playtime")} ${mins}:${String(secs).padStart(2, "0")}`, W / 2, H - 30, 12, "#546e7a", "center");
  }

  renderSkilltree() {
    const W = innerWidth, H = innerHeight, t = this.t, run = this.run;
    this.ctx.fillStyle = "rgba(2,2,10,0.85)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("sk.title"), W / 2, H * 0.1, 24, "#00e5ff", "center", "#00e5ff");
    this.text(`${t("sk.points")}: ${run.sp}`, W / 2, H * 0.15, 15, "#ffc400", "center");
    const branches = [["ghost", "#7df9ff"], ["surge", "#ff9100"], ["chrono", "#b388ff"]];
    const colW = Math.min(260, W / 3.2);
    branches.forEach(([br, color], c) => {
      const bx = W / 2 + (c - 1) * colW;
      this.text(t("sk.branch." + br), bx, H * 0.22, 14, color, "center", color);
      SKILLS[br].forEach((id, r) => {
        const y = H * 0.27 + r * this.fontPx(64);
        const idx = c * 4 + r;
        const owned = !!run.skills[id];
        const prereq = r === 0 || run.skills[SKILLS[br][r - 1]];
        const sel = this.skIdx === idx;
        const boxW = colW - 24;
        this.ctx.fillStyle = sel ? "rgba(0,229,255,0.14)" : "rgba(255,255,255,0.03)";
        this.ctx.fillRect(bx - boxW / 2, y - 14, boxW, this.fontPx(52));
        this.ctx.strokeStyle = owned ? color : prereq ? "#546e7a" : "#263238";
        this.ctx.strokeRect(bx - boxW / 2 + 0.5, y - 13.5, boxW, this.fontPx(52));
        this.text((owned ? "● " : "○ ") + t("sk." + id + ".name"), bx, y + 4, 13, owned ? color : prereq ? "#cfd8dc" : "#455a64", "center");
        this.text(t("sk." + id + ".desc"), bx, y + this.fontPx(22), 10, owned ? "#e0f7ff" : "#607d8b", "center");
      });
    });
    this.text("[K] " + t("menu.back"), W / 2, H - 24, 12, "#546e7a", "center");
  }

  renderInventory() {
    const W = innerWidth, H = innerHeight, t = this.t, run = this.run;
    this.ctx.fillStyle = "rgba(2,2,10,0.85)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("inv.title"), W / 2, H * 0.12, 24, "#00e5ff", "center", "#00e5ff");
    this.text(`⚿ ${t("inv.keys")}: ${run.keys}    ⚡ ${t("inv.cells")}: ${run.cells}`, W / 2, H * 0.2, 15, "#ffd740", "center");
    if (run.cells > 0) this.text(t("inv.useCell"), W / 2, H * 0.25, 12, "#00e676", "center");
    this.text(t("inv.lore") + ` (${run.lore.length})`, W / 2, H * 0.32, 14, "#ffc400", "center");
    if (!run.lore.length) this.text(t("inv.empty"), W / 2, H * 0.38, 12, "#607d8b", "center");
    const start = this.invScroll || 0;
    run.lore.slice(start, start + 6).forEach((key, i) => {
      const [ch, idx] = key.split(":").map(Number);
      const pool = this.t("frag.ch" + ch);
      this.wrapText(pool[idx] || key, W * 0.12, H * 0.38 + i * this.fontPx(42), 11, W * 0.76, "#cfd8dc", this.fontPx(15));
    });
    this.text("[I] " + t("menu.back"), W / 2, H - 24, 12, "#546e7a", "center");
  }

  renderQuests() {
    const W = innerWidth, H = innerHeight, t = this.t, run = this.run;
    this.ctx.fillStyle = "rgba(2,2,10,0.85)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("q.title"), W / 2, H * 0.12, 24, "#00e5ff", "center", "#00e5ff");
    this.text(t("q.main"), W * 0.12, H * 0.22, 14, "#9ad8ff", "left", "#00e5ff");
    this.wrapText(t("quest.main.ch" + run.chapter), W * 0.12, H * 0.27, 13, W * 0.76, "#e0f7ff", this.fontPx(18));
    let y = H * 0.36;
    for (let c = 1; c <= 5; c++) {
      const q = run.quests["ch" + c];
      if (!q || q.state === "inactive") continue;
      const def = CHAPTERS[c - 1].quest;
      const status = q.state === "done" ? t("q.done") : `${Math.min(q.n, def.count)}/${def.count}`;
      this.text(`${t("q.side")}: ${t("quest.ch" + c + ".name")} — ${status}`, W * 0.12, y, 12, q.state === "done" ? "#00e676" : "#b388ff");
      y = this.wrapText(t("quest.ch" + c + ".desc"), W * 0.14, y + this.fontPx(16), 11, W * 0.72, "#90a4ae", this.fontPx(15));
      y += this.fontPx(8);
    }
    this.text("[J] " + t("menu.back"), W / 2, H - 24, 12, "#546e7a", "center");
  }

  renderGameover() {
    const W = innerWidth, H = innerHeight, t = this.t;
    this.ctx.fillStyle = "rgba(20,0,6,0.8)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("gameover.title"), W / 2, H * 0.3, 32, "#ff1744", "center", "#ff1744");
    this.text(t("gameover.sub"), W / 2, H * 0.38, 13, "#ff8a80", "center");
    this.menuList([t("gameover.respawn"), t("gameover.tomenu")], W / 2, H * 0.52, this.fontPx(38), this.menuIdx);
  }

  renderEndchoice() {
    const W = innerWidth, H = innerHeight, t = this.t;
    this.drawBackdropFit(this.getBackdrop(6));
    this.ctx.fillStyle = "rgba(2,2,10,0.75)";
    this.ctx.fillRect(0, 0, W, H);
    this.text(t("ending.choose"), W / 2, H * 0.16, 28, "#ffffff", "center", "#e0e0ff");
    const mergeOk = this.run.fragTotal >= Math.ceil(TOTAL_FRAGS * 0.75);
    const opts = [
      ["ending.opt.delete", "ending.opt.delete.desc", "#ff1744", true],
      ["ending.opt.save", "ending.opt.save.desc", "#00e676", true],
      ["ending.opt.merge", "ending.opt.merge.desc", "#ffffff", mergeOk]
    ];
    const cw = Math.min(280, W / 3.4), chh = Math.min(240, H * 0.42);
    this._menuRects = [];
    opts.forEach(([nameK, descK, color, ok], i) => {
      const x = W / 2 + (i - 1) * (cw + 16) - cw / 2, y = H * 0.3;
      this._menuRects.push([x, y, cw, chh]);
      this.ctx.fillStyle = this.endIdx === i ? "rgba(255,255,255,0.1)" : "rgba(3,6,18,0.8)";
      this.ctx.fillRect(x, y, cw, chh);
      this.ctx.strokeStyle = this.endIdx === i ? color : "#37474f";
      this.ctx.lineWidth = this.endIdx === i ? 2.5 : 1;
      this.ctx.strokeRect(x, y, cw, chh);
      this.text(t(nameK), x + cw / 2, y + 44, 15, ok ? color : "#455a64", "center", this.endIdx === i && ok ? color : null);
      this.wrapText(t(descK), x + 18, y + 80, 12, cw - 36, ok ? "#cfd8dc" : "#455a64", this.fontPx(17));
      if (!ok) this.wrapText(t("ending.merge.locked"), x + 18, y + chh - 58, 10, cw - 36, "#ff8a80", this.fontPx(14));
    });
    this.text(`◆ ${this.run.fragTotal}/${TOTAL_FRAGS}`, W / 2, H * 0.85, 14, "#ffc400", "center");
    if (this.menuIdx < 3 && this._tapConfirm2) { this.endIdx = this.menuIdx; this._tapConfirm2 = false; }
  }

  renderToasts() {
    const W = innerWidth, H = innerHeight;
    this.toasts.forEach((tt, i) => {
      const alpha = clamp(tt.t, 0, 1);
      this.ctx.globalAlpha = alpha;
      const y = H * 0.12 + i * this.fontPx(40);
      this.ctx.font = `bold ${this.fontPx(13)}px 'Courier New', monospace`;
      const w = Math.min(this.ctx.measureText(tt.text).width + 30, W * 0.9);
      this.ctx.fillStyle = "rgba(3,6,18,0.85)";
      this.ctx.fillRect(W / 2 - w / 2, y - this.fontPx(16), w, this.fontPx(24));
      this.ctx.strokeStyle = tt.color;
      this.ctx.strokeRect(W / 2 - w / 2 + 0.5, y - this.fontPx(16) + 0.5, w, this.fontPx(24));
      // clip long texts
      const max = Math.floor((w - 20) / (this.fontPx(13) * 0.6));
      const shown = tt.text.length > max ? tt.text.slice(0, max - 1) + "…" : tt.text;
      this.text(shown, W / 2, y, 13, tt.color, "center");
      this.ctx.globalAlpha = 1;
    });
  }

  renderCRT() {
    const ctx = this.ctx, W = innerWidth, H = innerHeight;
    ctx.globalAlpha = 0.5;
    const pat = ctx.createPattern(this.scan, "repeat");
    ctx.fillStyle = pat;
    ctx.fillRect(0, 0, W, H);
    ctx.globalAlpha = 1;
    const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, Math.max(W, H) * 0.75);
    vg.addColorStop(0, "rgba(0,0,0,0)");
    vg.addColorStop(1, "rgba(0,0,0,0.4)");
    ctx.fillStyle = vg;
    ctx.fillRect(0, 0, W, H);
  }
}
