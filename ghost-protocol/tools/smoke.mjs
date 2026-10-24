// Playwright smoke test: boots the game, drives menu → intro → chapter 1 play,
// moves the player, checks fps, console errors and 404s, takes screenshots.
// Run: NODE_PATH=$(npm root -g) node tools/smoke.mjs [screenshotDir]
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const shotDir = process.argv[2] || "/tmp";
const errors = [];
const notFound = [];

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));
page.on("response", (r) => { if (r.status() === 404) notFound.push(r.url()); });

await page.goto("http://localhost:8123/?dev=1");
await page.waitForTimeout(1200);
await page.screenshot({ path: `${shotDir}/01_menu.png` });

const state = async () => page.evaluate(() => document.getElementById("dev").textContent);
console.log("menu:", await state());

// new game
await page.keyboard.press("Enter");
await page.waitForTimeout(600);
await page.screenshot({ path: `${shotDir}/02_intro.png` });
// skip intro + chapter cutscene (Escape skips a whole cutscene)
for (let i = 0; i < 10; i++) {
  const s = await state();
  if (!s.includes("cutscene")) break;
  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);
}
await page.waitForTimeout(800);
console.log("after cutscenes:", await state());
await page.screenshot({ path: `${shotDir}/03_play.png` });

// verify play state + movement
const pos0 = await page.evaluate(() => window.__g ? [window.__g.player.x, window.__g.player.y] : null);
await page.keyboard.down("KeyD");
await page.waitForTimeout(900);
await page.keyboard.up("KeyD");
await page.keyboard.down("KeyS");
await page.waitForTimeout(900);
await page.keyboard.up("KeyS");
const pos1 = await page.evaluate(() => window.__g ? [window.__g.player.x, window.__g.player.y] : null);
console.log("moved:", pos0, "->", pos1);
await page.screenshot({ path: `${shotDir}/04_moved.png` });

// dash + pulse
await page.keyboard.press("ShiftLeft");
await page.keyboard.press("Space");
await page.waitForTimeout(400);

// pause menu, skilltree
await page.keyboard.press("Escape");
await page.waitForTimeout(300);
await page.screenshot({ path: `${shotDir}/05_pause.png` });
await page.keyboard.press("Escape");
await page.keyboard.press("KeyK");
await page.waitForTimeout(300);
await page.screenshot({ path: `${shotDir}/06_skills.png` });
await page.keyboard.press("KeyK");

// hud + fps after 3s of play
await page.waitForTimeout(3000);
const dev = await state();
console.log("dev overlay:", dev);
await page.screenshot({ path: `${shotDir}/07_late.png` });

// mobile viewport sanity
await page.setViewportSize({ width: 390, height: 844 });
await page.waitForTimeout(500);
await page.screenshot({ path: `${shotDir}/08_mobile.png` });

console.log("console errors:", errors.length ? errors : "none");
console.log("404s:", notFound.length ? notFound : "none");
const fps = parseInt((dev || "").match(/(\d+) fps/)?.[1] || "0", 10);
const playState = (dev || "").includes("play");
const moved = pos0 && pos1 && (Math.abs(pos1[0] - pos0[0]) > 10 || Math.abs(pos1[1] - pos0[1]) > 10);
console.log(JSON.stringify({ fps, playState, moved }));
await browser.close();
const hardErrors = errors.filter(e => !e.includes("favicon") && !e.includes("img_") && !e.includes("sfx_") && !e.includes("Failed to load resource"));
process.exit(hardErrors.length || !playState || !moved ? 1 : 0);
