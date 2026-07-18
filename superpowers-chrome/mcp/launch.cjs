#!/usr/bin/env node
// Environment-aware launcher for the superpowers-chrome MCP server.
//
// Added for Nates Setup (siehe ../SETUP-NOTES.md). Zweck:
//  1. Chromium-Erkennung in Claude-Code-Remote-Containern: Dort liegt der
//     Browser unter /opt/pw-browsers/chromium statt /usr/bin/*. Wenn kein
//     Standardpfad existiert und CHROME_WS_BROWSER nicht gesetzt ist, wird
//     der Playwright-Chromium automatisch verwendet.
//  2. Egress-Proxy: In Remote-Sessions muss ausgehendes HTTPS durch den
//     Agent-Proxy (HTTPS_PROXY). Chrome liest diese Variable nicht selbst,
//     daher wird --proxy-server an CHROME_EXTRA_ARGS angehaengt, sofern
//     nicht bereits ein Proxy konfiguriert ist.
//
// Auf Systemen ohne diese Besonderheiten (lokaler Mac/PC mit installiertem
// Chrome, kein HTTPS_PROXY) verhaelt sich der Launcher exakt wie der
// direkte Start von dist/index.js.
"use strict";

const { existsSync } = require("node:fs");
const path = require("node:path");

const STANDARD_PATHS = {
  darwin: [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
  ],
  linux: ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"],
  win32: [
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  ],
};

const PLAYWRIGHT_CHROMIUM = "/opt/pw-browsers/chromium";

if (!process.env.CHROME_WS_BROWSER) {
  const standard = (STANDARD_PATHS[process.platform] || []).some((p) => existsSync(p));
  if (!standard && existsSync(PLAYWRIGHT_CHROMIUM)) {
    process.env.CHROME_WS_BROWSER = PLAYWRIGHT_CHROMIUM;
    console.error(`launch.cjs: using Playwright Chromium at ${PLAYWRIGHT_CHROMIUM}`);
  }
}

const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
const extra = process.env.CHROME_EXTRA_ARGS || "";
if (proxy && !extra.includes("--proxy-server")) {
  // --ssl-version-max=tls1.2: der Egress-Gateway resettet Chromes
  // TLS-1.3-ClientHello (unabhaengig von ML-KEM/ECH, per Netlog verifiziert);
  // mit TLS 1.2 laufen Handshakes und Zertifikatspruefung normal durch.
  process.env.CHROME_EXTRA_ARGS =
    `${extra} --proxy-server=${proxy} --ssl-version-max=tls1.2`.trim();
  console.error(`launch.cjs: routing Chrome through proxy ${proxy} (TLS <=1.2)`);
}

// Hand over to the bundled ESM server, forwarding CLI args (e.g. --headless).
import(path.join(__dirname, "dist", "index.js")).catch((err) => {
  console.error("launch.cjs: failed to start MCP server:", err);
  process.exit(1);
});
