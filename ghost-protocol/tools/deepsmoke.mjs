// Deep smoke: loads every map of every chapter, simulates 2s each, exercises
// boss states and the ending choice screen. Fails on any runtime exception.
import { createRequire } from "node:module";
const require = createRequire(import.meta.url);
const { chromium } = require("playwright");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on("pageerror", (e) => errors.push("PAGEERROR: " + e.message));

await page.goto("http://localhost:8123/?dev=1");
await page.waitForTimeout(800);

const result = await page.evaluate(() => {
  const g = window.__g;
  const log = [];
  try {
    g.newRun();
    for (const a of ["dash", "hack", "emp", "shield", "cloak", "magnet", "slow", "teleport"]) g.run.abilities[a] = true;
    for (let ch = 1; ch <= 6; ch++) {
      g.run.chapter = ch;
      const maps = g.chapterDef().maps;
      for (let mi = 0; mi < maps.length; mi++) {
        g.loadLevel(mi);
        g.screen = "play";
        for (let i = 0; i < 120; i++) {
          g.update(1 / 60);
          if (g.screen === "dialog") { // boss intro — click through
            g.dialog.chars = 1e9;
            g.dialog.idx = g.dialog.lines.length;
            const cb = g.dialog.onDone; g.dialog = null; cb();
          }
          if (g.screen === "gameover") { g.run.hp = 100; g.screen = "play"; }
        }
        g.render();
        log.push(`ch${ch} map${mi} ok (${g.level.hunters.length}h ${g.level.drones.length}d boss=${g.level.boss ? g.level.boss.type : "-"})`);
        // boss kill path
        if (g.level.boss) {
          g.level.boss.state = "fight";
          g.level.boss.hp = 1;
          const before = g.run.chapter;
          for (let i = 0; i < 30 && g.level.boss && g.level.boss.state !== "dead"; i++) {
            g.level.boss.hp = -1;
            g.update(1 / 60);
          }
          // resolve defeat dialog
          for (let i = 0; i < 10 && g.screen === "dialog"; i++) {
            const cb = g.dialog.onDone; g.dialog = null; cb();
          }
          log.push(`  boss dead → screen=${g.screen} chapter=${g.run.chapter} (was ${before})`);
          if (g.screen === "cutscene") { // chapter intro fired — finish it
            g.cutscene.idx = g.cutscene.beats.length;
            g.update(1 / 60);
            log.push(`  cutscene done → screen=${g.screen} chapter=${g.run.chapter} map=${g.run.mapIdx}`);
          }
          // restore loop control
          g.run.chapter = ch;
        }
      }
    }
    // ending choice render
    g.screen = "endchoice"; g.endIdx = 1;
    g.update(1 / 60);
    g.render();
    log.push("endchoice ok, TOTAL_FRAGS check: fragTotal=" + g.run.fragTotal);
    // saves round-trip
    g.run.chapter = 3; g.run.mapIdx = 0;
    g.saveSlot(0);
    const ok = g.loadSlot(0);
    log.push("save/load slot0: " + ok + " chapter=" + g.run.chapter + " screen=" + g.screen);
    // options + skilltree + inventory + quests + achievements render
    for (const s of ["pause", "skilltree", "inventory", "quests", "achievements", "saves", "options", "credits", "menu"]) {
      g.screen = s;
      if (s === "credits") g.creditsY = 0;
      g.update(1 / 60);
      g.render();
      log.push("screen " + s + " ok");
    }
    // hack overlay
    g.run.chapter = 2; g.loadLevel(0); g.screen = "play";
    g.startHack(() => {}, () => {});
    g.update(1 / 60); g.render();
    log.push("hack overlay ok");
    // dialog with npc
    g.screen = "play";
    g.talkToNpc();
    g.update(1 / 60); g.render();
    log.push("npc dialog ok, screen=" + g.screen);
    return { ok: true, log };
  } catch (e) {
    return { ok: false, log, err: e.message + "\n" + e.stack };
  }
});

console.log(result.log.join("\n"));
if (!result.ok) console.log("ERR:", result.err);
console.log("pageerrors:", errors.length ? errors : "none");
await browser.close();
process.exit(result.ok && !errors.length ? 0 : 1);
