# Vertrieb — befundgestützte Direktansprache

**Die Regel, aus der alles folgt:** Wir kontaktieren niemanden, ohne
vorher seine Website geprüft zu haben. Jede Ansprache enthält eine
wahre, überprüfbare Beobachtung über *diese* Firma.

Das ist kein Anstandsgebot, sondern der Grund, warum es funktioniert.
Eine Massennachricht wird weggeklickt. Ein Befund über die eigene Firma
wird gelesen.

---

## Idealkundenprofil

| Merkmal | Trifft zu | Trifft nicht zu |
|---|---|---|
| Grösse | 5–50 Mitarbeitende | unter 3, über 200 |
| Führung | Inhabergeführt | Konzerntochter |
| Leistung | Erklärungsbedürftig, Kunde vergleicht | Laufkundschaft, Impulskauf |
| Kundenwert | Ein Auftrag ≥ CHF 1'500 | Kleinbeträge |
| Bisheriger Kanal | Google, Empfehlung | reine Ausschreibungen |
| Website | Vorhanden, mind. 5 Seiten | keine oder reine Visitenkarte |
| Marketing | Kein eigenes Team | eigene Marketingabteilung |

**Branchen zuerst:** Treuhand und Steuerberatung · Anwaltskanzleien ·
Zahnärzte, Kieferorthopädie, Privatkliniken · Physiotherapie ·
Immobilienverwaltung · Umzug und Reinigung · IT-Dienstleister für KMU ·
Fahrschulen · spezialisierte B2B-Hersteller.

**Warum diese:** Ihre Kunden stellen genau die Fragen, die KI heute
beantwortet. Ein einziger gewonnener Kunde deckt das Audit mehrfach.

---

## Qualifizierung — vier Kriterien, alle prüfbar

Vor jedem Kontakt. Wer weniger als drei erfüllt, wird nicht angerufen.

1. **Technischer Befund unter 70 %** oder mindestens ein
   Antwort-Crawler gesperrt. *(automatisch, `cited.py pruefen`)*
2. **Bei mindestens 3 von 5 Fragen nicht genannt.** *(erfasst)*
3. **Ein Konkurrent wird stattdessen genannt.** *(aus dem Wortlaut)*
4. **Ansprechperson identifizierbar** — Inhaber oder Geschäftsführung,
   namentlich, mit Durchwahl oder Mobilnummer.

**Wer alle vier erfüllt, ist ein A-Lead.** Drei: B. Zwei oder weniger:
nicht anrufen.

---

## Bewertungsschlüssel

| Kriterium | Punkte |
|---|---|
| Antwort-Crawler gesperrt | 30 |
| Technischer Befund unter 50 % | 25 |
| Technischer Befund 50–69 % | 15 |
| Kein lesbarer Inhalt (JavaScript-Seite) | 25 |
| Keine strukturierten Daten | 15 |
| Bei 0 von 5 Fragen genannt | 30 |
| Bei 1–2 von 5 genannt | 15 |
| Namentlicher Konkurrent in der Antwort | 20 |
| Inhaber direkt erreichbar | 10 |

**ab 70 Punkten:** sofort anrufen · **40–69:** anrufen, wenn Zeit ·
**unter 40:** nicht anrufen, im Bestand lassen.

Der Schlüssel misst nur eines: **wie gross der Schmerz ist, den wir
belegen können.** Nicht Sympathie, nicht Firmengrösse.

---

## Rechercheablauf, 15 Minuten je Firma

```
1  Website prüfen (2 Min, automatisch)
      python3 cited.py pruefen <domain> --json > befunde/<firma>.json
2  Fragensatz erzeugen (1 Min)
3  Fünf Fragen an ChatGPT, Perplexity, Google AI stellen (8 Min)
4  Antworten im Wortlaut erfassen (2 Min)
5  Punkte zählen, Ansprechperson suchen (2 Min)
```

Schritt 3 ist der einzige Handgriff und der ist nicht wegzuautomatisieren
— genau deshalb ist er auch der Beleg, den Software-Anbieter nicht haben.

---

## Der Anruf — 45 Sekunden

> „Grüezi, [Name] von CITED aus Rapperswil. Ich habe eine kurze Sache,
> dauert eine Minute — passt es gerade?"
>
> *(Warten.)*
>
> „Ich habe heute Morgen geprüft, was KI-Systeme antworten, wenn jemand
> nach [Leistung] in [Ort] fragt. Ich habe fünf Fragen gestellt, bei
> ChatGPT, Perplexity und Google.
>
> **Ihre Firma kam in keiner einzigen Antwort vor. [Konkurrent] in
> allen fünf.**
>
> Ich wollte fragen, ob Sie das wussten."

Dann still sein.

