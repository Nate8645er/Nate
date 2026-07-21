/**
 * Demo-Modus: deterministische, simulierte Agentenantworten.
 *
 * Wird vom Orchestrator verwendet, wenn für einen Provider kein API-Key
 * gesetzt ist oder der Call endgültig scheitert. Die Mission läuft damit
 * IMMER vollständig durch – ohne Netzwerk, ohne Zufall (gleiche Eingabe
 * ergibt exakt dieselbe Ausgabe).
 */

import type {
  ArtifactFile,
  OrgDepartmentSpec,
  OrgRoleSpec,
  QualityReport,
  TaskPlan,
  WorkerRole,
} from "./types";

/** Deterministischer Hash (FNV-1a) für stabile "Bewertungen" aus Text. */
function hash(text: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < text.length; i++) {
    h ^= text.charCodeAt(i);
    h = Math.imul(h, 0x01000193);
  }
  return h >>> 0;
}

/** Kürzt das Ziel für Ueberschriften auf eine handliche Länge. */
function shortGoal(goal: string): string {
  const g = goal.trim().replace(/\s+/g, " ");
  return g.length > 80 ? `${g.slice(0, 77)}…` : g;
}

/* --------------------------- Datei-Artefakte (Demo) --------------------------- */

/** HTML-escapen (Attribut/Textkontext) für sicher eingebettete Nutzertexte. */
function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/** Web-Ziele: das Ziel verlangt eine Website/Seite/App/einen Prototyp. */
function isWebGoal(goal: string): boolean {
  return /(website|webseite|web-seite|homepage|kasse|shop|landing\s*page|landingpage|app|prototyp|seite)/i.test(
    goal,
  );
}

/** Dokument-Ziele: Pläne, Strategien, Kampagnen, Berichte, Analysen usw. */
function isDocumentGoal(goal: string): boolean {
  return /(plan|strategie|kampagne|bericht|report|analyse|konzept|studie|marketing|angebot|offerte)/i.test(
    goal,
  );
}

/** Generische Bau-Ziele ohne klaren Web-/Dokument-Bezug (z. B. "erstelle ..."). */
function isGenericBuildGoal(goal: string): boolean {
  return /(bauen|erstell|script|skript|entwickl|entwirf|generier)/i.test(goal);
}

/**
 * Erkennt buildbare Ziele: Web-Aufträge liefern eine echte index.html,
 * Dokument-Aufträge (Plan/Strategie/Kampagne/Bericht/Analyse) liefern ein
 * dokument.md plus praesentation.html, generische Bau-Aufträge eine index.html.
 */
export function isBuildableGoal(goal: string): boolean {
  return isWebGoal(goal) || isDocumentGoal(goal) || isGenericBuildGoal(goal);
}

/**
 * Erzeugt für buildbare Ziele eine kleine, ECHTE Beispiel-Datei-Ausgabe:
 * Web-/generische Bau-Ziele erhalten eine eigenständige (inline gestylte)
 * index.html plus README.md, Dokument-Ziele (Plan/Strategie/Kampagne/Bericht/
 * Analyse) ein professionell formatiertes dokument.md plus praesentation.html.
 * Nicht buildbare Ziele liefern eine leere Liste.
 *
 * Deterministisch (kein Zufall): gleiches Ziel => gleiche Dateien.
 */
export function demoArtifactFiles(goal: string): ArtifactFile[] {
  if (isWebGoal(goal)) return webArtifactFiles(goal);
  if (isDocumentGoal(goal)) return documentArtifactFiles(goal);
  if (isGenericBuildGoal(goal)) return webArtifactFiles(goal);
  return [];
}

