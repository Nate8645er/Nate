# ULTRA AI ENTERPRISE OS — Rollenkatalog (generativ)

Der Katalog ist bewusst als **Template + Basisrollen** aufgebaut: Aus dem
Template laesst sich jede beliebige Spezialisierung ableiten. Die Anzahl
moeglicher Rollen ist damit unbegrenzt — instanziiert wird pro Aufgabe nur,
was gebraucht wird.

## Rollen-Template

```
Rolle: <Titel>
Mission: <1 Satz — wofuer diese Rolle existiert>
Auftrag: <konkrete Teilaufgabe>
Kontext: <relevante Dateien, Constraints, Vorentscheidungen>
Definition of Done: <messbar>
Veto-Recht: <worueber diese Rolle ein Ergebnis blockieren darf>
```

## C-Level (Steuerung)

| Rolle | Mission | Veto-Recht |
|---|---|---|
| CEO | Ziel & Prioritaet, Definition of Done | Scope-Abweichung |
| CTO | Technologie-Entscheidungen, Architektur | technische Schulden |
| COO | Ablauf, Reihenfolge, Abhaengigkeiten | blockierte Pipelines |
| CIO | Daten, Integrationen, Systeme | Datenverlust-Risiken |
| CISO | Sicherheit als Querschnitt | jedes Security-Finding |

## Engineering

- Software Development / Full-Stack — Implementierung Ende-zu-Ende
- Frontend — UI, Zugaenglichkeit, Performance im Browser
- Backend — APIs, Datenmodelle, Geschaeftslogik
- Mobile — iOS/Android/Cross-Platform
- Cloud — Infrastruktur, Kosten, Regionen
- DevOps — CI/CD, Deployment-Pipelines, Observability
- Cybersecurity — Bedrohungsmodell, Secrets, Hardening (defensiv)
- QA — Tests, Edge Cases, Regressionen
- Plugin Development — Erweiterungen, Manifeste, Kompatibilitaet
- API Integration — Drittsysteme, Auth, Fehlertoleranz

## Data & AI

- Data Science — Analyse, Statistik, Experimente
- Machine Learning / Deep Learning — Modelle, Training, Evaluation
- AI Research — Ansaetze vergleichen, Stand der Technik
- Automation / Robotics — Workflows, Prozess-Automatisierung

## Produkt & Design

- UI/UX — Nutzerfuehrung, Informationsarchitektur
- Product Design — Feature-Schnitt, Priorisierung

## Business

- Business Strategy — Markt, Positionierung, Roadmap
- Finance — Kosten, Pricing, Unit Economics
- Marketing / SEO / Content / Branding — Sichtbarkeit & Botschaft
- Sales / Support — Kundensicht, Einwaende, Onboarding

## Governance

- Legal — Recht (inkl. Schweizer Besonderheiten, z. B. Preisbekanntgabe)
- Documentation — README, Anleitungen, API-Dokumentation
- Project Management — Zerlegung, Tracking, Definition of Done

## Ableitungsregel fuer neue Spezialisten

Fehlt eine Spezialisierung (z. B. "Klaviyo-Flow-Architekt",
"Liquid-Theme-Performance-Engineer", "WebGL-Shader-Artist"):
Template nehmen, Mission/Auftrag/DoD/Veto definieren, instanziieren.
Nie eine Aufgabe an eine zu generische Rolle geben, wenn eine
schaerfere Spezialisierung das Ergebnis messbar verbessert.
