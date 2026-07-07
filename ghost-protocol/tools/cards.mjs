// Renders the deploy card images from the game's own art:
// dist/thumbnail.jpg (16:9, title screen) and dist/favicon.png (1:1 emblem).
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

mkdirSync("dist", { recursive: true });
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.goto("http://localhost:8123/");
await page.waitForTimeout(1200);
await page.screenshot({ path: "dist/thumbnail.jpg", type: "jpeg", quality: 90 });

// favicon: glowing cyan ghost emblem on deep midnight circuit background (style formula palette)
await page.evaluate(() => {
  const c = document.createElement("canvas");
  c.width = 512; c.height = 512;
  c.id = "fav";
  const x = c.getContext("2d");
  x.fillStyle = "#0a1230";
  x.fillRect(0, 0, 512, 512);
  x.strokeStyle = "rgba(124,77,255,0.25)";
  x.lineWidth = 6;
  for (let i = 0; i < 8; i++) {
    x.strokeRect(40 + i * 26, 40 + i * 18, 432 - i * 52, 432 - i * 36);
  }
  x.shadowColor = "#00e5ff";
  x.shadowBlur = 60;
  // ghost body
  x.fillStyle = "#7df9ff";
  x.beginPath();
  x.moveTo(136, 400);
  x.lineTo(136, 240);
  x.arc(256, 240, 120, Math.PI, 0);
  x.lineTo(376, 400);
  for (let i = 0; i < 4; i++) x.lineTo(376 - (i + 0.5) * 60, 400 - (i % 2 ? 0 : 42));
  x.closePath();
  x.fill();
  x.shadowBlur = 0;
  // visor
  x.fillStyle = "#03252e";
  x.fillRect(176, 216, 160, 56);
  x.fillStyle = "#ffffff";
  x.fillRect(190, 228, 54, 22);
  document.body.appendChild(c);
});
const fav = await page.locator("#fav");
await fav.screenshot({ path: "dist/favicon.png" });
await browser.close();
console.log("cards written to dist/");
