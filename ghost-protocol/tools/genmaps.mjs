// Deterministic maze generator for Ghost Protocol: Neon Maze.
// Produces public/levels.js with guaranteed-traversable maps (recursive backtracker
// + loops + rooms), specials placed on reachable floor, then self-validates.
// Run: node tools/genmaps.mjs
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];

function genMaze(cw, ch, rng, loopFrac, rooms) {
  const w = cw * 2 + 1, h = ch * 2 + 1;
  const g = Array.from({ length: h }, () => new Array(w).fill("#"));
  // backtracker on cell grid
  const visited = Array.from({ length: ch }, () => new Array(cw).fill(false));
  const stack = [[0, 0]];
  visited[0][0] = true;
  g[1][1] = ".";
  while (stack.length) {
    const [cx, cy] = stack[stack.length - 1];
    const opts = [];
    for (const [dx, dy] of DIRS) {
      const nx = cx + dx, ny = cy + dy;
      if (nx >= 0 && ny >= 0 && nx < cw && ny < ch && !visited[ny][nx]) opts.push([dx, dy]);
    }
    if (!opts.length) { stack.pop(); continue; }
    const [dx, dy] = opts[Math.floor(rng() * opts.length)];
    const nx = cx + dx, ny = cy + dy;
    visited[ny][nx] = true;
    g[cy * 2 + 1 + dy][cx * 2 + 1 + dx] = ".";
    g[ny * 2 + 1][nx * 2 + 1] = ".";
    stack.push([nx, ny]);
  }
  // loops: open a fraction of interior walls that separate two floors
  const cand = [];
  for (let y = 1; y < h - 1; y++) for (let x = 1; x < w - 1; x++) {
    if (g[y][x] !== "#") continue;
    if (g[y][x - 1] === "." && g[y][x + 1] === ".") cand.push([x, y]);
    else if (g[y - 1][x] === "." && g[y + 1][x] === ".") cand.push([x, y]);
  }
  for (let i = cand.length - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [cand[i], cand[j]] = [cand[j], cand[i]]; }
  for (let i = 0; i < Math.floor(cand.length * loopFrac); i++) g[cand[i][1]][cand[i][0]] = ".";
  // rooms
  for (let r = 0; r < rooms; r++) {
    const rw = 3 + 2 * Math.floor(rng() * 2), rh = 3;
    const rx = 1 + 2 * Math.floor(rng() * ((w - rw - 2) / 2));
    const ry = 1 + 2 * Math.floor(rng() * ((h - rh - 2) / 2));
    for (let y = ry; y < ry + rh; y++) for (let x = rx; x < rx + rw; x++) g[y][x] = ".";
  }
  return g;
}

function pad(g, rings) {
  const w = g[0].length + rings * 2;
  const out = [];
  for (let i = 0; i < rings; i++) out.push(new Array(w).fill("#"));
  for (const row of g) out.push(new Array(rings).fill("#").concat(row, new Array(rings).fill("#")));
  for (let i = 0; i < rings; i++) out.push(new Array(w).fill("#"));
  return out;
}

function bfs(g, sx, sy, blocked) {
  const h = g.length, w = g[0].length;
  const dist = Array.from({ length: h }, () => new Array(w).fill(-1));
  const q = [[sx, sy]]; dist[sy][sx] = 0;
  for (let i = 0; i < q.length; i++) {
    const [x, y] = q[i];
    for (const [dx, dy] of DIRS) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
      if (dist[ny][nx] >= 0) continue;
      const c = g[ny][nx];
      if (c === "#" || blocked.includes(c)) continue;
      dist[ny][nx] = dist[y][x] + 1;
      q.push([nx, ny]);
    }
  }
  return dist;
}

function floors(g) {
  const out = [];
  for (let y = 0; y < g.length; y++) for (let x = 0; x < g[0].length; x++) if (g[y][x] === ".") out.push([x, y]);
  return out;
}

