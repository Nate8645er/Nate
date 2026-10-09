"""Sicherheits-Modul: periodischer Schutz-Check über die Windows-Bordmittel.

Ehrlich eingeordnet: Eine Python-App ist KEIN eigener Virenscanner und keine
Firewall. Der wirksame und ehrliche Weg ist, die bereits vorhandenen, starken
Windows-Schutzmechanismen zu orchestrieren und zu überwachen:

  - Microsoft Defender (Antivirus, Echtzeitschutz, Bedrohungserkennung)
  - Windows-Firewall
  - Windows-/Signatur-Updates

Der SecurityMonitor läuft alle 30 Minuten und:
  1. prüft Defender-Status, Echtzeitschutz, Firewall, gefundene Bedrohungen,
  2. aktualisiert die Virensignaturen (sicher, schnell),
  3. meldet Probleme als ALARM (Dashboard + Log).

Aktives Eingreifen (kompletter Scan starten) läuft über Defender und braucht
die PC-Freischaltung (JARVIS_ALLOW_PC=1). „Sofort auf Hacker/Viren reagieren"
heißt: Defender erkennt/blockt in Echtzeit, JARVIS überwacht, alarmiert und
kann einen Scan/eine Signaturaktualisierung auslösen — kein magischer
Eigen-Virenschutz.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from collections import deque
from typing import Any

from .plugins import Plugin, dangerous_allowed

# PowerShell-Skript sammelt den Sicherheitsstatus als JSON (nur Windows).
_PS_CHECK = r"""
$o = [ordered]@{}
try {
  $s = Get-MpComputerStatus
  $o.defender_an = [bool]$s.AntivirusEnabled
  $o.echtzeitschutz = [bool]$s.RealTimeProtectionEnabled
  $o.signatur_alter_tage = [int]((Get-Date) - $s.AntivirusSignatureLastUpdated).TotalDays
} catch { $o.defender_fehler = "$($_.Exception.Message)" }
try {
  $t = @(Get-MpThreatDetection -ErrorAction SilentlyContinue)
  $o.bedrohungen = $t.Count
  $o.bedrohung_namen = @($t | ForEach-Object { $_.ThreatID } | Select-Object -First 5)
} catch { $o.bedrohungen = 0 }
try {
  $fw = Get-NetFirewallProfile -ErrorAction SilentlyContinue
  $o.firewall_alle_an = ((@($fw | Where-Object { -not $_.Enabled }).Count) -eq 0)
} catch { $o.firewall_fehler = "$($_.Exception.Message)" }
$o | ConvertTo-Json -Compress
"""


def _pwsh(script: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
        capture_output=True, text=True, timeout=timeout)


class SecurityPlugin(Plugin):
    name = "security"
    description = ("Sicherheits-Check: Defender-Status, Firewall, Bedrohungen, "
                  "Signaturen aktualisieren, Scan starten")
    allowed_teams = ["Führung", "Cybersecurity", "DevOps", "Automatisierung",
                     "Qualitätsmanagement"]

    def _require_pc(self) -> str | None:
        if os.environ.get("JARVIS_ALLOW_PC") == "1" or dangerous_allowed():
            return None
        return ("Aktion gesperrt (greift ins System ein). Zum Freischalten "
                "JARVIS_ALLOW_PC=1 setzen und neu starten.")

    def check(self) -> dict[str, Any]:
        """Read-only Sicherheitsstatus (immer erlaubt)."""
        if os.name != "nt":
            import psutil
            vm = psutil.virtual_memory()
            top = sorted(psutil.process_iter(["name", "cpu_percent"]),
                         key=lambda p: p.info.get("cpu_percent") or 0, reverse=True)[:5]
            return {"plattform": "nicht-windows",
                    "hinweis": "Defender/Firewall-Prüfung nur auf Windows verfügbar.",
                    "ram_prozent": vm.percent,
                    "top_prozesse": [p.info.get("name") for p in top],
                    "zeit": time.strftime("%Y-%m-%d %H:%M:%S")}
        try:
            r = _pwsh(_PS_CHECK)
            data = json.loads(r.stdout.strip() or "{}")
        except Exception as e:
            return {"fehler": f"Statusabfrage fehlgeschlagen: {type(e).__name__}",
                    "zeit": time.strftime("%Y-%m-%d %H:%M:%S")}
        data["zeit"] = time.strftime("%Y-%m-%d %H:%M:%S")
        # Bewertung
        probleme = []
        if data.get("defender_an") is False:
            probleme.append("Defender ist AUS")
        if data.get("echtzeitschutz") is False:
            probleme.append("Echtzeitschutz ist AUS")
        if data.get("firewall_alle_an") is False:
            probleme.append("Firewall-Profil deaktiviert")
        if (data.get("bedrohungen") or 0) > 0:
            probleme.append(f"{data['bedrohungen']} Bedrohung(en) erkannt")
        if (data.get("signatur_alter_tage") or 0) > 3:
            probleme.append(f"Virensignaturen {data['signatur_alter_tage']} Tage alt")
        data["probleme"] = probleme
        data["status"] = "alarm" if probleme else "sicher"
        return data

    def run(self, action: str = "check", **kwargs: Any) -> Any:
        if action == "check":
            return self.check()
        if os.name != "nt":
            return "Diese Aktion braucht Windows (Defender)."
        gate = self._require_pc()
        if action == "signatures":
            if gate:
                return gate
            r = _pwsh("Update-MpSignature; 'Virensignaturen aktualisiert.'")
            return (r.stdout or r.stderr).strip()
        if action == "scan":
            if gate:
                return gate
            r = _pwsh("Start-MpScan -ScanType QuickScan; 'Quick-Scan gestartet.'", timeout=15)
            return (r.stdout or r.stderr).strip() or "Quick-Scan gestartet."
        if action == "update":
            if gate:
                return gate
            # Windows-Update-Suche anstoßen (installiert nichts ohne dein Zutun)
            _pwsh("Start-Process -WindowStyle Hidden UsoClient StartScan", timeout=15)
            return "Windows-Update-Suche angestoßen (Installation nur mit deiner Bestätigung)."
        if action == "threats":
            # Von Microsoft Defender gemeldete Bedrohungen abrufen
            r = _pwsh("Get-MpThreat | Select-Object ThreatName,SeverityID | "
                      "ConvertTo-Json -Compress")
            out = (r.stdout or "").strip()
            return out or "Keine von Defender gemeldeten Bedrohungen."
        if action == "fullscan":
            if gate:
                return gate
            _pwsh("Start-MpScan -ScanType FullScan", timeout=15)
            return "Defender-Vollscan gestartet."
        if action == "remove":
            if gate:
                return gate
            # Defender die erkannten Bedrohungen entfernen/in Quarantäne schieben lassen
            r = _pwsh("Remove-MpThreat; 'Defender: erkannte Bedrohungen entfernt/quarantäniert.'")
            return (r.stdout or r.stderr).strip() or "Defender: Bedrohungsentfernung ausgelöst."
        raise ValueError("Unbekannte Aktion: "
                         "check|signatures|scan|fullscan|update|threats|remove")


class BodyguardSquad:
    """24/7-Wächter: benannte Bodyguard-Agenten patrouillieren im Kurztakt,
    beheben sichere Probleme automatisch und alarmieren bei Bedrohungen.

    Ehrlich: Das echte Erkennen/Blocken von Viren & Angriffen leistet Microsoft
    Defender in Echtzeit. Die Wächter kontrollieren laufend, halten den Schutz
    scharf (Firewall/Echtzeitschutz reaktivieren, Signaturen aktuell) und lösen
    bei einer Bedrohung sofort einen Defender-Scan aus.
    """

    GUARDS = [
        ("Titan Vega-01", "DEFENDER"),
        ("Rex Stein-02", "FIREWALL"),
        ("Nova Falk-03", "PROZESSE"),
        ("Atlas Kern-04", "SIGNATUREN"),
        ("Orion Wolf-05", "NETZWERK"),
        ("Vega Sturm-06", "UPDATES"),
    ]

    def __init__(self, plugin: SecurityPlugin, interval_s: int = 300) -> None:
        self.plugin = plugin
        self.interval = max(30, interval_s)
        self.on = False
        self.patrols = 0
        self.last_findings: list[str] = []
        self.last_fixes: list[str] = []
        self.last_patrol = "–"
        self.guards = [{"name": n, "posten": p, "status": "bereit"} for n, p in self.GUARDS]
        self._thread: threading.Thread | None = None
        self._gen = 0
        self._log = None

    def set_logger(self, fn: Any) -> None:
        self._log = fn

    def _may_act(self) -> bool:
        return os.name == "nt" and (
            os.environ.get("JARVIS_ALLOW_PC") == "1" or dangerous_allowed())

    def _remediate(self, report: dict[str, Any]) -> list[str]:
        """Sichere Selbstheilung — nur bei echten Problemen und mit Freischaltung."""
        fixes: list[str] = []
        if not self._may_act():
            return fixes
        try:
            if report.get("echtzeitschutz") is False:
                _pwsh("Set-MpPreference -DisableRealtimeMonitoring $false")
                fixes.append("Echtzeitschutz reaktiviert")
            if report.get("firewall_alle_an") is False:
                _pwsh("Set-NetFirewallProfile -All -Enabled True")
                fixes.append("Firewall reaktiviert")
            if (report.get("signatur_alter_tage") or 0) > 1:
                _pwsh("Update-MpSignature")
                fixes.append("Virensignaturen aktualisiert")
            if (report.get("bedrohungen") or 0) > 0:
                # Als Defender-Assistent: scannen UND Defender die Bedrohung entfernen lassen
                _pwsh("Start-MpScan -ScanType QuickScan", timeout=15)
                _pwsh("Remove-MpThreat")
                fixes.append("Defender-Scan + Bedrohungsentfernung ausgelöst")
        except Exception:
            pass
        return fixes

    def _patrol(self) -> None:
        report = self.plugin.check()
        self.patrols += 1
        self.last_patrol = report.get("zeit", "–")
        probleme = report.get("probleme", []) if isinstance(report, dict) else []
        self.last_findings = probleme
        # EHRLICH: Ohne Windows kann kein Posten (Defender/Firewall/…) real geprüft
        # werden — dann nicht fälschlich "WACHSAM" melden, sondern "NUR WINDOWS".
        if report.get("plattform") == "nicht-windows":
            for g in self.guards:
                g["status"] = "NUR WINDOWS"
            self.last_fixes = []
            if self._log:
                self._log("info", "Bodyguards bereit — Defender/Firewall-Prüfung nur auf Windows aktiv")
            return
        # Posten-Status je Wächter setzen
        def post_ok(posten: str) -> bool:
            if posten == "DEFENDER":
                return report.get("defender_an") is not False and report.get("echtzeitschutz") is not False
            if posten == "FIREWALL":
                return report.get("firewall_alle_an") is not False
            if posten == "SIGNATUREN":
                return (report.get("signatur_alter_tage") or 0) <= 3
            if posten in ("PROZESSE", "NETZWERK"):
                return (report.get("bedrohungen") or 0) == 0
            return True
        for g in self.guards:
            g["status"] = "WACHSAM" if post_ok(g["posten"]) else "ALARM"
        # Selbstheilung
        self.last_fixes = self._remediate(report) if probleme else []
        if self._log:
            if probleme:
                self._log("warn", "BODYGUARD-ALARM: " + "; ".join(probleme)
                          + (" | behoben: " + "; ".join(self.last_fixes) if self.last_fixes else ""))
            else:
                self._log("info", "Bodyguard-Patrouille ok")

    def _run(self, gen: int) -> None:
        while self.on and gen == self._gen:
            try:
                self._patrol()
            except Exception:
                pass
            for _ in range(self.interval):
                if not self.on or gen != self._gen:
                    return
                time.sleep(1)

    def start(self) -> None:
        if self.on:
            return
        self.on = True
        self._gen += 1
        gen = self._gen
        self._thread = threading.Thread(target=self._run, args=(gen,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.on = False
        self._gen += 1
        self._thread = None

    def stats(self) -> dict[str, Any]:
        return {
            "aktiv": self.on,
            "anzahl": len(self.guards),
            "assistiert": "Microsoft Defender",
            "intervall_min": round(self.interval / 60, 1),
            "patrouillen": self.patrols,
            "letzte_patrouille": self.last_patrol,
            "letzte_funde": self.last_findings,
            "letzte_fixes": self.last_fixes,
            "selbstheilung": "aktiv" if self._may_act() else "nur melden (JARVIS_ALLOW_PC=0)",
            "waechter": self.guards,
        }


class SecurityMonitor:
    """Läuft alle 30 Minuten: Check + Signaturen aktualisieren + Alarm bei Problemen."""

    def __init__(self, plugin: SecurityPlugin, interval_s: int = 1800) -> None:
        self.plugin = plugin
        self.interval = max(60, interval_s)
        self.on = False
        self.reports: deque[dict[str, Any]] = deque(maxlen=48)  # ~24h Historie
        self.last: dict[str, Any] = {}
        self.checks = 0
        self._thread: threading.Thread | None = None
        self._gen = 0
        self._log = None

    def set_logger(self, fn: Any) -> None:
        self._log = fn

    def _run(self, gen: int) -> None:
        while self.on and gen == self._gen:
            report = self.plugin.check()
            self.checks += 1
            self.last = report
            self.reports.appendleft(report)
            if self._log:
                if report.get("status") == "alarm":
                    self._log("warn", "SICHERHEITS-ALARM: " + "; ".join(report.get("probleme", [])))
                elif report.get("plattform") == "nicht-windows":
                    self._log("info", "Sicherheits-Monitor bereit — Defender-Check nur auf Windows")
                elif report.get("status") == "sicher":
                    self._log("info", "Sicherheits-Check ok")
                else:
                    self._log("info", "Sicherheits-Check abgeschlossen")
            # Signaturen sicher aktualisieren (nur Windows, best effort)
            if os.name == "nt":
                try:
                    self.plugin.run("signatures")
                except Exception:
                    pass
            for _ in range(self.interval):
                if not self.on or gen != self._gen:
                    return
                time.sleep(1)

    def start(self) -> None:
        if self.on:
            return
        self.on = True
        self._gen += 1
        gen = self._gen
        self._thread = threading.Thread(target=self._run, args=(gen,), daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self.on = False
        self._gen += 1
        self._thread = None

    def stats(self) -> dict[str, Any]:
        return {
            "laeuft": self.on,
            "intervall_min": self.interval // 60,
            "checks_gesamt": self.checks,
            "letzter_status": self.last.get("status", "–"),
            "letzte_probleme": self.last.get("probleme", []),
            "letzter_check": self.last.get("zeit", "–"),
            "letzter_bericht": self.last,
            "verlauf": list(self.reports)[:12],
        }
