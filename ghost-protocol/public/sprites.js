// Ghost Protocol: Neon Maze — procedural sprite factory.
// STYLE FORMULA (embedded): chunky HD pixel art rendering with glowing neon bloom,
// sharp geometric silhouettes with thin luminous outlines, environment in deep
// midnight-blue and violet circuit-board tones with charcoal shadows, hero in radiant
// cyan-white that pops against the surroundings, hunters and hazards in hot magenta
// and crimson glow, memory fragments and pickups in bright golden-amber light, dark
// synthwave cyberpunk atmosphere with volumetric neon haze, high contrast between
// game elements and backgrounds, clean readable silhouettes, consistent top-down
// perspective across all assets.
// Every sprite below is pre-rendered once to an offscreen canvas (bloom baked in),
// so the frame loop only blits — no shadowBlur at runtime.

export const TILE = 32;

function C(w, h) {
  const c = document.createElement("canvas");
  c.width = w; c.height = h;
  return c;
}

function px(ctx, x, y, w, h, color) {
  ctx.fillStyle = color;
  ctx.fillRect(Math.round(x), Math.round(y), Math.round(w), Math.round(h));
}

function withGlow(size, color, blur, draw) {
  const c = C(size, size);
  const ctx = c.getContext("2d");
  ctx.save();
  ctx.shadowColor = color;
  ctx.shadowBlur = blur;
  draw(ctx);
  ctx.restore();
  return c;
}

// chunky rounded capsule silhouette used by the hero and NPCs
function capsule(ctx, x, y, w, h, color) {
  ctx.fillStyle = color;
  const r = w / 2;
  ctx.beginPath();
  ctx.moveTo(x, y + r);
  ctx.arc(x + r, y + r, r, Math.PI, 0);
  ctx.lineTo(x + w, y + h - 2);
  ctx.lineTo(x, y + h - 2);
  ctx.closePath();
  ctx.fill();
}

export function makeHero() {
  // 48px canvas, drawn ~26px body — radiant cyan-white
  const s = 48;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  ctx.shadowColor = "#00e5ff";
  ctx.shadowBlur = 10;
  capsule(ctx, 14, 10, 20, 30, "#d8ffff");
  ctx.shadowBlur = 0;
  capsule(ctx, 16, 12, 16, 26, "#7df9ff");
  // visor
  px(ctx, 18, 18, 12, 5, "#03252e");
  px(ctx, 19, 19, 5, 2, "#ffffff");
  // core light
  px(ctx, 22, 28, 4, 6, "#ffffff");
  // thin luminous outline
  ctx.strokeStyle = "#aefcff";
  ctx.lineWidth = 1;
  ctx.strokeRect(14.5, 10.5, 19, 28);
  return c;
}

const HUNTER_COLORS = {
  blaze: ["#ff1744", "#ff8a80", "#4a0410"],
  phantom: ["#b388ff", "#e8dcff", "#1d0b3d"],
  widow: ["#ff00aa", "#ff8ad8", "#3d0028"],
  glitch: ["#ff4dff", "#ffb3ff", "#2e0630"]
};

export function makeHunter(type) {
  const [main, hi, dark] = HUNTER_COLORS[type];
  const s = 48;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  ctx.shadowColor = main;
  ctx.shadowBlur = 12;
  // classic arcade-ghost body, sharp geometric skirt
  ctx.fillStyle = main;
  ctx.beginPath();
  ctx.moveTo(12, 40);
  ctx.lineTo(12, 22);
  ctx.arc(24, 22, 12, Math.PI, 0);
  ctx.lineTo(36, 40);
  for (let i = 0; i < 4; i++) ctx.lineTo(36 - (i + 0.5) * 6, 40 - (i % 2 ? 0 : 5));
  ctx.closePath();
  ctx.fill();
  ctx.shadowBlur = 0;
  // per-personality crest
  ctx.fillStyle = hi;
  if (type === "blaze") { // flame crest
    ctx.beginPath(); ctx.moveTo(20, 12); ctx.lineTo(24, 2); ctx.lineTo(28, 12); ctx.closePath(); ctx.fill();
  } else if (type === "phantom") { // hollow split
    px(ctx, 22, 12, 4, 26, dark);
  } else if (type === "widow") { // side legs
    px(ctx, 6, 24, 6, 3, hi); px(ctx, 36, 24, 6, 3, hi);
    px(ctx, 8, 30, 4, 3, hi); px(ctx, 36, 30, 4, 3, hi);
  } else if (type === "glitch") { // sliced offset
    const slice = ctx.getImageData(0, 26, s, 5);
    ctx.putImageData(slice, 4, 26);
  }
  // eyes
  px(ctx, 17, 18, 6, 7, "#ffffff"); px(ctx, 27, 18, 6, 7, "#ffffff");
  px(ctx, 19, 21, 3, 4, dark); px(ctx, 29, 21, 3, 4, dark);
  return c;
}