function isDeadEnd(g, x, y) {
  let n = 0;
  for (const [dx, dy] of DIRS) if (g[y + dy]?.[x + dx] !== "#" && g[y + dy]?.[x + dx] !== undefined) n++;
  return n === 1;
}

function isCorridor(g, x, y) {
  const lr = g[y][x - 1] !== "#" && g[y][x + 1] !== "#" && g[y - 1][x] === "#" && g[y + 1][x] === "#";
  const ud = g[y - 1][x] !== "#" && g[y + 1][x] !== "#" && g[y][x - 1] === "#" && g[y][x + 1] === "#";
  return lr || ud;
}

// Build one maze map with placements. Returns grid strings or null if constraints fail.
let lastFail = "";
function buildMap(spec, seed) {
  const rng = mulberry32(seed);
  const g = pad(genMaze(spec.cw, spec.ch, rng, spec.loops, spec.rooms), 2);
  const h = g.length, w = g[0].length;
  const put = (x, y, c) => { g[y][x] = c; };
  // P near top-left: first floor
  let P = null;
  outer: for (let y = 1; y < h; y++) for (let x = 1; x < w; x++) if (g[y][x] === ".") { P = [x, y]; break outer; }
  const dist = bfs(g, P[0], P[1], []);
  const fl = floors(g).filter(([x, y]) => dist[y][x] >= 0 && !(x === P[0] && y === P[1]));
  if (fl.length < 60) { lastFail='floors'; return null; }
  const maxD = Math.max(...fl.map(([x, y]) => dist[y][x]));
  const at = (frac) => fl.filter(([x, y]) => Math.abs(dist[y][x] - maxD * frac) <= maxD * 0.12);
  const taken = new Set([P.join(",")]);
  const takeFrom = (arr, pred) => {
    const c = arr.filter(([x, y]) => !taken.has(x + "," + y) && (!pred || pred(x, y)));
    if (!c.length) return null;
    const p = c[Math.floor(rng() * c.length)];
    taken.add(p.join(","));
    return p;
  };
  // exit: farthest dead end (for door pocket) or farthest tile
  let X = null;
  const deadFar = fl.filter(([x, y]) => dist[y][x] > maxD * 0.75 && isDeadEnd(g, x, y) && !taken.has(x + "," + y));
  if (spec.door && deadFar.length) {
    X = deadFar[Math.floor(rng() * deadFar.length)];
  } else {
    let best = fl[0];
    for (const p of fl) if (dist[p[1]][p[0]] > dist[best[1]][best[0]]) best = p;
    X = best;
  }
  taken.add(X.join(","));
  if (spec.door && isDeadEnd(g, X[0], X[1])) {
    for (const [dx, dy] of DIRS) {
      const nx = X[0] + dx, ny = X[1] + dy;
      if (g[ny]?.[nx] === ".") { put(nx, ny, "D"); taken.add(nx + "," + ny); break; }
    }
  }
  // key reachable without door
  if (spec.door) {
    const dNoDoor = bfs(g, P[0], P[1], ["D"]);
    const kc = fl.filter(([x, y]) => dNoDoor[y][x] > maxD * 0.4 && !taken.has(x + "," + y));
    if (!kc.length) { lastFail='key'; return null; }
    const K = kc[Math.floor(rng() * kc.length)];
    put(K[0], K[1], "K"); taken.add(K.join(","));
  }
  // hack door gating a bonus pocket (chapters with hack)
  if (spec.hackPockets) {
    let placed = 0;
    for (const [x, y] of fl) {
      if (placed >= spec.hackPockets) break;
      if (taken.has(x + "," + y) || !isDeadEnd(g, x, y) || dist[y][x] < 6) continue;
      for (const [dx, dy] of DIRS) {
        if (g[y + dy]?.[x + dx] === ".") {
          put(x + dx, y + dy, "H"); taken.add((x + dx) + "," + (y + dy));
          put(x, y, "A"); taken.add(x + "," + y);
          placed++;
          break;
        }
      }
    }
  }
  // secret pocket behind '%' — carve into a solid wall band (padding ring or thick wall)
  let secretDone = false;
  for (const [x, y] of fl) {
    if (secretDone) break;
    if (taken.has(x + "," + y)) continue;
    for (const [dx, dy] of DIRS) {
      const wx = x + dx, wy = y + dy, bx = x + dx * 2, by = y + dy * 2;
      if (g[wy]?.[wx] !== "#" || g[by]?.[bx] !== "#") continue;
      if (bx <= 0 || by <= 0 || bx >= w - 1 || by >= h - 1) continue;
      // pocket must stay sealed except for the mouth
      let sealed = true;
      for (const [ex, ey] of DIRS) {
        const nx = bx + ex, ny = by + ey;
        if (nx === wx && ny === wy) continue;
        if (g[ny]?.[nx] !== "#") { sealed = false; break; }
      }
      if (!sealed) continue;
      put(wx, wy, "%");
      put(bx, by, spec.secretReward || "F");
      taken.add(wx + "," + wy); taken.add(bx + "," + by);
      secretDone = true;
      break;
    }
  }
  if (!secretDone && spec.secretReward === "Q") { lastFail='secret'; return null; } // ch1 coin must exist
  // checkpoint mid-way on a corridor-ish tile
  const C = takeFrom(at(0.5)) || takeFrom(fl);
  put(C[0], C[1], "C");
  // NPC in mid-early zone
  if (spec.npc) { const Np = takeFrom(at(0.3)); if (!Np) { lastFail='npc'; return null; } put(Np[0], Np[1], "N"); }
  // fragments spread across distance bands
  const bands = [0.2, 0.35, 0.5, 0.65, 0.8];
  let fPlaced = 0;
  for (let i = 0; i < spec.frags; i++) {
    const p = takeFrom(at(bands[i % bands.length])) || takeFrom(fl);
    if (!p) { lastFail='frag'; return null; }
    put(p[0], p[1], "F"); fPlaced++;
  }
  // quest targets
  for (let i = 0; i < (spec.quests || 0); i++) {
    const p = takeFrom(at(0.3 + 0.5 * (i / Math.max(1, spec.quests - 1) || 0))) || takeFrom(fl);
    if (!p) { lastFail='quest'; return null; }
    put(p[0], p[1], "Q");
  }
  // hunters far from P
  for (let i = 0; i < spec.hunters.length; i++) {
    const p = takeFrom(fl, (x, y) => dist[y][x] > maxD * 0.45);
    if (!p) { lastFail='hunter'; return null; }
    put(p[0], p[1], "E");
  }
  // drones
  for (let i = 0; i < (spec.drones || 0); i++) {
    const p = takeFrom(fl, (x, y) => dist[y][x] > maxD * 0.25);
    if (!p) return null;
    put(p[0], p[1], "e");
  }
  // timed lasers on corridors
  for (let i = 0; i < (spec.lasers || 0); i++) {
    const p = takeFrom(fl, (x, y) => isCorridor(g, x, y) && dist[y][x] > maxD * 0.3);
    if (p) put(p[0], p[1], "L");
  }
  // switched laser group: S + 2 l
  if (spec.switchGroup) {
    const S = takeFrom(at(0.45));
    if (S) {
      put(S[0], S[1], "S");
      for (let i = 0; i < 2; i++) {
        const p = takeFrom(fl, (x, y) => isCorridor(g, x, y) && dist[y][x] > maxD * 0.55);
        if (p) put(p[0], p[1], "l");
      }
    }
  }
  // portals
  if (spec.portals >= 1) {
    const a = takeFrom(at(0.25)), b = takeFrom(at(0.85));
    if (a && b) { put(a[0], a[1], "1"); put(b[0], b[1], "2"); }
  }
  if (spec.portals >= 2) {
    const a = takeFrom(at(0.4)), b = takeFrom(at(0.7));
    if (a && b) { put(a[0], a[1], "3"); put(b[0], b[1], "4"); }
  }
  // pickups
  for (let i = 0; i < (spec.cells || 1); i++) { const p = takeFrom(fl); if (p) put(p[0], p[1], "A"); }
  for (let i = 0; i < (spec.kits || 1); i++) { const p = takeFrom(fl); if (p) put(p[0], p[1], "+"); }
  // lore terminal
  if (spec.lore) { const p = takeFrom(at(0.6)); if (p) put(p[0], p[1], "h"); }
  put(P[0], P[1], "P");
  put(X[0], X[1], "X");
  return { grid: g.map(r => r.join("")), quota: Math.max(1, fPlaced - 1) };
}

