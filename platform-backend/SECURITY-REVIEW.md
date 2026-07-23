# Security-Review — platform-backend (Phase 8)

**Rahmen:** rein defensiver Review vor Auslieferung sicherheitsrelevanter
Änderungen (CLAUDE.md-Regel). Ehrlich: nur Befunde, die im Code wirklich stehen.

**Methodik:**
- Manueller Review der sicherheitskritischen Pfade (Auth, RBAC, Tenancy,
  Injection, Secrets, Deserialisierung, Subprozesse).
- Automatisch: `bandit -r app` (Python-SAST) + `ruff` mit `flake8-bugbear`.
- `gitleaks`/`semgrep` waren in dieser Umgebung nicht installiert — daher der
  manuelle Secrets-Review + die testgestützte Prüfung „keine Klartext-Secrets in
  den k8s-Manifesten" (`tests/test_k8s_manifests.py`).

## Automatischer Scan (bandit)
`Total issues — High: 0, Medium: 0, Low: 9.` Alle 9 Low-Befunde sind
`B404`/`B603` (Nutzung des `subprocess`-Moduls) an drei bewusst geprüften
Stellen: `compute/hal.py` (nvidia-smi), `platform/backup.py` (pg_dump/pg_restore),
`integrations/mcp_client.py` (StdioTransport). Alle mit **fester Argumentliste,
`shell=False`, ohne End-User-Eingabe in `argv`**. Kein Handlungsbedarf; siehe
Kontext unten.

## Manuelle Befunde

### MEDIUM-1 — Keycloak-Audience in Produktion setzen
`platform/auth.py`: Ist `OidcConfig.audience is None`, wird `verify_aud=False`.
Dann würde ein im selben Realm für einen ANDEREN Client ausgestelltes Token
akzeptiert. Signatur/Issuer/Ablauf werden weiterhin geprüft, aber die Zielgruppe
nicht. **Fix/Betrieb:** In Produktion immer die `audience` (client_id) setzen.
*(Bewusst optional gehalten; hier als Deployment-Pflicht markiert.)*

### MEDIUM-2 — RLS erfordert unprivilegierte DB-Rolle (operativ)
Die Mandantentrennung auf DB-Ebene (Postgres RLS) greift **nicht**, wenn die
App-Verbindung als Superuser oder mit `BYPASSRLS` läuft (live verifiziert, siehe
`docs/plattform-ausbau/VERIFIKATION-LIVE-DIENSTE.md`). **Fix/Betrieb:** Die in
`DATABASE_URL` genutzte Rolle MUSS `NOBYPASSRLS` und Nicht-Superuser sein. Im
k8s-Secret-Manifest ist das als Kommentar hinterlegt; gehört in die
Deploy-Checkliste. Code-Ebene (`TenantRepository`) schützt zusätzlich.

### LOW-1 — MCP-Server-Kommandos nur vom Betreiber
`integrations/mcp_client.py` `StdioTransport(argv)` startet einen Subprozess mit
`argv`. Das ist sicher, solange `argv` aus der Betreiber-Konfiguration stammt.
**Regel:** MCP-Server-Kommandos NIE aus Tenant-/End-User-Eingaben bauen (sonst
Command-Injection). Aktuell nicht der Fall.

## Verifiziert sicher (positiv)
- **JWT/Auth:** `algorithms=["RS256"]` fest → `alg=none` und HS/RS-Confusion
  ausgeschlossen; `require=["exp","iat"]`, Issuer erzwungen; Fehler werfen
  `TokenError` (nie leise durchlassen). Der unverifizierte Header wird nur zur
  `kid`-Auswahl gelesen — die Signatur wird trotzdem geprüft.
- **RBAC:** Default-Deny. `permissions_of` startet leer; unbekannte Rolle → keine
  Rechte; `require` wirft `PermissionDenied`.
- **Mandantentrennung:** Jeder Lesepfad im VectorStore (`InMemory` und `Qdrant`)
  verlangt einen `tenant` und filtert darauf; live gegen echten Qdrant + echte
  Postgres-RLS bewiesen.
- **Injection:** Kein `eval`/`exec`/`pickle`/`yaml.load`/`shell=True`/
  `verify=False` im `app/`-Baum. SQL ausschließlich über SQLAlchemy-Parameter.
- **Secrets:** Kommen nur aus der Umgebung (`config.py`), nie hartcodiert/geloggt.
  Backup redigiert die DSN (`redact_dsn`), Passwörter gehen via `PGPASSWORD`-Env,
  nie in `argv` (Prozessliste). k8s-Manifeste enthalten testgeprüft keine
  Klartext-Secrets.
- **DoS/Ressourcen:** Agenten haben harte Limits (Schritte/Budget/Tiefe);
  Subprozesse haben Timeouts; k8s-Deployment setzt CPU/Memory-Limits + PDB.

## Fazit
Keine High/Medium-Code-Schwachstellen gefunden. Die beiden MEDIUM-Punkte sind
**Betriebs-/Konfigurationspflichten** (Audience setzen, DB-Rolle `NOBYPASSRLS`),
nicht Code-Fehler. Empfehlung: bandit + ruff in die CI aufnehmen (blockierend).
