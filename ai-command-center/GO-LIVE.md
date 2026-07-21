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
- 8 Bereiche: Missionen, Kommandozentrale (/chat), E-Mail-Zentrale (/email),
  Autopilot (/workflows), Berichte (/berichte), Team (/team),
  Integrationen, Admin. Alle nach Vercel-Deploy sofort nutzbar.
- Werbevideo fuer TikTok/Reels/Shorts: acc-werbevideo-tiktok.mp4
  (1080x1920, 58s, ohne Musik -- Sound in der App hinzufuegen).
  Hochladen: TikTok -> Upload -> Video waehlen -> Trend-Sound drueber.