function validate(gridRows, { arena } = {}) {
  const g = gridRows;
  const w = g[0].length, h = g.length;
  for (const r of g) if (r.length !== w) return "row width";
  for (let x = 0; x < w; x++) if (g[0][x] !== "#" || g[h - 1][x] !== "#") return "border";
  for (let y = 0; y < h; y++) if (g[y][0] !== "#" || g[y][w - 1] !== "#") return "border";
  let P = null, counts = {};
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const c = g[y][x];
    counts[c] = (counts[c] || 0) + 1;
    if (c === "P") P = [x, y];
  }
  if (!P || counts["P"] !== 1) return "P count";
  if (!arena && !counts["X"]) return "no X";
  if (arena && !counts["B"]) return "no B";
  for (const [a, b] of [["1", "2"], ["3", "4"]]) {
    if ((counts[a] || 0) !== (counts[b] || 0)) return "portal pair";
  }
  // full reachability (doors/secrets passable)
  const seen = Array.from({ length: h }, () => new Array(w).fill(false));
  const st = [P]; seen[P[1]][P[0]] = true;
  const portals = {};
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if ("1234".includes(g[y][x])) portals[g[y][x]] = [x, y];
  const pairs = { "1": "2", "2": "1", "3": "4", "4": "3" };
  while (st.length) {
    const [x, y] = st.pop();
    const c = g[y][x];
    if (pairs[c] && portals[pairs[c]]) {
      const [tx, ty] = portals[pairs[c]];
      if (!seen[ty][tx]) { seen[ty][tx] = true; st.push([tx, ty]); }
    }
    for (const [dx, dy] of DIRS) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= w || ny >= h || seen[ny][nx] || g[ny][nx] === "#") continue;
      seen[ny][nx] = true; st.push([nx, ny]);
    }
  }
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (g[y][x] !== "#" && !seen[y][x]) return `unreachable ${g[y][x]} at ${x},${y}`;
  }
  // key before door
  if (counts["D"]) {
    if (!counts["K"] || counts["K"] < counts["D"]) return "keys < doors";
    const seen2 = Array.from({ length: h }, () => new Array(w).fill(false));
    const st2 = [P]; seen2[P[1]][P[0]] = true;
    while (st2.length) {
      const [x, y] = st2.pop();
      const c = g[y][x];
      if (pairs[c] && portals[pairs[c]]) {
        const [tx, ty] = portals[pairs[c]];
        if (!seen2[ty][tx]) { seen2[ty][tx] = true; st2.push([tx, ty]); }
      }
      for (const [dx, dy] of DIRS) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= w || ny >= h || seen2[ny][nx]) continue;
        const cc = g[ny][nx];
        if (cc === "#" || cc === "D") continue;
        seen2[ny][nx] = true; st2.push([nx, ny]);
      }
    }
    let kOk = false;
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) if (g[y][x] === "K" && seen2[y][x]) kOk = true;
    if (!kOk) return "key behind door";
  }
  return null;
}

