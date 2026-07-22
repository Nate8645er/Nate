# Go-Live-Checkliste + Kunden-E-Mail-Vorlage

## Checkliste bis zum ersten Verkauf
1. [ ] Vercel: Repo "Nate" importiert, Root "ai-command-center",
       4 Env-Variablen gesetzt (3 API-Keys + LICENSE_SECRET), deployt.
2. [ ] Test als Admin: /dashboard öffnen, Lizenz aktivieren (eigener
       Schlüssel), 1 Mission pro Stufe fahren.
3. [ ] Shopify: Store-Name "AI Command Center", JARVIS-Theme-ZIP
       hochgeladen + veroeffentlicht, App "Shopify Subscriptions"
       installiert, Zahlungen aktiv (erst Testmodus/Bogus Gateway).
4. [ ] Produkt-Videos hochgeladen (Produkt -> Medien).
5. [ ] Plattform-URL eintragen: in den 5 Shopify-Produktbeschreibungen
       ("Zugang unter: <URL>") und auf der ZEHNTAGE-Website.
6. [ ] AGB/Datenschutz anwaltlich prüfen lassen (Vorlagen liegen im Shop).
7. [ ] API-Keys rotieren (standen im Chat) und in Vercel aktualisieren.

## E-Mail-Vorlage: Schlüssel-Zustellung nach Kauf
Betreff: Ihr Zugang zu AI Command Center ist bereit

Guten Tag {Vorname Name}

Vielen Dank für Ihre Bestellung von {PLAN} bei AI Command Center.

SO EINFACH GEHT ES: Im Anhang finden Sie Ihre persönliche Start-Datei
"AI-Command-Center-Start.html". Einfach anklicken – am PC, Laptop oder
Handy. Die Plattform öffnet sich und Ihre Lizenz wird automatisch
aktiviert. Fertig.

Falls Sie lieber manuell starten:
1. Öffnen Sie: {PLATTFORM-URL}/dashboard
2. Klicken Sie oben rechts auf "Lizenz aktivieren"
3. Geben Sie Ihren persönlichen Lizenzschlüssel ein:

   {LIZENZSCHLUESSEL}

4. Wählen Sie Ihre Branche, geben Sie Ihrer KI-Abteilung den ersten
   Auftrag und sehen Sie Ihrem Team live bei der Arbeit zu.

IHR ANLEITUNGSVIDEO: Ebenfalls im Anhang finden Sie das Anleitungsvideo
für Ihr Abo (acc-anleitung-{plan klein}.mp4, knapp 4 Minuten). Einmal
anschauen und Sie wissen, wie Sie Ihre Stufe einrichten und nutzen –
von der Aktivierung über Ihre Skills bis zu E-Mail, Kunden, WhatsApp
und Autopilot. Es gibt pro Abo-Stufe ein eigenes Video – bitte immer
das zur gekauften Stufe passende beilegen.

Ihr Abo ist monatlich kündbar. Bei Fragen antworten Sie einfach auf
diese E-Mail.

Freundliche Grüsse
Blin Murseli
AI Command Center

## Schlüssel erzeugen (pro Verkauf)
{PLATTFORM-URL}/admin -> Passwort = LICENSE_SECRET -> Plan -> Erzeugen.
Danach Button "Start-Datei": lädt die persönliche
AI-Command-Center-Start.html herunter -> als Anhang in die Kunden-E-Mail.
Wichtig: Die Start-Datei auf der LIVE-Plattform (Vercel-URL) erzeugen,
damit der Link in der Datei auf die richtige Adresse zeigt.

## Neu seit Update (Juli 2026)
- Jahresabos im Shop (5 neue Shopify-Produkte, Tag "jahresabo"):
  10x Monatspreis = 2 Monate geschenkt. PERSONAL 199 / STARTER 1'990 /
  PROFESSIONAL 7'990 / BUSINESS 24'990 / ENTERPRISE ab 89'000 CHF/Jahr.
- Ultra-Levelup-Codes (Zusatzverkauf pro Bezahl-Stufe): /admin ->
  Checkbox "Ultra" oder scripts/generate-license.mjs ULTRA-<PLAN>.
  Wirkung: +50% Missionen, +50% Token-Budget, +2 Browser-Quellen,
  Skills der naechsten Stufe. Kunde gibt den Code im Lizenz-Fenster ein.
- Token-Budgets pro Stufe serverseitig erzwungen (FREE bewusst knapp).
- Pro Abo ein Komplett-Anleitungsvideo (acc-komplett-<plan>.mp4, ~6 Min,
  16 Kapitel inkl. Firma-verbinden, KI-Browser, Ultra) - nach Kauf das
  Video der gekauften Stufe beilegen.
- Eingebauter KI-Browser: Belegschaft recherchiert vor jeder Mission im
  Web (Suchketten-Fallback DuckDuckGo/Bing/Wikipedia, Quellen im Ergebnis).
  Jede Stufe hat ihn; Quellen je Stufe: FREE 2 / PERSONAL 3 / STARTER 4 /
  PROFESSIONAL 6 / BUSINESS 8 / ENTERPRISE 10. Schalter (Globus) in der
  Kommandozentrale, standardmaessig AN.
- 8 Bereiche: Missionen, Kommandozentrale (/chat), E-Mail-Zentrale (/email),
  Autopilot (/workflows), Berichte (/berichte), Team (/team),
  Integrationen, Admin. Alle nach Vercel-Deploy sofort nutzbar.
- Werbevideo fuer TikTok/Reels/Shorts: acc-werbevideo-tiktok.mp4
  (1080x1920, 58s, ohne Musik -- Sound in der App hinzufuegen).
  Hochladen: TikTok -> Upload -> Video waehlen -> Trend-Sound drueber.
