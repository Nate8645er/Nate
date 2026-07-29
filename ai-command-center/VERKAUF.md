# AI Command Center: Verkauf an Kunden

## Die Verkaufskette (Ende zu Ende)
1. Kunde kauft ein Abo im Shopify-Store (STARTER/PROFESSIONAL/BUSINESS/ENTERPRISE).
2. Du erzeugst einen Lizenzschlüssel für den gekauften Plan (siehe unten) und
   sendest ihn per E-Mail an den Kunden (Shopify: Bestellung -> Kunde -> E-Mail).
3. Kunde öffnet die Plattform-URL, klickt "Lizenz aktivieren", gibt den
   Schlüssel ein. Sein Plan ist freigeschaltet, Tageslimit gilt automatisch.

## Voraussetzung: Plattform online stellen (einmalig, Vercel)
1. vercel.com -> Sign up mit GitHub -> Projekt "Nate" importieren.
2. Root Directory auf "ai-command-center" setzen (Framework Next.js).
3. Environment Variables setzen:
   ANTHROPIC_API_KEY, OPENAI_API_KEY, MOONSHOT_API_KEY, LICENSE_SECRET
   WICHTIG: LICENSE_SECRET ist geheim und muss zu den verkauften Schlüsseln
   passen. Aendert man es, werden ALLE ausgegebenen Schlüssel ungültig.
4. Deploy. Ergebnis: oeffentliche URL, z. B. ai-command-center-xxx.vercel.app

## Lizenzschlüssel erzeugen (pro Verkauf)
Auf einem Rechner mit gesetztem LICENSE_SECRET (dasselbe wie in Vercel):

    export LICENSE_SECRET=<dein-secret>
    node scripts/generate-license.mjs STARTER 1
    node scripts/generate-license.mjs BUSINESS 5   # 5 auf Vorrat

## Schlüssel per Admin-Seite (/admin)
Statt Kommandozeile können Schlüssel auch per Klick erzeugt werden:
1. Plattform-URL + "/admin" öffnen (z. B. ai-command-center-xxx.vercel.app/admin).
   Es gibt keinen Link dorthin – nur wer die URL kennt, erreicht die Seite.
2. Admin-Passwort eingeben. Standard ist das LICENSE_SECRET dieser Installation;
   optional ein eigenes ADMIN_SECRET setzen (Env-Variable, siehe .env.example).
3. Plan + Anzahl (1–50) wählen, "Schlüssel erzeugen" klicken.
4. Schlüssel je einzeln oder alle auf einmal kopieren und per E-Mail an den
   Kunden senden. Die Schlüssel passen automatisch zum LICENSE_SECRET.

## Plan-Limits (serverseitig erzwungen)
FREE 3/Tag, PERSONAL 10, STARTER 25, PROFESSIONAL 100, BUSINESS 400, ENTERPRISE 1000.
Team-Grösse sichtbar: FREE 4, PERSONAL 6, STARTER 12, PROFESSIONAL 50, BUSINESS 250, ENTERPRISE 1000.

## Automatische Schlüssel-Zustellung (implementiert)
Der Shopify-Webhook (app/api/shopify/webhook/route.ts) erzeugt bei bezahlter
Bestellung automatisch den Schlüssel und liefert ihn aus (siehe
LIZENZ-AUTOMATIK.md). Die manuelle Erzeugung (oben) bleibt als Fallback.

## Noch offen für Voll-Automatik (Phase 3, optional)
- Einmal-Einloesung/Widerruf von Schlüsseln (braucht Vercel KV/Upstash).
- IP-Rate-Limit gegen Missbrauch (Vercel KV).
- AGB/Datenschutz vor Verkaufsstart anwaltlich prüfen.
