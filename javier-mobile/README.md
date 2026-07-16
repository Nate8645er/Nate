# JAVIER MOBILE

Eine JARVIS-artige KI fuer das iPhone 14 - als PWA, ohne Xcode. Das Backend
(Python + FastAPI + Anthropic Tool-Use-Agent) laeuft auf dem Windows-PC, das
iPhone verbindet sich per Browser im gleichen WLAN.

## Was JAVIER kann

- Sprechen und zuhoeren ueber AirPods (Push-to-talk auf den Arc-Reactor)
- Todo-Liste anlegen, lesen, abhaken (lokale JSON-Datei)
- Termine lesen und anlegen (lokale ICS-Kalenderdatei)
- Wetter fuer Rapperswil-Jona (Open-Meteo)
- Shopify-Status von MeowUfo, read-only (Bestellungen, Umsatz)
- Nachrichten vorbereiten (SMS / WhatsApp) - du tippst selbst auf Senden
- Instagram-Posts vorbereiten (Ausgangskorb) und optional echt
  veroeffentlichen (Graph API, siehe unten)
- Harmlose PC-Aktionen per Whitelist (Ordner oeffnen, Dateien listen,
  Screenshot)

## Freihaendig sprechen mit AirPods (Auto-Modus)

AirPods verbinden - Mikrofon und Sprachausgabe laufen automatisch darueber,
ohne Konfiguration. Zwei Arten zu sprechen:

- **Push-to-talk:** Arc-Reactor gedrueckt halten, sprechen, loslassen.
- **Auto-Modus:** Oben rechts auf "AUTO AUS" tippen. Ab dann oeffnet sich
  das Mikrofon nach jeder Antwort von JAVIER automatisch wieder - du
  fuehrst ein Gespraech, ohne das iPhone anzufassen. Nach etwa sechs
  stillen Runden pausiert der Modus von selbst (Akku und Privatsphaere);
  ein Tipp auf AUTO oder den Reaktor startet ihn wieder.

Der erste Tap ist Pflicht (iOS verlangt eine Nutzer-Interaktion fuer Mikro
und Sprachausgabe), und der Auto-Modus laeuft nur, solange die App im
Vordergrund geoeffnet ist - ein "Hey JAVIER" bei gesperrtem iPhone gibt
iOS nicht her.

## Ehrliche iOS-Grenzen (damit es keine Ueberraschungen gibt)

- **Kein Hintergrund-Listening.** iOS erlaubt Webseiten keinen dauerhaften
  Mikrofonzugriff. Du musst den Reaktor-Knopf druecken (Push-to-talk).
- **Kein automatisches Senden von iMessage/SMS/WhatsApp.** Apple und Meta
  erlauben das nicht. JAVIER bereitet die Nachricht vor und oeffnet den
  Nachrichten-Dialog mit vorbefuelltem Text - den letzten Tipp auf "Senden"
  machst du.
- **Sprachausgabe braucht eine Nutzer-Interaktion.** Die erste Sprachausgabe
  funktioniert erst nach einem Tap (der Reaktor-Tap zaehlt).
- **Mikrofon nur ueber HTTPS.** Deshalb das mkcert-Zertifikat (siehe unten).
- Die PWA laeuft nur, solange sie im Vordergrund geoeffnet ist.

## Schnellstart auf dem PC

1. `start.bat` doppelklicken. Beim ersten Mal werden die Abhaengigkeiten
   installiert und der Anthropic API-Key abgefragt (oder vorher in `.env`
   eintragen, Vorlage: `.env.example`).
2. Im Terminal erscheinen URL und QR-Code fuer das iPhone.
3. Windows-Firewall: beim ersten Start "Zugriff zulassen" fuer private
   Netzwerke bestaetigen (Port 8000).

## HTTPS mit mkcert (noetig fuer das Mikrofon auf iOS)