function buildArena(w, h, boss, extras) {
  const g = Array.from({ length: h }, (_, y) => Array.from({ length: w }, (_, x) =>
    (x === 0 || y === 0 || x === w - 1 || y === h - 1) ? "#" : "."));
  // symmetric pillars
  for (const [px, py] of [[3, 2], [w - 4, 2], [3, h - 3], [w - 4, h - 3]]) { g[py][px] = "#"; g[py][px + (px < w / 2 ? 1 : -1)] = "#"; }
  g[3][Math.floor(w / 2)] = "B";
  g[h - 3][Math.floor(w / 2)] = "P";
  g[h - 3][2] = "A";
  g[h - 3][w - 3] = "+";
  if (extras === "hack") { g[Math.floor(h / 2)][2] = "h"; g[Math.floor(h / 2)][w - 3] = "h"; }
  return g.map(r => r.join(""));
}

const CH_META = [
  { id: 1, nameKey: "ch.1.name", accent: "#00e5ff", tint: "#0a1230", newAbilities: ["dash"], boss: "guardian", npc: "echo", quest: { id: "ch1", type: "fetch", count: 1 } },
  { id: 2, nameKey: "ch.2.name", accent: "#7c4dff", tint: "#120a30", newAbilities: ["hack"], boss: "hacker", npc: "byte", quest: { id: "ch2", type: "use", count: 3 } },
  { id: 3, nameKey: "ch.3.name", accent: "#ff9100", tint: "#1a1005", newAbilities: ["emp", "shield"], boss: "queen", npc: "pixel", quest: { id: "ch3", type: "reach", count: 1 } },
  { id: 4, nameKey: "ch.4.name", accent: "#76ff03", tint: "#08170a", newAbilities: ["cloak", "magnet"], boss: "leviathan", npc: "root", quest: { id: "ch4", type: "destroy", count: 5 } },
  { id: 5, nameKey: "ch.5.name", accent: "#40c4ff", tint: "#050d1f", newAbilities: ["slow", "teleport"], boss: "omega", npc: "iris", quest: { id: "ch5", type: "touch", count: 3 } },
  { id: 6, nameKey: "ch.6.name", accent: "#e0e0ff", tint: "#14061f", newAbilities: [], boss: "architect", npc: null, quest: null }
];