/** Web-Startpaket: eigenständige index.html + README.md. */
function webArtifactFiles(goal: string): ArtifactFile[] {
  const g = shortGoal(goal);
  const safe = escapeHtml(g);

  const html = [
    "<!doctype html>",
    '<html lang="de">',
    "<head>",
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    `  <title>${safe}</title>`,
    "  <style>",
    "    :root { --bg:#0f0d0b; --card:#171310; --accent:#ff8c2a; --text:#f3ead9; --muted:#c9b391; }",
    "    * { box-sizing: border-box; }",
    "    body { margin:0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:var(--bg); color:var(--text); }",
    "    header { padding:72px 24px 56px; text-align:center; background:radial-gradient(120% 80% at 50% 0%, rgba(255,140,42,0.16), transparent 70%); }",
    "    header h1 { margin:0 0 12px; font-size:clamp(28px,6vw,52px); letter-spacing:-0.02em; }",
    "    header p { margin:0 auto; max-width:620px; color:var(--muted); font-size:18px; line-height:1.6; }",
    "    .cta { display:inline-block; margin-top:28px; padding:14px 30px; border-radius:8px; background:var(--accent); color:#1a0f04; font-weight:700; text-decoration:none; }",
    "    main { max-width:960px; margin:0 auto; padding:24px; display:grid; gap:20px; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); }",
    "    .card { background:var(--card); border:1px solid rgba(255,140,42,0.18); border-radius:12px; padding:24px; }",
    "    .card h2 { margin:0 0 8px; font-size:20px; color:#fff3e2; }",
    "    .card p { margin:0; color:var(--muted); line-height:1.6; }",
    "    footer { text-align:center; padding:40px 24px 60px; color:var(--muted); font-size:14px; }",
    "  </style>",
    "</head>",
    "<body>",
    "  <header>",
    "    <h1>Willkommen</h1>",
    `    <p>${safe} &ndash; erstellt von Ihrer KI-Abteilung als sofort einsatzbereiter Startpunkt.</p>`,
    '    <a class="cta" href="#kontakt">Jetzt Kontakt aufnehmen</a>',
    "  </header>",
    "  <main>",
    '    <section class="card"><h2>Über uns</h2><p>Kurze, klare Vorstellung Ihres Angebots. Ersetzen Sie diesen Text durch Ihre eigene Geschichte.</p></section>',
    '    <section class="card"><h2>Leistungen</h2><p>Drei bis fünf Kernleistungen als klare Stichpunkte &ndash; damit Besucher den Nutzen sofort erkennen.</p></section>',
    '    <section class="card" id="kontakt"><h2>Kontakt</h2><p>Telefon, E-Mail und Oeffnungszeiten. Ein klarer Handlungsaufruf schliesst die Seite ab.</p></section>',
    "  </main>",
    "  <footer>Demo-Ausgabe &middot; von AI Command Center generiert</footer>",
    "</body>",
    "</html>",
  ].join("\n");

  const readme = [
    `# ${g}`,
    "",
    "Diese Dateien wurden von **AI Command Center** als Beispiel-Startpaket erzeugt.",
    "",
    "## Inhalt",
    "- `index.html` – eigenständige Landingpage (Styles inline, direkt im Browser oder in der Live-Vorschau lauffähig).",
    "",
    "## Nächste Schritte",
    "1. Texte durch Ihre eigenen Inhalte ersetzen.",
    "2. Farben in `:root` an Ihr Branding anpassen.",
    "3. Datei auf einen beliebigen Webspace hochladen.",
  ].join("\n");

  return [
    { path: "index.html", language: "html", content: html },
    { path: "README.md", language: "markdown", content: readme },
  ];
}

/**
 * Dokument-Paket: professionell formatiertes dokument.md (Titel, Abschnitte,
 * Tabellen) plus praesentation.html (scrollbare Slide-Sektionen, pures
 * HTML/CSS ohne externe Libraries).
 */
