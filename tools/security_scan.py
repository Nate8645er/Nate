#!/usr/bin/env python3
"""Sicherheits-Rundumcheck fuer dieses Repository.

Buendelt die Scanner, die in dieser Umgebung wirklich laufen:
  - detect-secrets : Secrets/Keys im Code (Ersatz fuer gitleaks — die
                     GitHub-Release-Binaries sind hinter dem Proxy nicht
                     erreichbar, detect-secrets leistet dasselbe per pip)
  - pip-audit      : bekannte CVEs in den Python-Abhaengigkeiten
  - npm audit      : bekannte CVEs in den JS-Abhaengigkeiten
  - git-Pruefung   : ist versehentlich eine .env oder ein Key eingecheckt?

Exit-Code 0 = sauber, 1 = Befunde. Damit auch in CI nutzbar.

Nutzung:
    python3 tools/security_scan.py            # alles
    python3 tools/security_scan.py --quick    # nur Secrets + git (schnell)
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: pathlib.Path | None = None) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except FileNotFoundError:
        return 127, f"Werkzeug nicht gefunden: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, f"Zeitueberschreitung: {' '.join(cmd)}"


def check_tracked_secrets() -> list[str]:
    """Kein .env und keine Schluesseldatei darf im Git liegen."""
    findings = []
    rc, out = run(["git", "ls-files"], cwd=ROOT)
    if rc != 0:
        return [f"git ls-files fehlgeschlagen: {out.strip()[:200]}"]
    for line in out.splitlines():
        name = line.strip()
        base = pathlib.PurePath(name).name
        if base == ".env" or base.startswith(".env.") and not base.endswith(".example"):
            findings.append(f"Getrackte Umgebungsdatei im Git: {name}")
        if base.endswith((".pem", ".key", ".p12", ".pfx")):
            findings.append(f"Getrackte Schluesseldatei im Git: {name}")
    return findings


# Bekannte Key-Formate. Gemeinsam genutzt von der aktuellen-Stand-Pruefung
# UND der Historien-Pruefung (siehe unten) — ein Key, der einmal committet
# und spaeter wieder entfernt wurde, bleibt sonst unentdeckt in der Historie.
KEY_PATTERNS = [
    (r"sk-or-v1-[A-Za-z0-9]{32}", "OpenRouter-Key"),
    (r"sk-ant-[A-Za-z0-9_-]{20}", "Anthropic-Key"),
    (r"sk_live_[A-Za-z0-9]{20}", "Stripe-Live-Key"),
    (r"whsec_[A-Za-z0-9]{20}", "Stripe-Webhook-Secret"),
    (r"ghp_[A-Za-z0-9]{30}", "GitHub-Token"),
    (r"AKIA[A-Z0-9]{16}", "AWS-Access-Key"),
]


def check_key_patterns() -> list[str]:
    """Bekannte Key-Formate im AKTUELLEN getrackten Inhalt (nicht nur Dateinamen)."""
    findings = []
    for pat, label in KEY_PATTERNS:
        rc, out = run(["git", "grep", "-nIE", pat], cwd=ROOT)
        if rc == 0 and out.strip():
            for line in out.strip().splitlines()[:5]:
                findings.append(f"{label} im Git-Inhalt: {line[:160]}")
    return findings


def check_key_patterns_in_history() -> list[str]:
    """Dieselben Muster in der Historie DIESES Branches (HEAD), nicht nur im
    aktuellen Stand. `git grep` (oben) saehe einen Key nicht mehr, sobald er
    in einem spaeteren Commit wieder entfernt wurde — er bliebe aber fuer
    jeden, der das Repo klont, in der Historie lesbar. Nutzt `git log
    -S<muster> --pickaxe-regex`, das genau die Commits findet, die die
    Vorkommen-Anzahl eines Musters aendern (also Hinzufuegen ODER Entfernen).

    Bewusst NUR `HEAD`, nicht `--all`: Dieses Repo enthaelt viele parallele
    Branches aus unabhaengigen Sitzungen (JARVIS, Javier Mobile, ...). Mit
    `--all` in einem `fetch-depth: 0`-CI-Checkout meldet der Scan auch Funde
    aus fremden Branches, die dieser PR nicht eingefuehrt hat und die er auch
    nicht rotieren/umschreiben kann (kein Zugriff, keine Verantwortung) — real
    beobachtet mit Commit bb71776 (ein Test-Platzhalter "sk-ant-HIER-DEINEN-
    SCHLUESSEL-EINFUEGEN" auf einem JARVIS-Branch, keine Ahnenschaft zu HEAD,
    kein echter Schluessel). `HEAD` allein findet trotzdem jeden Key, der auf
    DIESEM Branch committet und spaeter wieder entfernt wurde.

    Ein Fund hier ist NICHT durch neuen Code behebbar — nur durch sofortige
    Rotation des Keys beim Anbieter und ggf. History-Rewrite (git filter-repo)
    plus Force-Push, was ausserhalb dieses Skripts eine bewusste, manuelle
    Entscheidung sein muss.
    """
    findings = []
    for pat, label in KEY_PATTERNS:
        rc, out = run(
            ["git", "log", "HEAD", "--oneline", "-S", pat, "--pickaxe-regex"],
            cwd=ROOT,
        )
        if rc == 0 and out.strip():
            commits = out.strip().splitlines()
            findings.append(
                f"{label} in der Git-HISTORIE gefunden ({len(commits)} Commit(s)): "
                f"{commits[0][:100]} — SOFORT beim Anbieter rotieren, unabhaengig "
                f"vom aktuellen Dateistand!"
            )
    return findings


def scan_detect_secrets() -> list[str]:
    if not shutil.which("detect-secrets"):
        return ["detect-secrets nicht installiert (pip install detect-secrets) — uebersprungen"]
    # Ohne --all-files scannt detect-secrets nur GIT-GETRACKTE Dateien —
    # genau richtig: node_modules, out/, .models/ usw. sind gitignored und
    # wuerden den Scan sonst minutenlang blockieren (real gemessen).
    #
    # .secrets.baseline muss ausgeschlossen werden: sie enthaelt die HASHES
    # der bereits geprueften Funde, die detect-secrets sonst selbst wieder als
    # "Hex High Entropy String" meldet. Lokal fiel das zunaechst nicht auf,
    # weil die Datei noch untracked war — in CI (committet) schlug der Scan
    # dann fehl. Deshalb hier explizit ausschliessen statt sich auf den
    # Tracking-Zustand zu verlassen.
    rc, out = run(
        ["detect-secrets", "scan", "--exclude-files", r"^\.secrets\.baseline$"],
        cwd=ROOT,
    )
    if rc != 0:
        return [f"detect-secrets Fehler: {out.strip()[:200]}"]
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return ["detect-secrets lieferte kein gueltiges JSON"]

    # Baseline: bereits gepruefte Falsch-Positive (os.environ-Verweise,
    # Test-Konstanten, CI-Testdatenbank-Passwoerter). Nur NEUE Funde melden —
    # ein Scanner, der jedes Mal dieselben 13 Nicht-Befunde meldet, wird
    # ignoriert und schuetzt dann gar nichts.
    known: set[tuple[str, str]] = set()
    baseline = ROOT / ".secrets.baseline"
    if baseline.is_file():
        try:
            bl = json.loads(baseline.read_text(encoding="utf-8"))
            for path, entries in (bl.get("results") or {}).items():
                for e in entries:
                    known.add((path, e.get("hashed_secret", "")))
        except json.JSONDecodeError:
            return [".secrets.baseline ist kein gueltiges JSON — bitte neu erzeugen"]

    findings = []
    for path, entries in (data.get("results") or {}).items():
        # .env* ist bewusst lokal und gitignored — kein Befund.
        if pathlib.PurePath(path).name.startswith(".env"):
            continue
        for e in entries:
            if (path, e.get("hashed_secret", "")) in known:
                continue  # bereits geprueft und als unkritisch eingestuft
            findings.append(f"{path}:{e.get('line_number')} — {e.get('type')} (NEU)")
    return findings


def scan_pip_audit() -> list[str]:
    if not shutil.which("pip-audit"):
        return ["pip-audit nicht installiert — uebersprungen"]
    findings = []
    for req in sorted(ROOT.rglob("requirements.txt")):
        if "node_modules" in req.parts:
            continue
        rc, out = run(["pip-audit", "-r", str(req)])
        if rc != 0 and "No known vulnerabilities" not in out:
            findings.append(f"{req.relative_to(ROOT)}: {out.strip()[:400]}")
    return findings


def scan_npm_audit() -> list[str]:
    findings = []
    for pkg in sorted(ROOT.rglob("package.json")):
        if "node_modules" in pkg.parts:
            continue
        d = pkg.parent
        if not (d / "node_modules").is_dir():
            findings.append(f"{d.relative_to(ROOT)}: node_modules fehlt — 'npm ci' noetig, uebersprungen")
            continue
        rc, out = run(["npm", "audit", "--audit-level=high"], cwd=d)
        if rc != 0:
            findings.append(f"{d.relative_to(ROOT)}: {out.strip()[:400]}")
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="Nur Secrets + git-Pruefung")
    args = ap.parse_args()

    sections: list[tuple[str, list[str]]] = [
        ("Getrackte Secret-Dateien", check_tracked_secrets()),
        ("Key-Muster im Git-Inhalt (aktueller Stand)", check_key_patterns()),
        ("Key-Muster in der Git-HISTORIE", check_key_patterns_in_history()),
        ("detect-secrets", scan_detect_secrets()),
    ]
    if not args.quick:
        sections += [
            ("pip-audit (Python-CVEs)", scan_pip_audit()),
            ("npm audit (JS-CVEs)", scan_npm_audit()),
        ]

    total = 0
    for title, findings in sections:
        real = [f for f in findings if "uebersprungen" not in f]
        total += len(real)
        status = "OK" if not real else f"{len(real)} BEFUND(E)"
        print(f"\n### {title}: {status}")
        for f in findings:
            print(f"  - {f}")

    print(f"\n{'=' * 60}")
    if total == 0:
        print("Ergebnis: keine Befunde.")
        return 0
    print(f"Ergebnis: {total} Befund(e) — bitte pruefen.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
