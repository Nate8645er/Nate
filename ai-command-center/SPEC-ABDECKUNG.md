# Spezifikations-Abdeckung: Unternehmens-KI (1:1-Matrix)

Jede Zeile der Kunden-Spezifikation, ehrlich eingeordnet:
**LIVE** = heute im Produkt nutzbar. **ENTERPRISE** = wird pro Kunde als
bezahltes Projekt eingerichtet (braucht Zugänge/Freigaben des Kunden --
das ist die Leistung ab 8'900 CHF/Monat, kein Mangel).

## Kernfunktionen
| Anforderung | Status | Wo |
|---|---|---|
| Verbindung mit ERP/CRM/Buchhaltung/E-Mail/Kalender/Cloud | ENTERPRISE | Integration-Center (/integrationen), Adapter-Architektur steht |
| Analyse von Unternehmensdaten | LIVE | Datei anhängen (Kommando + Dashboard), /prognose, /preise |
| Automatisierung wiederkehrender Aufgaben | LIVE | Autopilot (/workflows); 24/7-Serverbetrieb: ENTERPRISE |
| Berichte, Auswertungen, Dashboards | LIVE | /berichte, /analysen, /wochenbericht |
| Kundensupport durch KI | LIVE | /support-Skill (FAQ + Antwort-Vorlagen); Live-Chatbot im Kundensystem: ENTERPRISE |
| Dokumentenanalyse + Zusammenfassungen | LIVE | PDF/TXT/MD/CSV/HTML-Anhang, /kontrolle |
| Intelligente Suche über Unternehmensdaten | LIVE (Arbeitsdaten) | Suche in /berichte; Suche in Fremdsystemen: ENTERPRISE |
| Terminplanung + Workflow-Automatisierung | LIVE | /termine-Skill, Autopilot; Kalender-Sync: ENTERPRISE |
| Vertrieb, Marketing, HR, Finanzen | LIVE | 19 Skills in 4 Kategorien (/faehigkeiten) |
| Mehrsprachige Kommunikation | LIVE | /uebersetzen-Skill, Aufträge in jeder Sprache |

## Technische Anforderungen
| Anforderung | Status | Wo |
|---|---|---|
| Benutzeranmeldung mit Rollen | LIVE (Basis) | /benutzer (Admin/Manager/Mitarbeiter) + Lizenz; SSO/2FA zentral: ENTERPRISE |
| API-Schnittstellen | LIVE | 6 dokumentierte API-Routen; Kunden-APIs anbinden: ENTERPRISE |
| Cloud- und On-Premise-Betrieb | LIVE (Cloud/Vercel) | On-Premise: ENTERPRISE (ARCHITEKTUR-ENTERPRISE.md) |
| Verschlüsselte Datenspeicherung | LIVE | HTTPS überall; Arbeitsdaten bleiben im Browser des Kunden (Datenminimierung) |
| DSGVO-konform | LIVE (Basis) | Keine serverseitige Speicherung von Kundendaten, Export + Löschen in /einstellungen; AVV/EU-Hosting: ENTERPRISE |
| Modulare Architektur | LIVE | Skills, Connectors, Agenten-Rollen -- neue Module ohne Kern-Umbau |
| Skalierbarkeit | LIVE | Stateless auf Vercel (horizontal skalierend), Limits pro Plan |

## KI-Funktionen
| Anforderung | Status | Wo |
|---|---|---|
| Sprachmodell für Konversationen | LIVE | 3 Anbieter mit Fallback-Kette |
| Dokumentenverständnis PDF/Word/Excel | LIVE | PDF direkt; Word/Excel als PDF/CSV (steht im UI); Bilder: ENTERPRISE |
| Automatische Datenanalyse | LIVE | Datei-Anhang -> Analyse-Mission |
| Prognosen und Vorhersagen | LIVE | /prognose-Skill (3 Szenarien) |
| Individuelle Empfehlungen | LIVE | Branchen-Onboarding fliesst in jede Mission |
| Eigenständige Agenten | LIVE | Commander -> Worker -> Quality; Org-Modus bis 1000 |
| Lernfähig / passt sich an | LIVE (Basis) | Unternehmensprofil + Verlauf; echtes Firmen-Gedächtnis (RAG): ENTERPRISE |

## Benutzeroberfläche (alle 7 gefordert -- alle 7 vorhanden)
| Gefordert | Seite |
|---|---|
| Übersicht Unternehmensdaten | /analysen + /berichte |
| KI-Chat für Mitarbeiter | /chat (Kommandozentrale: führt aus statt nur zu antworten) |
| Workflow-Manager | /workflows (Autopilot) |
| Analyse-/Statistikbereich | /analysen |
| Benutzerverwaltung | /benutzer |
| Integrationsverwaltung | /integrationen |
| Einstellungsbereich | /einstellungen |

## Integrationen (M365, Google, Salesforce, SAP, ...)
Alle 15 im Integration-Center katalogisiert (Adapter-Muster). Live-Anbindung
erfordert die OAuth-Freigabe im System des Kunden -> pro Kunde als
Enterprise-Projekt (deshalb "Verfügbar auf Anfrage"). Ohne diese Freigabe
kann KEIN Anbieter der Welt auf Firmendaten zugreifen -- das ist Sicherheit.
