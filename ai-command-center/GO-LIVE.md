# Go-Live-Checkliste + Kunden-E-Mail-Vorlage

## Checkliste bis zum ersten Verkauf
1. [ ] Vercel: Repo "Nate" importiert, Root "ai-command-center",
       4 Env-Variablen gesetzt (3 API-Keys + LICENSE_SECRET), deployt.
2. [ ] Test als Admin: /dashboard oeffnen, Lizenz aktivieren (eigener
       Schluessel), 1 Mission pro Stufe fahren.
3. [ ] Shopify: Store-Name "AI Command Center", JARVIS-Theme-ZIP
       hochgeladen + veroeffentlicht, App "Shopify Subscriptions"
       installiert, Zahlungen aktiv (erst Testmodus/Bogus Gateway).
4. [ ] Produkt-Videos hochgeladen (Produkt -> Medien).
5. [ ] Plattform-URL eintragen: in den 5 Shopify-Produktbeschreibungen
       ("Zugang unter: <URL>") und auf der ZEHNTAGE-Website.
6. [ ] AGB/Datenschutz anwaltlich pruefen lassen (Vorlagen liegen im Shop).
7. [ ] API-Keys rotieren (standen im Chat) und in Vercel aktualisieren.

## E-Mail-Vorlage: Schluessel-Zustellung nach Kauf
Betreff: Ihr Zugang zu AI Command Center ist bereit

Guten Tag {Vorname Name}

Vielen Dank fuer Ihre Bestellung von {PLAN} bei AI Command Center.

So starten Sie in 2 Minuten:
1. Oeffnen Sie: {PLATTFORM-URL}/dashboard
2. Klicken Sie oben rechts auf "Lizenz aktivieren"
3. Geben Sie Ihren persoenlichen Lizenzschluessel ein:

   {LIZENZSCHLUESSEL}

4. Waehlen Sie Ihre Branche, geben Sie Ihrer KI-Abteilung den ersten
   Auftrag und sehen Sie Ihrem Team live bei der Arbeit zu.

Ihr Abo ist monatlich kuendbar. Bei Fragen antworten Sie einfach auf
diese E-Mail.

Freundliche Gruesse
Blin Murseli
AI Command Center

## Schluessel erzeugen (pro Verkauf)
{PLATTFORM-URL}/admin -> Passwort = LICENSE_SECRET -> Plan -> Erzeugen.