export function makeDrone() {
  const s = 36;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  ctx.shadowColor = "#ff1744";
  ctx.shadowBlur = 8;
  ctx.fillStyle = "#8a0f2d";
  ctx.beginPath();
  ctx.moveTo(18, 4); ctx.lineTo(32, 18); ctx.lineTo(18, 32); ctx.lineTo(4, 18);
  ctx.closePath(); ctx.fill();
  ctx.shadowBlur = 0;
  px(ctx, 14, 14, 8, 8, "#ff1744");
  px(ctx, 16, 16, 4, 4, "#ffd0d8");
  return c;
}

export function makeMine() {
  const s = 24;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  ctx.shadowColor = "#ff00aa";
  ctx.shadowBlur = 8;
  ctx.fillStyle = "#530136";
  ctx.beginPath(); ctx.arc(12, 12, 7, 0, 7); ctx.fill();
  ctx.shadowBlur = 0;
  px(ctx, 10, 10, 4, 4, "#ff00aa");
  return c;
}

export function makeNpc(hueShift = 0) {
  const s = 44;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  const col = `hsl(${170 + hueShift}, 90%, 65%)`;
  ctx.shadowColor = col;
  ctx.shadowBlur = 9;
  capsule(ctx, 13, 10, 18, 28, col);
  ctx.shadowBlur = 0;
  px(ctx, 16, 17, 12, 4, "#04262b");
  px(ctx, 17, 18, 4, 2, "#eaffff");
  // antenna
  px(ctx, 21, 4, 2, 7, col);
  return c;
}