iOS blockiert das Mikrofon auf unverschluesselten Seiten. Loesung:
selbstsigniertes Zertifikat mit [mkcert](https://github.com/FiloSottile/mkcert).

Auf dem PC (PowerShell):

```
winget install FiloSottile.mkcert
mkcert -install
cd <dieser Ordner>
mkdir certs
cd certs
mkcert -cert-file cert.pem -key-file key.pem <PC-IP> localhost
```

`<PC-IP>` ist die IP, die `start.bat` anzeigt (z.B. 192.168.1.50).
Liegen `certs/cert.pem` und `certs/key.pem` vor, startet der Server
automatisch mit HTTPS.

Dann dem iPhone die mkcert-Stammzertifizierung beibringen:

1. Auf dem PC: `mkcert -CAROOT` zeigt den Ordner mit `rootCA.pem`.
2. Datei aufs iPhone bringen - am einfachsten: in dem CAROOT-Ordner kurz
   `python -m http.server 8001` starten und auf dem iPhone in Safari
   `http://<PC-IP>:8001/rootCA.pem` oeffnen, "Zulassen" tippen.
3. iPhone: Einstellungen -> Allgemein -> VPN und Geraeteverwaltung ->
   geladenes Profil "mkcert ..." installieren.
4. Wichtig: Einstellungen -> Allgemein -> Info -> Zertifikatsvertrauens-
   einstellungen -> Schalter fuer das mkcert-Zertifikat aktivieren.

Danach laedt `https://<PC-IP>:8000` ohne Warnung und das Mikrofon
funktioniert.

**Unterwegs:** Installiere [Tailscale](https://tailscale.com) auf PC und
iPhone (gleicher Account). Dann erreichst du JAVIER von ueberall unter der
Tailscale-IP des PCs (z.B. `https://100.x.y.z:8000`) - erzeuge das
mkcert-Zertifikat dann zusaetzlich fuer diese IP:
`mkcert -cert-file cert.pem -key-file key.pem <PC-IP> <Tailscale-IP> localhost`.

## In 3 Schritten aufs iPhone

1. **Server starten:** `start.bat` auf dem PC ausfuehren (HTTPS wie oben
   eingerichtet). iPhone und PC muessen im selben WLAN sein.
2. **In Safari oeffnen:** QR-Code aus dem Terminal scannen oder
   `https://<PC-IP>:8000` eintippen. Beim ersten Reaktor-Druck den
   Mikrofonzugriff erlauben.
3. **Zum Homescreen:** Teilen-Symbol -> "Zum Home-Bildschirm". Ab jetzt
   startet JAVIER als Vollbild-App mit eigenem Icon. AirPods verbinden -
   Ein- und Ausgabe laufen automatisch darueber.

## Kontakte fuer Nachrichten

`contacts.json` im Projektordner pflegen (Name -> Nummer im internationalen
Format):

```json
{ "Mutter": "+41791234567" }
```

Dann genuegt: "JAVIER, schreib meiner Mutter, dass ich spaeter komme." -
JAVIER formuliert, fragt nach ("Soll ich das absenden, Nate?") und zeigt
dann den WhatsApp/SMS-Button.

## Instagram Graph API Setup (optional, Kurzfassung)

Ohne Setup legt JAVIER Posts nur in den Ausgangskorb (`data/outbox/`).
Fuer echtes Veroeffentlichen:

1. **Business-Account:** Instagram-App -> Einstellungen -> Kontoart ->
   auf "Business" umstellen (kostenlos).
2. **Facebook-Seite verknuepfen:** Falls noch keine existiert, auf
   facebook.com eine Seite "MeowUfo" erstellen. Dann in der Instagram-App:
   Einstellungen -> Konten-Center bzw. "Verknuepfte Konten" -> Facebook-
   Seite verbinden.
3. **Meta-App erstellen:** [developers.facebook.com](https://developers.facebook.com)
   -> "App erstellen" -> Typ "Business". Produkt "Instagram Graph API"
   hinzufuegen.
4. **Token holen:** Im Graph API Explorer der App einen User-Token mit den
   Berechtigungen `instagram_basic`, `instagram_content_publish`,
   `pages_show_list`, `pages_read_engagement` erzeugen und ueber den
   "Access Token Debugger" in einen Long-Lived-Token (ca. 60 Tage)
   verlaengern.
5. **Business-ID finden:** Im Graph API Explorer `GET /me/accounts`
   (liefert die Page-ID), dann
   `GET /<page-id>?fields=instagram_business_account` - die ID darin ist
   die `IG_BUSINESS_ID`.
6. Beide Werte in `.env` eintragen (`IG_ACCESS_TOKEN`, `IG_BUSINESS_ID`)
   und Server neu starten - JAVIER erhaelt dann das Tool
   `publish_instagram_post`.

**Wichtig:** Die Graph API laedt das Bild von einer **oeffentlichen
https-URL** - lokale Pfade gehen nicht. Einfachste Loesungen:

- Bild zuerst in den Shopify-Adminbereich hochladen (Inhalte -> Dateien)
  und die CDN-URL verwenden, oder
- Tailscale Funnel: `tailscale funnel 8000` macht den Server kurzzeitig
  oeffentlich erreichbar (dann funktioniert eine URL auf ein Bild im
  static-Ordner).

## Projektstruktur

```
javier-mobile/
  server.py        FastAPI + Anthropic Tool-Use-Loop (claude-sonnet-4-6)
  tools.py         Alle Agent-Tools (Todos, Kalender, Wetter, Shopify, ...)
  instagram.py     Optionales Graph-API-Modul
  static/          index.html, manifest.json, sw.js, Icons (die PWA)
  contacts.json    Name -> Telefonnummer fuer Nachrichten
  start.bat        Ein-Klick-Start mit QR-Code
  data/            Entsteht zur Laufzeit: todos.json, calendar.ics,
                   outbox/, screenshots/
  certs/           Hier cert.pem + key.pem von mkcert ablegen
```

Abhaengigkeiten (bewusst minimal): fastapi, uvicorn, anthropic,
python-dotenv, requests, qrcode.