function documentArtifactFiles(goal: string): ArtifactFile[] {
  const g = shortGoal(goal);
  const safe = escapeHtml(g);

  const dokument = [
    `# ${g}`,
    "",
    `> Erstellt von **AI Command Center**, direkt verwendbares Arbeitsdokument.`,
    "",
    "## 1. Zusammenfassung",
    `Dieses Dokument übersetzt die Mission "${g}" in einen konkreten, umsetzbaren Fahrplan:`,
    "Ausgangslage, Zielbild, Massnahmen mit Zeitplan sowie messbare Erfolgskriterien.",
    "",
    "## 2. Ausgangslage und Zielbild",
    "- Ausgangslage: Das Vorhaben ist definiert, die Umsetzung braucht Struktur und Prioritäten.",
    "- Zielbild: Ein klar positioniertes Angebot mit messbarem Effekt innerhalb von 90 Tagen.",
    "- Annahme: Es liegen noch keine internen Daten vor; alle Werte sind konservative Annahmen.",
    "",
    "## 3. Zielgruppen",
    "| Segment | Beschreibung | Priorität |",
    "| --- | --- | --- |",
    "| Kernzielgruppe | Kaufbereite mit konkretem Bedarf, direkte und nutzenorientierte Ansprache | Hoch |",
    "| Ausbauzielgruppe | Interessierte ohne Dringlichkeit, Ansprache über Inhalte mit Mehrwert | Mittel |",
    "| Multiplikatoren | Partner und Empfehler mit Reichweite im Umfeld | Mittel |",
    "",
    "## 4. Massnahmenplan (90 Tage)",
    "| Phase | Zeitraum | Massnahme | Ergebnis |",
    "| --- | --- | --- | --- |",
    "| 1. Fundament | Woche 1 bis 2 | Positionierung und Kernbotschaft festziehen | Ein Satz Nutzenversprechen |",
    "| 2. Sichtbarkeit | Woche 3 bis 6 | Kanäle aktivieren, Inhalte nach Redaktionsplan | Erste messbare Reichweite |",
    "| 3. Konversion | Woche 7 bis 10 | Angebot mit klarem Handlungsaufruf testen | Erste Anfragen/Abschlüsse |",
    "| 4. Skalierung | Woche 11 bis 13 | Bestes Format verstärken, Schwaches stoppen | Wiederholbarer Prozess |",
    "",
    "## 5. Budget und Erfolgskriterien",
    "| Kennzahl | Zielwert | Messung |",
    "| --- | --- | --- |",
    "| Anfragen pro Woche | Definierter Zielwert ab Woche 6 | Wöchentliches Reporting |",
    "| Kosten pro Anfrage | Obergrenze vorab fixieren | Laufende Auswertung je Kanal |",
    "| Wiederkehrquote | Steigend ab Phase 3 | Monatlicher Vergleich |",
    "",
    "## 6. Nächste Schritte",
    "1. Kernbotschaft und Zielwert bestätigen (Entscheid des Auftraggebers).",
    "2. Phase 1 starten und Verantwortlichkeiten mit Terminen hinterlegen.",
    "3. Nach 4 Wochen Zwischenbilanz ziehen und den Plan nachschärfen.",
  ].join("\n");

  const slideCss = [
    "    :root { --bg:#0f0d0b; --accent:#ff8c2a; --text:#f3ead9; --muted:#c9b391; }",
    "    * { box-sizing: border-box; margin: 0; }",
    "    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; background:var(--bg); color:var(--text); }",
    "    section.slide { min-height:100vh; display:flex; flex-direction:column; justify-content:center; padding:8vh 8vw; border-bottom:1px solid rgba(255,140,42,0.25); }",
    "    .kicker { color:var(--accent); font-size:14px; letter-spacing:0.2em; text-transform:uppercase; margin-bottom:16px; }",
    "    h1 { font-size:clamp(30px,6vw,58px); letter-spacing:-0.02em; line-height:1.1; }",
    "    h2 { font-size:clamp(24px,4vw,40px); margin-bottom:20px; }",
    "    p, li { color:var(--muted); font-size:18px; line-height:1.7; max-width:720px; }",
    "    ul, ol { padding-left:24px; display:grid; gap:10px; }",
    "    .hint { margin-top:auto; padding-top:32px; font-size:13px; color:rgba(201,179,145,0.6); }",
  ].join("\n");

  const praesentation = [
    "<!doctype html>",
    '<html lang="de">',
    "<head>",
    '  <meta charset="utf-8" />',
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />',
    `  <title>${safe}</title>`,
    "  <style>",
    slideCss,
    "  </style>",
    "</head>",
    "<body>",
    '  <section class="slide">',
    '    <div class="kicker">Präsentation</div>',
    `    <h1>${safe}</h1>`,
    "    <p>Fahrplan mit Zielbild, Massnahmen und messbaren Erfolgskriterien. Erstellt von Ihrer KI-Abteilung.</p>",
    '    <div class="hint">Scrollen für die nächste Folie</div>',
    "  </section>",
    '  <section class="slide">',
    '    <div class="kicker">Folie 2</div>',
    "    <h2>Ausgangslage und Zielbild</h2>",
    "    <ul>",
    "      <li>Ausgangslage: Das Vorhaben ist definiert, die Umsetzung braucht Struktur und Prioritäten.</li>",
    "      <li>Zielbild: Ein klar positioniertes Angebot mit messbarem Effekt innerhalb von 90 Tagen.</li>",
    "      <li>Alle Werte sind konservative Annahmen, bis eigene Daten vorliegen.</li>",
    "    </ul>",
    "  </section>",
    '  <section class="slide">',
    '    <div class="kicker">Folie 3</div>',
    "    <h2>Zielgruppen</h2>",
    "    <ul>",
    "      <li><strong>Kernzielgruppe:</strong> Kaufbereite mit konkretem Bedarf, direkte Ansprache.</li>",
    "      <li><strong>Ausbauzielgruppe:</strong> Interessierte ohne Dringlichkeit, Inhalte mit Mehrwert.</li>",
    "      <li><strong>Multiplikatoren:</strong> Partner und Empfehler mit Reichweite.</li>",
    "    </ul>",
    "  </section>",
    '  <section class="slide">',
    '    <div class="kicker">Folie 4</div>',
    "    <h2>Massnahmenplan (90 Tage)</h2>",
    "    <ol>",
    "      <li>Fundament: Positionierung und Kernbotschaft festziehen (Woche 1 bis 2).</li>",
    "      <li>Sichtbarkeit: Kanäle aktivieren, Inhalte nach Redaktionsplan (Woche 3 bis 6).</li>",
    "      <li>Konversion: Angebot mit klarem Handlungsaufruf testen (Woche 7 bis 10).</li>",
    "      <li>Skalierung: Bestes Format verstärken, Schwaches stoppen (Woche 11 bis 13).</li>",
    "    </ol>",
    "  </section>",
    '  <section class="slide">',
    '    <div class="kicker">Folie 5</div>',
    "    <h2>Nächste Schritte</h2>",
    "    <ol>",
    "      <li>Kernbotschaft und Zielwert bestätigen.</li>",
    "      <li>Phase 1 starten, Verantwortlichkeiten mit Terminen hinterlegen.</li>",
    "      <li>Nach 4 Wochen Zwischenbilanz ziehen und nachschärfen.</li>",
    "    </ol>",
    '    <div class="hint">Von AI Command Center generiert, Details im dokument.md</div>',
    "  </section>",
    "</body>",
    "</html>",
  ].join("\n");

  return [
    { path: "dokument.md", language: "markdown", content: dokument },
    { path: "praesentation.html", language: "html", content: praesentation },
  ];
}