export function makeBoss(type) {
  const s = 96;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  const G = (col, blur, fn) => { ctx.save(); ctx.shadowColor = col; ctx.shadowBlur = blur; fn(); ctx.restore(); };
  if (type === "guardian") {
    G("#ff1744", 18, () => {
      ctx.fillStyle = "#5c0d18";
      ctx.fillRect(18, 18, 60, 60);
    });
    ctx.strokeStyle = "#ff5a70"; ctx.lineWidth = 3; ctx.strokeRect(18.5, 18.5, 59, 59);
    px(ctx, 30, 38, 14, 10, "#ffe1e6"); px(ctx, 52, 38, 14, 10, "#ffe1e6");
    px(ctx, 34, 41, 6, 5, "#20020a"); px(ctx, 56, 41, 6, 5, "#20020a");
    px(ctx, 28, 60, 40, 6, "#ff1744");
  } else if (type === "hacker") {
    G("#7c4dff", 18, () => {
      ctx.fillStyle = "#241145";
      ctx.beginPath();
      ctx.moveTo(48, 8); ctx.lineTo(86, 48); ctx.lineTo(48, 88); ctx.lineTo(10, 48);
      ctx.closePath(); ctx.fill();
    });
    ctx.strokeStyle = "#b388ff"; ctx.lineWidth = 2;
    for (let i = 0; i < 3; i++) { ctx.strokeRect(30 + i * 4, 30 + i * 4, 36 - i * 8, 36 - i * 8); }
    px(ctx, 40, 44, 16, 8, "#e8dcff");
  } else if (type === "queen") {
    G("#ff9100", 18, () => {
      ctx.fillStyle = "#4d2a00";
      ctx.beginPath(); ctx.arc(48, 52, 32, 0, 7); ctx.fill();
    });
    // crown
    ctx.fillStyle = "#ffb300";
    ctx.beginPath();
    ctx.moveTo(20, 30); ctx.lineTo(28, 10); ctx.lineTo(38, 26); ctx.lineTo(48, 6);
    ctx.lineTo(58, 26); ctx.lineTo(68, 10); ctx.lineTo(76, 30); ctx.closePath(); ctx.fill();
    px(ctx, 32, 46, 10, 10, "#ffe0b2"); px(ctx, 54, 46, 10, 10, "#ffe0b2");
    px(ctx, 35, 49, 4, 5, "#1f1002"); px(ctx, 57, 49, 4, 5, "#1f1002");
  } else if (type === "leviathan") { // head sprite; segments drawn separately
    G("#76ff03", 16, () => {
      ctx.fillStyle = "#1d3b03";
      ctx.beginPath(); ctx.arc(48, 48, 30, 0, 7); ctx.fill();
    });
    ctx.fillStyle = "#76ff03";
    ctx.beginPath(); ctx.moveTo(24, 34); ctx.lineTo(40, 44); ctx.lineTo(24, 50); ctx.closePath(); ctx.fill();
    ctx.beginPath(); ctx.moveTo(72, 34); ctx.lineTo(56, 44); ctx.lineTo(72, 50); ctx.closePath(); ctx.fill();
    px(ctx, 34, 58, 28, 6, "#b9ff70");
  } else if (type === "omega") {
    G("#40c4ff", 20, () => {
      ctx.fillStyle = "#062b40";
      ctx.beginPath(); ctx.arc(48, 48, 34, 0, 7); ctx.fill();
    });
    ctx.strokeStyle = "#40c4ff"; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(48, 48, 24, 0, 7); ctx.stroke();
    px(ctx, 40, 40, 16, 16, "#d4f4ff");
  } else { // architect
    G("#ffffff", 20, () => {
      ctx.fillStyle = "#2a1745";
      ctx.beginPath();
      ctx.moveTo(48, 6); ctx.lineTo(84, 30); ctx.lineTo(84, 70); ctx.lineTo(48, 92);
      ctx.lineTo(12, 70); ctx.lineTo(12, 30); ctx.closePath(); ctx.fill();
    });
    ctx.strokeStyle = "#e0e0ff"; ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(48, 6); ctx.lineTo(48, 92); ctx.moveTo(12, 30); ctx.lineTo(84, 70); ctx.moveTo(84, 30); ctx.lineTo(12, 70);
    ctx.stroke();
    px(ctx, 38, 40, 20, 12, "#ffffff");
  }
  return c;
}

export function makeSegment() { // leviathan body segment
  const s = 44;
  const c = C(s, s);
  const ctx = c.getContext("2d");
  ctx.shadowColor = "#76ff03";
  ctx.shadowBlur = 10;
  ctx.fillStyle = "#254d05";
  ctx.beginPath(); ctx.arc(22, 22, 15, 0, 7); ctx.fill();
  ctx.shadowBlur = 0;
  ctx.strokeStyle = "#76ff03"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(22, 22, 10, 0, 7); ctx.stroke();
  return c;
}