// per-map generation specs
const SPECS = {
  1: [
    { cw: 12, ch: 8, loops: 0.12, rooms: 2, frags: 3, hunters: ["blaze"], drones: 0, lasers: 0, npc: true, secretReward: "Q", quests: 0, cells: 1, kits: 1, lore: true },
    { cw: 13, ch: 9, loops: 0.12, rooms: 2, frags: 4, hunters: ["blaze", "widow"], drones: 1, lasers: 0, quests: 0, cells: 1, kits: 1 }
  ],
  2: [
    { cw: 13, ch: 9, loops: 0.14, rooms: 2, frags: 3, hunters: ["phantom"], drones: 1, lasers: 1, npc: true, quests: 2, hackPockets: 1, cells: 1, kits: 1, lore: true },
    { cw: 14, ch: 10, loops: 0.14, rooms: 2, frags: 4, hunters: ["phantom", "blaze"], drones: 1, lasers: 1, quests: 1, door: true, hackPockets: 1, cells: 1, kits: 1 }
  ],
  3: [
    { cw: 14, ch: 10, loops: 0.15, rooms: 3, frags: 3, hunters: ["widow", "blaze"], drones: 2, lasers: 2, npc: true, quests: 0, hackPockets: 1, cells: 1, kits: 1, lore: true },
    { cw: 14, ch: 10, loops: 0.15, rooms: 2, frags: 4, hunters: ["widow", "phantom"], drones: 2, lasers: 2, quests: 1, switchGroup: true, door: true, cells: 2, kits: 1 }
  ],
  4: [
    { cw: 14, ch: 10, loops: 0.16, rooms: 3, frags: 3, hunters: ["glitch", "widow"], drones: 1, lasers: 1, npc: true, quests: 3, cells: 1, kits: 1, lore: true },
    { cw: 15, ch: 10, loops: 0.16, rooms: 2, frags: 4, hunters: ["glitch", "phantom"], drones: 2, lasers: 2, quests: 2, portals: 1, door: true, cells: 1, kits: 2 }
  ],
  5: [
    { cw: 15, ch: 10, loops: 0.16, rooms: 3, frags: 3, hunters: ["blaze", "phantom", "glitch"], drones: 1, lasers: 2, npc: true, quests: 2, cells: 1, kits: 1, lore: true },
    { cw: 15, ch: 11, loops: 0.16, rooms: 2, frags: 4, hunters: ["widow", "phantom", "blaze"], drones: 2, lasers: 2, quests: 1, portals: 1, switchGroup: true, cells: 2, kits: 1 }
  ],
  6: [
    { cw: 15, ch: 11, loops: 0.18, rooms: 3, frags: 4, hunters: ["blaze", "phantom", "widow", "glitch"], drones: 2, lasers: 2, quests: 0, cells: 2, kits: 2, lore: true },
    { cw: 15, ch: 11, loops: 0.18, rooms: 2, frags: 4, hunters: ["blaze", "phantom", "widow", "glitch"], drones: 2, lasers: 2, quests: 0, portals: 2, door: true, cells: 2, kits: 2 }
  ]
};
const ARENAS = {
  guardian: buildArena(24, 12, "guardian"),
  hacker: buildArena(24, 12, "hacker", "hack"),
  queen: buildArena(26, 12, "queen"),
  leviathan: buildArena(28, 13, "leviathan"),
  omega: buildArena(26, 13, "omega"),
  architect: buildArena(30, 14, "architect")
};