/** Rendert Artefakt-Dateien als FILE-Blöcke für die Agenten-Textausgabe. */
function renderFileBlocks(files: readonly ArtifactFile[]): string {
  return files
    .map((f) => `=== FILE: ${f.path} ===\n${f.content}\n=== END FILE ===`)
    .join("\n\n");
}

/** Demo-Teilaufgabe je Worker (für den Commander-Plan im Demo-Modus). */
const DEMO_TASKS: Record<WorkerRole, (g: string) => string> = {
  builder: (g) =>
    `Erstelle ein konkretes, sofort verwendbares Umsetzungspaket für "${g}": Struktur, Kerninhalte und nächste Schritte.`,
  analyst: (g) =>
    `Analysiere für "${g}" Zielgruppe, Marktkontext, Chancen und Risiken und leite drei priorisierte Empfehlungen ab.`,
  marketing: (g) =>
    `Entwickle für "${g}" eine Kampagnenidee mit Zielgruppen-Profilen und einem 4-Wochen-Content-Plan.`,
  research: (g) =>
    `Recherchiere für "${g}" Hintergründe und Alternativen, vergleiche die Optionen strukturiert und bewerte die Quellenlage.`,
  coding: (g) =>
    `Entwirf für "${g}" eine technische Lösung mit Code-Skizze und einem konkreten Automatisierungs-Vorschlag.`,
  business: (g) =>
    `Bewerte für "${g}" Strategie, grobe Zahlen (Kosten/Ertrag) und die drei wichtigsten Risiken inkl. Gegenmassnahmen.`,
};

/** Commander-Plan im Demo-Modus: je eine Teilaufgabe pro aktivem Worker. */
export function demoPlan(goal: string, workers: readonly WorkerRole[]): TaskPlan {
  const g = shortGoal(goal);
  const plan: TaskPlan = {};
  for (const worker of workers) plan[worker] = DEMO_TASKS[worker](g);
  return plan;
}

