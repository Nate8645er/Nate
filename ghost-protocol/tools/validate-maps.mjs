// Map validator: width consistency, sealed border, reachability of all specials from P.
import { CHAPTERS } from "../public/levels.js";

let failures = 0;
const WALK = (ch) => ch !== "#";

for (const chap of CHAPTERS) {
  chap.maps.forEach((m, mi) => {
    const g = m.grid;
    const name = `ch${chap.id} map${mi}`;
    const w = g[0].length, h = g.length;
    for (let y = 0; y < h; y++) {
      if (g[y].length !== w) { console.log(`${name}: row ${y} width ${g[y].length} != ${w}`); failures++; }
    }
    // border sealed
    for (let x = 0; x < w; x++) {
      for (const y of [0, h - 1]) {
        if (g[y][x] !== "#") { console.log(`${name}: border hole at ${x},${y} '${g[y][x]}'`); failures++; }
      }
    }
    for (let y = 0; y < h; y++) {
      for (const x of [0, w - 1]) {
        if (g[y][x] !== "#") { console.log(`${name}: border hole at ${x},${y} '${g[y][x]}'`); failures++; }
      }
    }
    // find P
    let px = -1, py = -1, counts = {};
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const c = g[y][x];
      counts[c] = (counts[c] || 0) + 1;
      if (c === "P") { px = x; py = y; }
    }
    if (px < 0) { console.log(`${name}: no P`); failures++; return; }
    if ((counts["P"] || 0) !== 1) { console.log(`${name}: ${counts["P"]} P tiles`); failures++; }
    if (!m.arena && !counts["X"]) { console.log(`${name}: no X exit`); failures++; }
    if (m.arena && !counts["B"]) { console.log(`${name}: arena without B`); failures++; }
    if (!m.arena && (m.quota || 0) > (counts["F"] || 0)) { console.log(`${name}: quota ${m.quota} > fragments ${counts["F"] || 0}`); failures++; }
    for (const [a, b] of [["1", "2"], ["3", "4"]]) {
      const ca = counts[a] || 0, cb = counts[b] || 0;
      if ((ca || cb) && (ca !== 1 || cb !== 1)) { console.log(`${name}: portal pair ${a}/${b} counts ${ca}/${cb}`); failures++; }
    }
    // BFS with portals
    const seen = Array.from({ length: h }, () => new Array(w).fill(false));
    const portals = {};
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const c = g[y][x];
      if ("1234".includes(c)) portals[c] = [x, y];
    }
    const stack = [[px, py]]; seen[py][px] = true;
    while (stack.length) {
      const [x, y] = stack.pop();
      const c = g[y][x];
      const pairs = { "1": "2", "2": "1", "3": "4", "4": "3" };
      if (pairs[c] && portals[pairs[c]]) {
        const [tx, ty] = portals[pairs[c]];
        if (!seen[ty][tx]) { seen[ty][tx] = true; stack.push([tx, ty]); }
      }
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nx = x + dx, ny = y + dy;
        if (nx < 0 || ny < 0 || nx >= w || ny >= h) continue;
        if (!seen[ny][nx] && WALK(g[ny][nx])) { seen[ny][nx] = true; stack.push([nx, ny]); }
      }
    }
    const specials = "FKQDNZCXA+hSEeB1234Ll%";
    for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
      const c = g[y][x];
      if (specials.includes(c) && !seen[y][x]) {
        console.log(`${name}: unreachable '${c}' at ${x},${y}`); failures++;
      }
    }
  });
}
console.log(failures ? `FAILED: ${failures} problems` : "ALL MAPS OK");
process.exit(failures ? 1 : 0);