const chapters = [];
for (const meta of CH_META) {
  const maps = [];
  SPECS[meta.id].forEach((spec, mi) => {
    let built = null, usedSeed = -1;
    for (let seed = meta.id * 1000 + mi * 100 + 1; seed < meta.id * 1000 + mi * 100 + 90; seed++) {
      const b = buildMap({ ...spec, npc: !!spec.npc && !!meta.npc }, seed);
      if (!b) { if (process.env.DEBUG) console.log(`  seed ${seed}: build fail ${lastFail}`); continue; }
      const err = validate(b.grid, {});
      if (err) { if (process.env.DEBUG) console.log(`  seed ${seed}: validate fail ${err}`); continue; }
      built = b; usedSeed = seed; break;
    }
    if (!built) { console.error(`FAILED ch${meta.id} map${mi}`); process.exit(1); }
    console.log(`ch${meta.id} map${mi}: seed ${usedSeed}, ${built.grid[0].length}x${built.grid.length}, quota ${built.quota}`);
    maps.push({ quota: built.quota, hunters: spec.hunters, grid: built.grid });
  });
  const arena = ARENAS[meta.boss];
  const aerr = validate(arena, { arena: true });
  if (aerr) { console.error(`arena ${meta.boss}: ${aerr}`); process.exit(1); }
  maps.push({ arena: true, boss: meta.boss, hunters: [], grid: arena });
  chapters.push({ ...meta, maps });
}

const header = `// Ghost Protocol: Neon Maze — chapters, mazes and boss arenas.
// GENERATED by tools/genmaps.mjs (deterministic seeds) — regenerate instead of editing grids.
// Map legend:
//  #  wall            .  floor           P  player start
//  F  memory fragment K  data key        D  locked door (key)
//  H  hackable door   h  lore terminal   Q  quest object (chapter-specific)
//  L  timed laser     l  switched laser  S  switch (toggles l)
//  1/2, 3/4 portal pairs                 N  npc              C  checkpoint
//  E  hunter spawn    e  drone spawn     X  exit
//  %  secret wall (walkable, hidden)     A  energy cell      +  repair kit
//  B  boss spawn
`;
const body = "export const CHAPTERS = " + JSON.stringify(chapters, null, 1) + ";\n\n" +
  `export const QUEST_TARGET = { 1: "coin", 2: "relay", 3: "zz7", 4: "blossom", 5: "echo" };\n`;
const out = join(dirname(fileURLToPath(import.meta.url)), "..", "public", "levels.js");
writeFileSync(out, header + body);
console.log("written", out);