export function makeItems(accent) {
  const items = {};
  items.frag = withGlow(28, "#ffc400", 10, (ctx) => {
    ctx.fillStyle = "#ffc400";
    ctx.beginPath(); ctx.moveTo(14, 3); ctx.lineTo(24, 14); ctx.lineTo(14, 25); ctx.lineTo(4, 14);
    ctx.closePath(); ctx.fill();
    ctx.fillStyle = "#fff3c4"; ctx.fillRect(11, 11, 6, 6);
  });
  items.key = withGlow(26, "#ffd740", 8, (ctx) => {
    ctx.fillStyle = "#ffd740";
    ctx.beginPath(); ctx.arc(9, 13, 5, 0, 7); ctx.fill();
    ctx.fillRect(12, 11, 11, 4);
    ctx.fillRect(19, 15, 3, 4); ctx.fillRect(15, 15, 3, 3);
  });
  items.cell = withGlow(26, "#00e676", 8, (ctx) => {
    ctx.fillStyle = "#00e676"; ctx.fillRect(8, 5, 10, 16);
    ctx.fillStyle = "#b9ffd9"; ctx.fillRect(10, 8, 6, 4);
    ctx.fillRect(11, 3, 4, 3);
  });
  items.kit = withGlow(26, "#ff5252", 8, (ctx) => {
    ctx.fillStyle = "#ff5252";
    ctx.fillRect(11, 5, 4, 16); ctx.fillRect(5, 11, 16, 4);
  });
  items.coin = withGlow(26, "#ffc400", 9, (ctx) => {
    ctx.fillStyle = "#ffc400"; ctx.beginPath(); ctx.arc(13, 13, 9, 0, 7); ctx.fill();
    ctx.fillStyle = "#8a6d00"; ctx.font = "bold 12px monospace"; ctx.fillText("A", 9, 17);
  });
  items.relay = withGlow(30, "#00e676", 9, (ctx) => {
    ctx.fillStyle = "#04331c"; ctx.fillRect(5, 5, 20, 20);
    ctx.strokeStyle = "#00e676"; ctx.lineWidth = 2; ctx.strokeRect(6, 6, 18, 18);
    ctx.fillStyle = "#00e676"; ctx.fillRect(9, 10, 12, 2); ctx.fillRect(9, 14, 12, 2); ctx.fillRect(9, 18, 8, 2);
  });
  items.blossom = withGlow(30, "#d500f9", 10, (ctx) => {
    ctx.fillStyle = "#d500f9";
    for (let i = 0; i < 5; i++) {
      const a = i * Math.PI * 2 / 5 - Math.PI / 2;
      ctx.beginPath(); ctx.arc(15 + Math.cos(a) * 7, 15 + Math.sin(a) * 7, 5, 0, 7); ctx.fill();
    }
    ctx.fillStyle = "#76ff03"; ctx.beginPath(); ctx.arc(15, 15, 4, 0, 7); ctx.fill();
  });
  items.echo = withGlow(28, "#40c4ff", 10, (ctx) => {
    ctx.strokeStyle = "#40c4ff"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(14, 14, 5, 0, 7); ctx.stroke();
    ctx.beginPath(); ctx.arc(14, 14, 9, 0, 7); ctx.stroke();
    ctx.fillStyle = "#d4f4ff"; ctx.fillRect(12, 12, 4, 4);
  });
  items.zz7 = makeNpc(40);
  items.bolt = withGlow(14, "#7df9ff", 6, (ctx) => {
    ctx.fillStyle = "#d8ffff"; ctx.beginPath(); ctx.arc(7, 7, 3.5, 0, 7); ctx.fill();
  });
  items.ebolt = withGlow(14, "#ff1744", 6, (ctx) => {
    ctx.fillStyle = "#ffb3bd"; ctx.beginPath(); ctx.arc(7, 7, 3.5, 0, 7); ctx.fill();
  });
  items.glow = withGlow(24, accent, 9, (ctx) => {
    ctx.fillStyle = accent; ctx.beginPath(); ctx.arc(12, 12, 4, 0, 7); ctx.fill();
  });
  return items;
}

