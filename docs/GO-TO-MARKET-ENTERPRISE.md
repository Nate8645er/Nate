# Go-to-Market — Enterprise / On-Premise-KI

Positionierung des neuen `platform-backend` als verkaufbare Enterprise-Schicht.
**Kein Live-Shop wird hier geändert** — dies ist die Argumentations- und
Angebots-Grundlage; Preise/Texte im Shop bleiben, bis sie bewusst freigegeben
werden. Der bestehende Enterprise-Tarif (`lib/preise.ts`, CHF 790/Mt.) verspricht
bereits „Private Cloud oder On-Premise, eigene Modelle" — die Plattform löst
dieses Versprechen jetzt technisch ein.

## Zielkunde (ICP)
Mittelstand/Konzern in regulierten oder datensensiblen Branchen (Gesundheit,
Recht, Finanzen, Industrie, öffentliche Hand) im DACH-Raum, der KI will, aber
**Daten nicht in fremde Clouds geben darf/will**.

## Kernbotschaft
> „Ihre KI-Abteilung — im eigenen Haus. Datenhoheit, Mandantentrennung und
> Nachvollziehbarkeit, ohne dass ein einziges Dokument Ihr Netz verlässt."

## Differenzierung (Wettbewerb: SaaS-KI-Tools)
| Bedürfnis des Kunden | Übliche SaaS-Tools | Unsere Plattform |
|---|---|---|
| Daten bleiben im Haus | Cloud-only | **`local_only`**-Routing bindet Daten hart lokal (verifiziert) |
| Keine fremden Modell-Keys | Anbieter-Lock-in | Eigene lokale Modelle (Ollama/vLLM), Cloud optional |
| Mehrere Abteilungen/Kunden getrennt | oft nur logisch | **Postgres-RLS auf DB-Ebene** (live bewiesen) |
| Wer durfte was? | begrenzt | **RBAC Default-Deny + Append-only Audit** |
| Betreibbar & prüfbar | Blackbox | Prometheus-Metriken, Health/Readiness, k8s-Manifeste |

## Beweisbare Leistungsversprechen (keine Behauptungen — real getestet)
Jedes Versprechen ist durch einen ausführbaren Test/Live-Lauf gedeckt
(siehe `docs/plattform-ausbau/VERIFIKATION-LIVE-DIENSTE.md`, `SECURITY-REVIEW.md`,
`CUTOVER.md`):
1. **„Ihre Daten verlassen das Haus nicht."** — `data_class=local_only` erzwingt
   lokale Ausführung; Router-Entscheidung live geprüft.
2. **„Kunde A sieht nie Daten von Kunde B."** — Postgres-RLS blockt Cross-Tenant
   auf DB-Ebene; Qdrant-Suche mandantengetrennt — beides gegen echte Server bewiesen.
3. **„Echte KI im eigenen Rechenzentrum."** — lokale Inferenz über
   ModelRouter→LiteLLM→Ollama live gelaufen (CPU, ohne Cloud).
4. **„Sicherer Zugang."** — echte Keycloak-Token-Kette (JWKS-Signaturprüfung →
   Principal → RBAC) end-to-end verifiziert.
5. **„Betreibbar & nachvollziehbar."** — /metrics, /health/ready, Backup/Restore,
   k8s-Manifeste, Security-Review (bandit 0 High/0 Medium).

## Angebots-Bausteine (Vorschlag, nicht im Shop aktiviert)
- **Enterprise Cloud** (bestehend, 790/Mt.): gehostet, Mandant isoliert.
- **On-Premise / Private** (Projektpreis): Installation im Kundennetz
  (Docker Compose → k3s), Keycloak-Anbindung ans Firmen-SSO, eigene Modelle.
  Einrichtung + Schulung + SLA als Dienstleistung.
- **Add-ons:** ERP/CRM-Integration, dedizierte GPU, Compliance-Report (Audit-Export).

## Verkaufsprozess
Kein Self-Checkout — „Kontakt aufnehmen" (bereits so im Enterprise-CTA). Ablauf:
Demo (v2-Dashboard mit echten Live-Kennzahlen) → Pilot im Kundennetz (1 Abteilung)
→ Rollout gemäss `CUTOVER.md` (flag-gestuft, umkehrbar).

## Nächste vertriebsfähige Schritte (kein Shop-Eingriff ohne Freigabe)
- Eine Enterprise-Landing-Section, die die 5 Beweispunkte oben zeigt (v2-Stil).
- Ein 2-seitiges PDF-One-Pager aus diesem Dokument für den Erstkontakt.
- Demo-Skript für die 20-Minuten-Vorführung (Datenhoheit + Mandantentrennung live).