/** Builder-Ergebnis im Demo-Modus. */
export function demoBuilderOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  const lines = [
    `## Umsetzungspaket: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### 1. Konzept",
    `- Klarer Kern: Die Mission "${g}" wird in ein umsetzbares Ergebnis mit definiertem Umfang übersetzt.`,
    "- Aufbau in drei Ebenen: Fundament (Ziel & Zielgruppe), Ausarbeitung (Inhalte & Struktur), Feinschliff (Ton & Details).",
    "",
    "### 2. Struktur",
    "1. Ausgangslage und Zielbild in zwei Sätzen festhalten.",
    "2. Kerninhalte als nummerierte Bausteine ausarbeiten – jeder Baustein direkt verwendbar.",
    "3. Offene Punkte als konkrete Entscheidungsfragen an den Auftraggeber formulieren.",
    "",
    "### 3. Nächste Schritte",
    "- Entwurf intern gegen das Missionsziel prüfen.",
    "- Eine Feedbackrunde einplanen, danach finalisieren.",
    "- Ergebnis in den Zielkanal (Dokument, Website, Präsentation) überführen.",
  ];

  // Buildbare Ziele erhalten echte Beispiel-Dateien als FILE-Blöcke, die der
  // Orchestrator zum artifact-Event parst.
  const files = demoArtifactFiles(goal);
  if (files.length) {
    lines.push(
      "",
      "### 4. Erzeugte Dateien",
      "Direkt verwendbares Startpaket (siehe Datei-Blöcke):",
      "",
      renderFileBlocks(files),
    );
  }

  return lines.join("\n");
}

/** Analyst-Ergebnis im Demo-Modus. */
export function demoAnalystOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Analyse: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Zielgruppe",
    "- Primär: Entscheider mit klarem Bedarf und wenig Zeit – erwartet ein direkt verwendbares Ergebnis.",
    "- Sekundär: Umsetzende Teams, die mit dem Ergebnis weiterarbeiten.",
    "",
    "### Marktkontext",
    "- Annahme: Der Wettbewerb liefert generische Lösungen; Differenzierung entsteht durch Präzision und Tempo.",
    "- Annahme: Der grösste Hebel liegt in einer klaren Positionierung, nicht in mehr Umfang.",
    "",
    "### Chancen",
    "- Schneller sichtbarer Mehrwert durch ein fokussiertes erstes Ergebnis.",
    "- Wiederverwendbare Struktur für Folgemissionen.",
    "",
    "### Risiken",
    "- Unklare Zieldefinition führt zu Streuverlust – Gegenmassnahme: Zielbild in Satz 1 fixieren.",
    "- Ueberladung des Ergebnisses – Gegenmassnahme: maximal drei Kernaussagen.",
    "",
    "### Priorisierte Empfehlungen",
    "1. Zielbild und Kernbotschaft zuerst festziehen.",
    "2. Ein minimal vollständiges Ergebnis liefern, dann iterieren.",
    "3. Erfolgskriterium definieren (woran wird das Ergebnis gemessen?).",
  ].join("\n");
}

/** Marketing-Ergebnis im Demo-Modus. */
export function demoMarketingOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Marketing-Paket: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Kampagnenidee",
    `- Leitmotiv: "${g}" als greifbaren Kundennutzen erzählen – eine Kernbotschaft, überall konsistent.`,
    "- Mechanik: Aufmerksamkeit (Reichweiten-Kanal) -> Vertrauen (Beweis/Story) -> Handlung (klares Angebot mit CTA).",
    "",
    "### Zielgruppen",
    "- Kernzielgruppe: Bestandsnahe Kaufbereite mit konkretem Bedarf – Ansprache direkt und nutzenorientiert.",
    "- Ausbauzielgruppe: Interessierte ohne Dringlichkeit – Ansprache über Inhalte mit Mehrwert statt Rabatt.",
    "",
    "### Content-Plan (4 Wochen)",
    "1. Woche 1: Kernbotschaft + Vorstellung (1 Hero-Beitrag, 2 Kurzformate).",
    "2. Woche 2: Beweis – Kundenstimme oder Blick hinter die Kulissen (2 Beiträge).",
    "3. Woche 3: Angebot mit klarem CTA (1 Kampagnen-Beitrag, 1 Reminder).",
    "4. Woche 4: Auswertung + bestes Format wiederholen (2 Beiträge).",
    "",
    "### Messbarer nächster Schritt",
    "- Ein Kanal, ein Angebot, zwei Wochen testen; Erfolgskriterium vorab festlegen (z. B. Anfragen pro Woche).",
  ].join("\n");
}

/** Coding-Ergebnis im Demo-Modus. */
export function demoCodingOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Technische Lösung: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Lösungsskizze",
    "- Kleinster sinnvoller Aufbau: ein Eingang (Formular/API), ein Verarbeitungsschritt, ein Ausgang (Benachrichtigung/Ablage).",
    "- Erst manuell validieren, dann automatisieren – keine Infrastruktur vor dem ersten Nutzen.",
    "",
    "### Code-Skizze",
    "```ts",
    "// Minimaler Automatisierungs-Endpunkt (Skizze, bewusst ohne Framework-Details)",
    "export async function handleRequest(input: { name: string; nachricht: string }) {",
    "  if (!input.name.trim() || !input.nachricht.trim()) {",
    '    return { ok: false, fehler: "Name und Nachricht sind erforderlich." };',
    "  }",
    "  await speichern(input);        // z. B. Tabelle oder CRM",
    "  await benachrichtigen(input);  // z. B. E-Mail oder Chat",
    "  return { ok: true };",
    "}",
    "```",
    "",
    "### Automatisierungs-Vorschlag",
    "1. Wiederkehrenden manuellen Schritt identifizieren (höchste Frequenz zuerst).",
    "2. Mit einem No-Code-Workflow oder kleinem Skript abbilden; Fehlerfall mit Benachrichtigung absichern.",
    "3. Annahme: Es existiert noch keine Systemlandschaft – die Skizze bleibt bewusst anschlussoffen.",
  ].join("\n");
}