// Per-chapter tileset. Seamless-by-construction: patterns are drawn on the tile
// grid so edges always continue across neighboring tiles.
export function makeTileset(accent, tint, chapterId, rng) {
  const t = {};
  const T = TILE;

  const floor = C(T, T);
  {
    const ctx = floor.getContext("2d");
    ctx.fillStyle = tint;
    ctx.fillRect(0, 0, T, T);
    ctx.fillStyle = "rgba(255,255,255,0.03)";
    ctx.fillRect(0, 0, T, 1); ctx.fillRect(0, 0, 1, T);
    // faint circuit traces, deterministic per chapter
    ctx.strokeStyle = "rgba(124,180,255,0.08)";
    ctx.lineWidth = 1;
    for (let i = 0; i < 3; i++) {
      const x = Math.floor(rng() * (T - 8)) + 4, y = Math.floor(rng() * (T - 8)) + 4;
      ctx.strokeRect(x + 0.5, y + 0.5, 4 + Math.floor(rng() * 6), 2);
    }
  }
  t.floor = floor;

  const wall = C(T, T);
  {
    const ctx = wall.getContext("2d");
    ctx.fillStyle = "#05060f";
    ctx.fillRect(0, 0, T, T);
    ctx.fillStyle = "#101430";
    ctx.fillRect(2, 2, T - 4, T - 4);
    ctx.shadowColor = accent;
    ctx.shadowBlur = 6;
    ctx.strokeStyle = accent;
    ctx.lineWidth = 1.5;
    ctx.strokeRect(2.5, 2.5, T - 5, T - 5);
    ctx.shadowBlur = 0;
    ctx.fillStyle = "rgba(255,255,255,0.06)";
    ctx.fillRect(4, 4, T - 8, 2);
  }
  t.wall = wall;

  t.door = withGlow(T, "#ffd740", 8, (ctx) => {
    ctx.fillStyle = "#241c02"; ctx.fillRect(2, 2, T - 4, T - 4);
    ctx.strokeStyle = "#ffd740"; ctx.lineWidth = 2; ctx.strokeRect(4, 4, T - 8, T - 8);
    ctx.fillStyle = "#ffd740"; ctx.fillRect(T / 2 - 2, 8, 4, T - 16);
  });
  t.hdoor = withGlow(T, "#7c4dff", 8, (ctx) => {
    ctx.fillStyle = "#160a2e"; ctx.fillRect(2, 2, T - 4, T - 4);
    ctx.strokeStyle = "#7c4dff"; ctx.lineWidth = 2; ctx.strokeRect(4, 4, T - 8, T - 8);
    ctx.fillStyle = "#b388ff"; ctx.font = "bold 14px monospace"; ctx.fillText("</>", 4, T / 2 + 5);
  });
  t.exitClosed = withGlow(T, "#607d8b", 5, (ctx) => {
    ctx.fillStyle = "#0d1417"; ctx.fillRect(2, 2, T - 4, T - 4);
    ctx.strokeStyle = "#546e7a"; ctx.lineWidth = 2; ctx.strokeRect(4, 4, T - 8, T - 8);
    ctx.strokeStyle = "#37474f"; ctx.beginPath(); ctx.arc(T / 2, T / 2, 7, 0, 7); ctx.stroke();
  });
  t.exitOpen = withGlow(T, "#00e676", 12, (ctx) => {
    ctx.fillStyle = "#02180c"; ctx.fillRect(2, 2, T - 4, T - 4);
    ctx.strokeStyle = "#00e676"; ctx.lineWidth = 2; ctx.strokeRect(4, 4, T - 8, T - 8);
    ctx.fillStyle = "#00e676"; ctx.beginPath(); ctx.arc(T / 2, T / 2, 6, 0, 7); ctx.fill();
  });
  t.checkpoint = withGlow(T, "#00e5ff", 8, (ctx) => {
    ctx.strokeStyle = "#00e5ff"; ctx.lineWidth = 2;
    ctx.strokeRect(6, 6, T - 12, T - 12);
    ctx.fillStyle = "#00e5ff"; ctx.fillRect(T / 2 - 2, T / 2 - 2, 4, 4);
  });
  t.terminal = withGlow(T, accent, 8, (ctx) => {
    ctx.fillStyle = "#0a1020"; ctx.fillRect(5, 5, T - 10, T - 10);
    ctx.strokeStyle = accent; ctx.lineWidth = 2; ctx.strokeRect(6, 6, T - 12, T - 12);
    ctx.fillStyle = accent; ctx.fillRect(9, 11, T - 18, 2); ctx.fillRect(9, 16, T - 22, 2);
  });
  t.switch = withGlow(T, "#ffea00", 8, (ctx) => {
    ctx.fillStyle = "#1c1a02"; ctx.fillRect(6, 6, T - 12, T - 12);
    ctx.strokeStyle = "#ffea00"; ctx.lineWidth = 2; ctx.strokeRect(7, 7, T - 14, T - 14);
    ctx.fillStyle = "#ffea00"; ctx.beginPath(); ctx.arc(T / 2, T / 2, 4, 0, 7); ctx.fill();
  });
  t.portal = withGlow(T, "#e040fb", 12, (ctx) => {
    ctx.strokeStyle = "#e040fb"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(T / 2, T / 2, 9, 0, 7); ctx.stroke();
    ctx.fillStyle = "#fbd5ff"; ctx.beginPath(); ctx.arc(T / 2, T / 2, 3, 0, 7); ctx.fill();
  });
  return t;
}