**Warum dieser Aufbau:** Der Satz ist eine überprüfbare Tatsache über
seine Firma, kein Verkaufsargument. Die häufigste Reaktion ist eine
Rückfrage — und eine Rückfrage ist ein Gespräch.

### Reaktionen

**„Nein, das wusste ich nicht."** *(erwartet, häufigste)*
> „Die meisten wissen es nicht — es steht ja nirgends. Ich habe die
> Antworten im Wortlaut und dazu geprüft, woran es liegt. Darf ich
> Ihnen das in zwanzig Minuten zeigen? Kostet nichts."

**„Das ist mir egal / bringt uns nichts."**
> „Kann gut sein. Darf ich fragen: woher kommen Ihre Anfragen heute?"

Sagt er *Empfehlung*, ist er kein Kunde. Sagt er *Google*, dann:
> „Genau da verschiebt sich gerade etwas. Deshalb der Anruf."

**„Was kostet das?"**
> „Der Bericht kostet 1'200. Für die ersten drei Betriebe 790, weil ich
> noch keine Referenz habe und dafür Ihren Namen nennen dürfte. Ob es
> sich für Sie lohnt, sehen wir im Gespräch — das ist kostenlos."

**„Schicken Sie mir was."**
> „Mache ich, den Befund haben Sie in fünf Minuten im Postfach. Darf ich
> Sie Donnerstag kurz anrufen und hören, was Sie davon halten?"

Kein Ja auf den Rückruf heisst kein Interesse. Weiterziehen.

**„Machen wir schon mit unserer Agentur."**
> „Gut. Fragen Sie sie, bei wie vielen Antworten Sie genannt werden.
> Wenn sie die Zahl hat, sind Sie in guten Händen. Wenn nicht, rufen Sie
> mich an."

Das ist kein Trick — es ist die Frage, die den Unterschied entscheidet.

---

## Mail nach dem Anruf — nur an Erreichte

> **Betreff:** Ihre Firma in KI-Antworten — die fünf Fragen von vorhin
>
> Grüezi Herr/Frau [Name]
>
> Wie besprochen, hier der Befund. Ich habe fünf Fragen gestellt, die
> Ihre Kunden so stellen würden, an ChatGPT, Perplexity und Google AI.
>
> Ergebnis: [X] von 5 Antworten nennen Sie. [Konkurrent] wird [Y] mal
> genannt. Die Antworten stehen im Wortlaut im Anhang.
>
> Technisch habe ich zusätzlich geprüft, ob die Systeme Ihre Website
> überhaupt lesen können. Das grösste Hindernis ist [konkreter Befund].
>
> Passt Ihnen [Wochentag] oder [Wochentag] für zwanzig Minuten?
>
> Freundliche Grüsse
> [Name] · CITED · [Telefon]

Kurz. Anhang ist der Kurzbefund als PDF. Keine Broschüre.

---

## Nachfassen

| Wann | Was |
|---|---|
| Tag 0 | Anruf, danach Mail mit Befund |
| Tag 3 | Rückruf, falls zugesagt |
| Tag 10 | Eine Mail: eine neue Beobachtung, keine Wiederholung |
| Tag 30 | Nachmessung — „hat sich etwas verändert?" Das ist der stärkste Anlass, weil er neu ist. |
| danach | Bestand. Zweimal jährlich eine neue Messung. |

**Nach der dritten Berührung ohne Reaktion: Schluss.** Weiter zu drängen
schadet dem Ruf mehr, als der Auftrag wert wäre.

---

## Was wir nicht tun

Keine Massen-E-Mails. Keine identischen Nachrichten. Keine gekauften
Adresslisten. Keine unaufgeforderte Werbe-E-Mail vor dem ersten Kontakt
— in der Schweiz nach UWG heikel *(Einschätzung, nicht anwaltlich
geprüft)* und ohnehin wirkungslos. Keine erfundenen Referenzen. Keine
künstliche Dringlichkeit. Kein Blossstellen von Firmen in der
Öffentlichkeit.

---

## Kundenverwaltung

Eine Datei, `sales/leads.csv`, keine Software. Ab dem zehnten aktiven
Kontakt neu bewerten.

```
firma;domain;branche;ort;person;telefon;mail;punkte;befund_prozent;
genannt_von;konkurrent;status;letzter_kontakt;naechster_schritt;notiz
```

**Statuswerte:** `neu` → `geprüft` → `qualifiziert` → `angerufen` →
`erreicht` → `termin` → `angebot` → **`kunde`** / `absage`

Absagen mit **einem Wort** begründen. Nach zehn Absagen zeigt die Spalte,
ob das Angebot oder die Zielgruppe falsch ist. Das ist die wertvollste
Spalte der Datei.