/** Research-Ergebnis im Demo-Modus. */
export function demoResearchOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Tiefenrecherche: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Hintergrund",
    `- Die Fragestellung "${g}" lässt sich in drei Optionen zerlegen: Status quo behalten, punktuell verbessern, neu aufsetzen.`,
    "",
    "### Vergleich der Optionen",
    "1. Status quo: kein Aufwand, aber ungenutztes Potenzial – sinnvoll nur bei fehlenden Ressourcen.",
    "2. Punktuell verbessern: bestes Aufwand-Nutzen-Verhältnis; schnell messbar.",
    "3. Neu aufsetzen: höchstes Potenzial, aber längste Amortisation und grösstes Risiko.",
    "",
    "### Quellenlage",
    "- Demo-Modus: Es wurden keine Live-Quellen abgerufen; alle Aussagen sind als Annahmen gekennzeichnet.",
    "- Für eine belastbare Entscheidung: zwei bis drei Branchenquellen und eigene Zahlen ergänzen.",
    "",
    "### Empfehlung",
    "- Mit Option 2 starten und ein Erfolgskriterium definieren; Option 3 nur bei belegtem Engpass prüfen.",
  ].join("\n");
}

/** Business-Ergebnis im Demo-Modus. */
export function demoBusinessOutput(goal: string, task: string): string {
  const g = shortGoal(goal);
  return [
    `## Business-Bewertung: ${g}`,
    "",
    `**Auftrag:** ${task}`,
    "",
    "### Strategie",
    `- "${g}" auf ein klares Nutzenversprechen für eine Kernzielgruppe zuspitzen; Breite folgt nach dem ersten Beleg.`,
    "",
    "### Zahlen (Annahmen)",
    "- Aufwand: überschaubares Startbudget plus laufende Zeit pro Woche – vorab als Obergrenze fixieren.",
    "- Ertrag: erster messbarer Effekt nach 4 bis 8 Wochen realistisch; Break-even konservativ planen.",
    "",
    "### Risiken und Gegenmassnahmen",
    "1. Nachfrage bleibt aus (hoch/mittel): mit kleinem Test validieren, bevor investiert wird.",
    "2. Aufwand unterschätzt (mittel/mittel): Umfang fest deckeln, Zusatzwünsche in Phase 2 schieben.",
    "3. Kein messbarer Effekt (mittel/hoch): Erfolgskriterium vorab definieren und wöchentlich prüfen.",
    "",
    "### Entscheidungsvorlage",
    "- Weiterführen, wenn das Erfolgskriterium nach dem Testzeitraum erreicht ist; sonst stoppen oder anpassen.",
  ].join("\n");
}

