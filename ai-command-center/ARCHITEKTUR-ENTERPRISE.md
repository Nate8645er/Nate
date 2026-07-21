# AI Command Center: Enterprise-Architektur (ehrliche Roadmap)

Dieses Dokument beschreibt, wie die Plattform zur vollen Unternehmens-KI
ausgebaut wird. Es trennt klar: WAS HEUTE LAEUFT, WAS MODULAR VORBEREITET
ist, und WAS ECHTES INTEGRATIONS-PROJEKT pro Kunde ist (Enterprise-Umsatz).

## 1. Heute produktiv
- Multi-Agent-Orchestrierung (Commander -> Worker -> Quality -> Synthese).
- Org-Modus: dynamische Firma mit Abteilungen + Belegschaft (bis 1000).
- Lizenz-/Plan-System mit Tageslimits, Branchen-Onboarding.
- Echte Datei-/Code-Ausgabe (Artifact-Event): Missionen liefern lauffaehige
  Dateien mit Vorschau + Download (Landingpage, Script, UI-Prototyp).
- Demo-Fallback, Timeouts, Security-Haertung (HMAC-Lizenzen, Injection-Schutz).

## 2. Modular vorbereitet (Framework steht, Umsetzung pro Connector)
### Integration-Center (Adapter-Muster)
Jede externe Software wird als Modul mit einheitlicher Schnittstelle angebunden:

    interface Connector {
      id: string;                 // "microsoft365", "salesforce", ...
      auth(): Promise<OAuthResult>;   // OAuth 2.0 des jeweiligen Anbieters
      read(query): Promise<Data>;     // Lesen (Mails, Kontakte, Belege ...)
      write(action): Promise<Result>; // Schreiben (Termin, Datensatz ...)
    }

Neue Integrationen = neues Modul, kein Umbau des Kerns.

### Connector-Katalog (Ziel)
Microsoft 365, Google Workspace, Salesforce, SAP, HubSpot, Slack,
MS Teams, Dropbox, OneDrive, AWS, Azure, Stripe, Shopify, WooCommerce,
plus generischer REST/Webhook-Connector fuer eigene Firmen-APIs.

### Warum je Kunde eingerichtet
Jede Firma muss der KI in ihrem eigenen Admin (z.B. Microsoft/Salesforce)
per OAuth Zugriff GEBEN. Das ist Sicherheit, kein Mangel: niemand kann
ohne diese Freigabe an Firmendaten. Genau das ist die Enterprise-Leistung.

## 3. Enterprise-Projekt pro Kunde (Umsatz ab 10'000/Monat)
- OAuth-App-Registrierung im Kundensystem, Rollen/Rechte-Mapping.
- Anbindung ERP/CRM/Buchhaltung an konkrete Kundenschemata.
- On-Premise- oder Private-Cloud-Betrieb, verschluesselte Datenhaltung.
- DSGVO: Auftragsverarbeitungsvertrag, Loeschkonzept, EU-Hosting.
- Individuelle Agenten/Workflows fuer die Firma.

## 4. Sicherheit & Compliance (Bauplan)
- Auth: Rollen (Admin/Manager/Mitarbeiter), 2FA, Session-Management.
- Verschluesselung ruhend + in Transit; Secrets in Vault/KMS.
- Audit-Logs je Aktion; Rate-Limiting; Mandantentrennung (Multi-Tenant).
- DSGVO-konforme Speicherung, EU-Region, Datenminimierung.

## 5. Skalierung (Bauplan)
- Stateless App auf Vercel/Cloud, horizontale Skalierung.
- Warteschlangen (Redis/Temporal) fuer lange Agenten-Jobs.
- Vektor-DB (Chroma/Qdrant) fuer Firmenwissen (RAG), pro Mandant getrennt.
- Kosten-/Nutzungs-Tracking je Kunde.

## 6. Naechste konkrete Bau-Schritte (in dieser Reihenfolge)
1. Artifact-Ausgabe fertig (laeuft): echte Dateien + Vorschau + Download.
2. Integration-Center-UI: Connector-Katalog mit Status + OAuth-Flow-Stub.
3. Dokumenten-KI: PDF/Word/Excel hochladen -> Zusammenfassung/Analyse
   (RAG via LlamaIndex + Chroma, bereits installiert).
4. Ein echter Referenz-Connector (z.B. Shopify oder Stripe) als Vorzeige-Fall.
5. Auth + Multi-Tenant (NextAuth + Postgres) fuer echte Firmenkonten.

Ehrlich: Punkte 1-3 sind Software, die ich hier baue. Punkte 4-5 und die
Live-Anbindung an SAP/Salesforce/M365 brauchen Kunden-Zugaenge und werden
pro Kunde als Enterprise-Projekt umgesetzt.