// Cinematic backdrop for cutscenes (procedural parallax panorama, 960x540).
// If a generated image asset exists for the chapter it is used instead (see game.js).
export function makeBackdrop(chapterId, accent, tint, rng, mode = "chapter") {
  const W = 960, H = 540;
  const c = C(W, H);
  const ctx = c.getContext("2d");
  // sky gradient
  const sky = ctx.createLinearGradient(0, 0, 0, H);
  if (mode === "delete") { sky.addColorStop(0, "#1a0000"); sky.addColorStop(1, "#4a0505"); }
  else if (mode === "merge") { sky.addColorStop(0, "#fff8e0"); sky.addColorStop(0.4, "#8f7cc9"); sky.addColorStop(1, "#150a2e"); }
  else { sky.addColorStop(0, "#020208"); sky.addColorStop(0.6, tint); sky.addColorStop(1, "#000"); }
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, H);
  // sun / core
  ctx.save();
  ctx.shadowColor = mode === "delete" ? "#ff1744" : accent;
  ctx.shadowBlur = 60;
  ctx.fillStyle = mode === "delete" ? "#ff1744" : accent;
  ctx.globalAlpha = 0.85;
  ctx.beginPath(); ctx.arc(W / 2, H * 0.42, 70, 0, 7); ctx.fill();
  ctx.restore();
  ctx.globalAlpha = 1;
  // horizontal synth-sun stripes
  ctx.fillStyle = "rgba(0,0,0,0.55)";
  for (let i = 0; i < 6; i++) ctx.fillRect(W / 2 - 80, H * 0.42 - 60 + i * 22, 160, 6 + i);
  // skyline silhouettes (two parallax bands)
  for (let band = 0; band < 2; band++) {
    ctx.fillStyle = band === 0 ? "#060613" : "#0b0b22";
    const base = H * (0.55 + band * 0.08);
    let x = 0;
    while (x < W) {
      const bw = 30 + Math.floor(rng() * 70);
      const bh = 40 + Math.floor(rng() * (120 - band * 40));
      ctx.fillRect(x, base - bh, bw, bh + 200);
      // lit windows
      ctx.fillStyle = "rgba(" + (band === 0 ? "0,229,255" : "124,77,255") + ",0.35)";
      for (let wy = base - bh + 6; wy < base - 8; wy += 12) {
        for (let wx = x + 4; wx < x + bw - 6; wx += 10) if (rng() > 0.55) ctx.fillRect(wx, wy, 3, 5);
      }
      ctx.fillStyle = band === 0 ? "#060613" : "#0b0b22";
      x += bw + 6 + Math.floor(rng() * 20);
    }
  }
  // perspective grid floor
  ctx.strokeStyle = mode === "delete" ? "rgba(255,23,68,0.5)" : "rgba(0,229,255,0.4)";
  ctx.lineWidth = 1;
  const horizon = H * 0.7;
  for (let i = 0; i <= 20; i++) {
    const xx = (i - 10) * (W / 10);
    ctx.beginPath(); ctx.moveTo(W / 2 + xx * 0.12, horizon); ctx.lineTo(W / 2 + xx, H); ctx.stroke();
  }
  for (let i = 0; i < 9; i++) {
    const yy = horizon + Math.pow(i / 8, 1.8) * (H - horizon);
    ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy); ctx.stroke();
  }
  // haze
  const haze = ctx.createLinearGradient(0, horizon - 60, 0, horizon + 40);
  haze.addColorStop(0, "rgba(0,0,0,0)");
  haze.addColorStop(0.5, mode === "merge" ? "rgba(255,244,214,0.25)" : "rgba(70,40,140,0.25)");
  haze.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = haze;
  ctx.fillRect(0, horizon - 60, W, 100);
  return c;
}

export function makeScanlines(w, h) {
  const c = C(w, 4);
  const ctx = c.getContext("2d");
  ctx.fillStyle = "rgba(0,0,0,0.18)";
  ctx.fillRect(0, 0, w, 1);
  ctx.fillStyle = "rgba(255,255,255,0.02)";
  ctx.fillRect(0, 2, w, 1);
  return c;
}