/**
 * Demo-Ausgabe je Worker-Rolle – der Orchestrator wählt darüber den
 * passenden Fallback für jeden aktiven Worker.
 */
export const DEMO_WORKER_OUTPUTS: Record<
  WorkerRole,
  (goal: string, task: string) => string
> = {
  builder: demoBuilderOutput,
  analyst: demoAnalystOutput,
  marketing: demoMarketingOutput,
  research: demoResearchOutput,
  coding: demoCodingOutput,
  business: demoBusinessOutput,
};

/* ------------------------- Organisations-Modus (Demo) ------------------------- */

/**
 * Bauplan der Demo-Firma: 3 Abteilungen mit je 3 Spezialisten-Rollen
 * (9 dynamische Agenten). Die Teilaufgaben werden deterministisch aus dem
 * Missionsziel abgeleitet.
 */
const DEMO_ORG_BLUEPRINT: readonly {
  name: string;
  roles: readonly { rolle: string; fachgebiet: string; teilaufgabe: (g: string) => string }[];
}[] = [
  {
    name: "Strategie & Analyse",
    roles: [
      {
        rolle: "Marktanalyst",
        fachgebiet: "Marktforschung",
        teilaufgabe: (g) =>
          `Analysiere für "${g}" den Markt: Grösse, Trends, Zielsegmente und die drei wichtigsten Wachstumstreiber.`,
      },
      {
        rolle: "Wettbewerbsanalyst",
        fachgebiet: "Wettbewerbsanalyse",
        teilaufgabe: (g) =>
          `Vergleiche für "${g}" die relevanten Wettbewerber und leite drei Differenzierungschancen ab.`,
      },
      {
        rolle: "Finanzplaner",
        fachgebiet: "Finanzplanung",
        teilaufgabe: (g) =>
          `Erstelle für "${g}" eine grobe Kosten-/Ertragsrechnung mit Annahmen und Break-even-Einschätzung.`,
      },
    ],
  },
  {
    name: "Produkt & Umsetzung",
    roles: [
      {
        rolle: "Konzeptentwickler",
        fachgebiet: "Konzeption",
        teilaufgabe: (g) =>
          `Entwickle für "${g}" das inhaltliche Kernkonzept mit Struktur und priorisierten Bausteinen.`,
      },
      {
        rolle: "Umsetzungsplaner",
        fachgebiet: "Projektplanung",
        teilaufgabe: (g) =>
          `Plane für "${g}" die Umsetzung in Phasen mit Meilensteinen, Aufwänden und Abhängigkeiten.`,
      },
      {
        rolle: "Prozessoptimierer",
        fachgebiet: "Prozesse & Automatisierung",
        teilaufgabe: (g) =>
          `Identifiziere für "${g}" die wichtigsten Prozesse und schlage je eine Automatisierung vor.`,
      },
    ],
  },
  {
    name: "Marketing & Vertrieb",
    roles: [
      {
        rolle: "Kampagnenmanager",
        fachgebiet: "Kampagnenplanung",
        teilaufgabe: (g) =>
          `Entwirf für "${g}" eine Kampagne mit Kernbotschaft, Kanälen und 4-Wochen-Plan.`,
      },
      {
        rolle: "Content-Stratege",
        fachgebiet: "Content-Strategie",
        teilaufgabe: (g) =>
          `Erstelle für "${g}" eine Content-Strategie mit Formaten, Frequenz und Erfolgskriterien.`,
      },
      {
        rolle: "Vertriebsplaner",
        fachgebiet: "Vertriebsstrategie",
        teilaufgabe: (g) =>
          `Definiere für "${g}" den Vertriebsweg: Zielkunden, Angebotslogik und messbare nächste Schritte.`,
      },
    ],
  },
];

/**
 * ORG-PLAN im Demo-Modus: deterministische virtuelle Firma (3 Abteilungen,
 * 9 Rollen) im selben JSON-Format, das der Commander liefern würde.
 * Die ids vergibt der Orchestrator beim Parsen (Slug aus der Rolle).
 */
export function demoOrgPlan(goal: string): {
  departments: { name: string; roles: { rolle: string; fachgebiet: string; teilaufgabe: string }[] }[];
} {
  const g = shortGoal(goal);
  return {
    departments: DEMO_ORG_BLUEPRINT.map((d) => ({
      name: d.name,
      roles: d.roles.map((r) => ({
        rolle: r.rolle,
        fachgebiet: r.fachgebiet,
        teilaufgabe: r.teilaufgabe(g),
      })),
    })),
  };
}

