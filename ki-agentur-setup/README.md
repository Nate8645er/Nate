# KI-Agentur – Automatische Windows-Einrichtung

Eine **Ein-Klick-Installationssuite** für deine professionelle KI-Web-Agentur.
Installiert alle 9 Tools + Voraussetzungen aus den **offiziellen Quellen**,
konfiguriert sie, liefert Startskripte und bindet sie in dein
**ULTRA Enterprise OS** ein.

> ⚠️ **Wichtig – bitte zuerst lesen:**
> Diese Skripte wurden in einer Cloud-Linux-Umgebung **erstellt**, aber sie
> laufen auf **deinem Windows-PC**. Sie konnten dort noch **nicht** ausgeführt
> werden (ich habe keinen Zugriff auf deinen PC). Führe `install.ps1` selbst
> auf deinem Rechner aus – das Skript erledigt dann alles automatisch.

---

## Was wird installiert

**Voraussetzungen** (via `winget`): Git · Python 3.12 · Node.js LTS (+npm) · uv ·
Docker Desktop · Java (Temurin 21) · Visual Studio 2022 Build Tools (C++) · pnpm

**Tools** (offizielle Repos/Pakete):

| Tool | Quelle | Zweck |
|---|---|---|
| ComfyUI | comfyanonymous/ComfyUI | KI-Bilder, Logos, Banner, Produktbilder |
| Comfy CLI | Comfy-Org/comfy-cli | ComfyUI automatisieren |
| ComfyUI MCP | joenorton/comfyui-mcp-server | ComfyUI als Agent-Werkzeug |
| browser-use | browser-use/browser-use | Webseiten testen & bedienen |
| CrewAI | crewAIInc/crewAI | Multi-Agenten & Workflows |
| n8n | n8n-io/n8n | Automatisierungen & Workflows |
| Metabase | metabase/metabase | Dashboards & Datenanalyse |
| OmniRoute | diegosouzapw/OmniRoute | KI-Gateway / Modell-Routing |
| bolt.diy | stackblitz-labs/bolt.diy | Schnelle Webanwendungen |

---

## Schnellstart (auf deinem Windows-PC)

1. **Repo holen** und in den Ordner wechseln:
   ```powershell
   git clone https://github.com/Nate8645er/Nate.git
   cd Nate\ki-agentur-setup
   ```

2. **Voraussetzung `winget`** prüfen (ab Windows 10/11 meist vorhanden):
   ```powershell
   winget --version
   ```
   Fehlt es → „App Installer“ aus dem Microsoft Store installieren.

3. **Alles installieren** (PowerShell, normaler Benutzer):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```
   > Nach der Docker-Desktop-Installation ist i. d. R. ein **Windows-Neustart**
   > nötig. Danach `install.ps1` bei Bedarf erneut ausführen – alles ist
   > idempotent (bereits Installiertes wird übersprungen).

4. **Neues Terminal öffnen** (damit alle Befehle im PATH sind) und prüfen:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\99-verify.ps1
   ```

5. **Dienste starten** (jeder in eigenem Fenster):
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\start\start-all.ps1
   ```

### Nur einzelne Tools
```powershell
.\install.ps1 -Only comfyui,n8n,bolt-diy
```
Gültige Namen: `comfyui`, `comfy-cli`, `comfyui-mcp`, `browser-use`, `crewai`,
`n8n`, `metabase`, `omniroute`, `bolt-diy`.

---

## Ordnerstruktur

```
ki-agentur-setup/
├─ install.ps1              # Master: Voraussetzungen + alle Tools + Verify
├─ scripts/
│  ├─ _common.ps1           # gemeinsame Helfer (Logging, winget, Retry, Git)
│  ├─ 00-prerequisites.ps1  # Git/Python/Node/uv/Docker/Java/BuildTools/pnpm
│  ├─ 10-comfyui.ps1  …  70-bolt-diy.ps1
│  └─ 99-verify.ps1         # Health-Check
├─ start/                   # Startskripte je Dienst + start-all.ps1
├─ config/
│  ├─ .env.example          # zentrale API-Keys / Ports
│  └─ claude-mcp-config.example.json  # ComfyUI-MCP in Claude einbinden
├─ tools-registry.json      # maschinenlesbares Aufgabe→Tool-Routing
├─ TOOLS.md                 # Harmonisierung mit ULTRA Enterprise OS
└─ README.md
```

**Installations-Workspace** (Standard): `%USERPROFILE%\KI-Agentur`
(überschreibbar via `.\install.ps1 -Root D:\KI-Agentur`).
Dort liegen `repos/`, `logs/`, `config/`, `metabase/`, `n8n-data/`.

---

## Dienste & URLs

| Tool | URL |
|---|---|
| ComfyUI | http://127.0.0.1:8188 |
| ComfyUI MCP | http://127.0.0.1:9000/mcp |
| n8n | http://127.0.0.1:5678 |
| Metabase | http://127.0.0.1:3000 (Erststart 1–2 Min.) |
| OmniRoute | http://127.0.0.1:20128 (API: `/v1`) |
| bolt.diy | http://localhost:5173 |

---

## Konfiguration / API-Keys

1. `config\.env.example` → nach `config\.env` kopieren und Keys eintragen.
2. Empfehlung: **OmniRoute** als zentrales Gateway starten; andere Tools nutzen
   dann `http://localhost:20128/v1` (Modell `auto`) statt einzelner Provider-Keys.
3. **ComfyUI-MCP in Claude Code einbinden**: `config\claude-mcp-config.example.json`
   als Vorlage nehmen (Pfade anpassen). Der Installer schreibt zusätzlich eine
   fertige Version nach `%USERPROFILE%\KI-Agentur\config\claude-mcp-config.json`.

> 🔐 Echte Keys **niemals** committen. `.env` ist bereits in `.gitignore`.

---

## Integration mit dem ULTRA Enterprise OS

`TOOLS.md` + `tools-registry.json` verbinden jedes Tool mit einem verantwortlichen
`ultra-*`-Agenten. Der **Boss** (`ultra-orchestrator`) wählt pro Aufgabe automatisch
das passende Werkzeug (z. B. ComfyUI für Produktbilder, browser-use für Tests,
n8n für Automatisierung). Details und End-to-End-Workflows: siehe **TOOLS.md**.

---

## Fehlerbehebung

- **Befehl nicht gefunden** nach der Installation → neues Terminal öffnen (PATH),
  nach Docker/Build-Tools ggf. Windows neu starten.
- **ComfyUI langsam / kein Bild** → ohne NVIDIA-GPU läuft PyTorch im CPU-Modus.
  Für echte Geschwindigkeit NVIDIA-GPU + aktuelle Treiber. Modelle nach
  `repos\ComfyUI\models\checkpoints` legen.
- **ComfyUI-MCP verbindet nicht** → zuerst ComfyUI starten, dann den MCP-Server.
- **Metabase startet nicht** → Java 21 prüfen (`java -version`); Erststart dauert.
- **Docker-Tools** (n8n/OmniRoute-Alternative) → Docker Desktop muss laufen.
- Logs: `%USERPROFILE%\KI-Agentur\logs\install.log`.
