# SETTLED — Entscheid

**Auftrag:** eine KI für E-Commerce und Crypto.
**Datum:** 04.09.2026 · **Ausgaben bisher:** CHF 0.00 · **Kunden:** 0

---

## Was ich nicht gebaut habe, und warum

Der naheliegende Crypto-Pitch ist ein Handelswerkzeug: KI, die Kurse
vorhersagt, Signale gibt, automatisch handelt. Ich habe das nicht
gebaut.

Nicht aus Vorsicht, sondern weil es eines von beidem wäre: es
funktioniert nicht, oder es schadet Leuten. Wer Rendite verspricht,
verkauft entweder eine Illusion oder ein Risiko, das der Käufer nicht
einschätzen kann. **Es gibt keine garantierte Rendite, und nichts in
diesem Vorhaben deutet welche an.**

Ebenfalls bewusst nicht gebaut: alles, was einen privaten Schlüssel,
eine Seed Phrase oder einen Börsenzugang verlangt. SETTLED liest
öffentliche Kettendaten. Ein Werkzeug, das kein Geld bewegen kann, kann
auch bei einem Fehler keines verlieren.

---

## Was ich gebaut habe

**SETTLED — die langweilige Hälfte von Krypto im Handel.**

Ein Onlinehändler nimmt USDT an. Dann beginnt die Arbeit:

- Ist die Zahlung angekommen? Vollständig? Auf der richtigen Kette?
- Der Kunde hat 97.50 geschickt statt 100 — Gebühr abgezogen. Liefern
  oder nachfassen?
- Da ist ein Eingang ohne Bestellung. Wer war das?
- Und was war die Zahlung am Eingangstag in Franken wert? Ohne diese
  Zahl kann der Treuhänder nicht buchen.

Das ist heute Handarbeit mit Blockexplorer und Taschenrechner. Es ist
fehleranfällig, es ist steuerlich heikel, und es skaliert nicht.

**Das ist der Schnittpunkt von E-Commerce und Crypto, an dem Geld
verdient wird — nicht der Handel.**

---

## Warum diese Nische trägt

**Der Schmerz ist buchhalterisch, nicht spekulativ.** Er verschwindet
nicht, wenn der Kurs fällt. Er wächst mit jeder Bestellung.

**Der Käufer ist identifizierbar.** Shops, die bereits Krypto annehmen.
Man sieht es ihnen an der Kasse an — die Ansprache kann also auf einer
überprüfbaren Beobachtung beruhen, genau wie bei CITED.

**Wiederkehrend von Natur aus.** Ein Abgleich pro Monat, für immer.
Buchhaltung hört nicht auf.

**Nachprüfbar.** Jede Zeile im Bericht verweist auf eine echte
Transaktion auf einer öffentlichen Kette. Der Kunde kann jede Aussage
selbst kontrollieren. Das ist bei einem Handelssignal nicht so — und
genau deshalb ist dieses Produkt verkaufbar und jenes nicht.

---

## Was verifiziert ist

| | |
|---|---|
| Bitcoin lesen | ✔ gegen die Genesis-Adresse, 25 Eingänge gelesen |
| USDT/USDC ERC-20 | ✔ 209 Eingänge in einem 60-Block-Fenster |
| USDT-TRC20 | ✔ echte Eingänge, fremde Token korrekt herausgefiltert |
| Historische Kurse | ✔ CHF-Tageskurs, frei, ohne Schlüssel |
| Abgleich | ✔ 27 Tests, plus end-to-end gegen echte Kettendaten |
| Fenster-Überlauf | ✔ Halbierung greift, 5597 Einträge aus einem Fenster, das sonst abbricht |

**Ende-zu-Ende geprüft:** drei Bestellungen gegen eine reale
öffentliche Tron-Adresse. Bezahlt, unterbezahlt und offen wurden
korrekt erkannt; die eine nicht bewertbare Zeile wurde mit Begründung
ausgewiesen statt geschätzt.

## Was NICHT gebaut ist

| | |
|---|---|
| Natives ETH | braucht einen kostenpflichtigen Indexer |
| Kurse älter als ~1 Jahr | freie CoinGecko-Stufe antwortet mit 401 |
| Shop-Anbindung (Shopify, WooCommerce) | nicht gebaut — Bestellungen kommen als CSV |
| Mehrere Adressen je Lauf | nicht gebaut |
| Website, Preise, Akquise | **nicht gebaut** |

---

## Der offene Punkt, der grösser ist als alles Technische

Dies ist das **vierte** Vorhaben in dieser Sitzung: Feierabend,
Tagwerk, CITED, jetzt SETTLED. Keines ist an einem Kunden gescheitert.
Alle drei wurden vor dem ersten Verkaufsgespräch abgeräumt.

Das Werkzeug hier ist gut und geprüft. Es ändert nichts daran, dass ein
viertes gutes Werkzeug ohne ein einziges Gespräch genauso viel wert ist
wie die drei davor: **null.**

**Der nächste Schritt ist kein Code.** Er ist, einen Shop zu finden,
der Krypto annimmt, und ihn zu fragen, wie er seine Zahlungen heute
abgleicht. Fünf solche Gespräche sind mehr wert als jede weitere Kette,
die ich anschliesse.