/**
 * Deterministische Demo-Antwort einer dynamischen Rolle – aus rolle,
 * fachgebiet und teilaufgabe generiert (auch für LLM-erdachte Rollen).
 */
export function demoDynOutput(goal: string, role: OrgRoleSpec): string {
  const g = shortGoal(goal);
  const variant = hash(`${role.rolle}|${role.teilaufgabe}`) % 3;
  const empfehlung = [
    "Mit dem kleinsten messbaren Schritt starten und wöchentlich nachsteuern.",
    "Eine Verantwortlichkeit und einen Termin je Massnahme festlegen.",
    "Erfolgskriterium vorab definieren und nach vier Wochen prüfen.",
  ][variant];
  return [
    `## ${role.rolle}: ${g}`,
    "",
    `**Fachgebiet:** ${role.fachgebiet}`,
    "",
    `**Auftrag:** ${role.teilaufgabe}`,
    "",
    "### Ergebnis",
    `- Kernbefund: Aus Sicht ${role.fachgebiet} liegt der grösste Hebel für "${g}" in Fokus und klarer Priorisierung.`,
    `- Vorgehen: Der Auftrag wurde in drei umsetzbare Schritte zerlegt – Analyse, Massnahme, Messung.`,
    "- Annahme: Es liegen keine internen Daten vor; alle Aussagen sind als Annahmen gekennzeichnet.",
    "",
    "### Empfehlung",
    `1. ${empfehlung}`,
    "2. Ergebnis mit den Nachbar-Rollen der Abteilung abgleichen, um Doppelarbeit zu vermeiden.",
    "3. Offene Entscheidungsfragen an den Commander zurückmelden.",
  ].join("\n");
}

/** Abteilungs-Zusammenfassung des Commanders im Demo-Modus. */
export function demoDepartmentSummary(dept: OrgDepartmentSpec, goal: string): string {
  const g = shortGoal(goal);
  return [
    `- Die Abteilung ${dept.name} hat ${dept.roles.length} Spezialisten-Ergebnisse zu "${g}" geliefert.`,
    ...dept.roles.map(
      (r) => `- ${r.rolle} (${r.fachgebiet}): Teilaufgabe bearbeitet, Empfehlung mit messbarem nächstem Schritt.`,
    ),
    "- Gemeinsame Linie: klein starten, Erfolgskriterium definieren, wöchentlich nachsteuern.",
  ].join("\n");
}

/** Quality-Report im Demo-Modus: stabiler Score 82–91 aus dem Input abgeleitet. */
export function demoQualityReport(combinedOutputs: string): QualityReport {
  return {
    score: 82 + (hash(combinedOutputs) % 10),
    improvements: [
      "Kernaussagen mit konkreten Zahlen oder Beispielen unterlegen.",
      "Annahmen durch kurze Validierung (Kundenfeedback, Daten) absichern.",
      "Nächste Schritte mit Verantwortlichkeiten und Terminen versehen.",
    ],
  };
}

/** Finale Synthese im Demo-Modus. */
export function demoSynthesis(goal: string, combinedOutputs: string): string {
  const g = shortGoal(goal);
  const body = combinedOutputs.trim()
    ? combinedOutputs.trim()
    : "_Keine Worker-Ergebnisse verfügbar – Kurzfassung aus dem Missionsziel abgeleitet._";
  return [
    `# Ergebnis: ${g}`,
    "",
    "## Zusammenfassung",
    `Die Mission "${g}" wurde vom Team bearbeitet: Jeder aktive Worker hat seine Teilaufgabe geliefert – vom umsetzbaren Paket bis zu Kontext, Chancen und Risiken. Alles ist unten zu einem verwendbaren Gesamtergebnis zusammengeführt.`,
    "",
    body,
    "",
    "## Empfohlenes Vorgehen",
    "1. Ergebnis reviewen und Zielbild bestätigen.",
    "2. Die priorisierten Empfehlungen des Analysten umsetzen.",
    "3. Verbesserungsvorschläge des Quality-Agenten einarbeiten und finalisieren.",
  ].join("\n");
}
