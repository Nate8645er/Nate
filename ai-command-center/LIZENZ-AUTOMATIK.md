# Automatische Lizenz-Auslieferung (Shopify → Schlüssel)

Bei jeder **bezahlten** Bestellung erzeugt die Route
`POST /api/shopify/webhook` automatisch den passenden Lizenzschlüssel und
liefert ihn aus. Getestet: Zuordnung Titel→Stufe und Schlüssel-Erzeugung
(die Keys bestehen die echte `verifyLicenseKey`-Prüfung).

## Aktivierung (einmalig, nach dem Vercel-Deploy)

### 1. Umgebungsvariablen in Vercel setzen
| Variable | Zweck | Pflicht |
|----------|-------|---------|
| `LICENSE_SECRET` | signiert die Schlüssel (muss gesetzt sein, sonst gelten die Keys nicht) | ja |
| `SHOPIFY_WEBHOOK_SECRET` | prüft die Echtheit der Webhook-Anfrage | ja |
| `SHOPIFY_STORE_DOMAIN` | z. B. `i0m1xi-h5.myshopify.com` – hängt die Keys an die Bestellung | empfohlen |
| `SHOPIFY_ADMIN_TOKEN` | Admin-API-Token (Rechte: `write_orders`) | empfohlen |
| `RESEND_API_KEY` + `ACC_FROM_EMAIL` | schickt dem Kunden die Keys automatisch per E-Mail | optional |

Je nachdem, was gesetzt ist, liefert der Webhook aus:
- **Nur Pflicht-Variablen:** der Schlüssel steht danach an der Bestellung
  (Notiz + Metafeld `acc.license_keys`) – du kopierst ihn und sendest ihn.
- **+ Admin-Token:** der Key wird automatisch an die Bestellung gehängt.
- **+ Resend:** der Kunde bekommt den Key sofort per E-Mail (voll automatisch).

### 2. Webhook in Shopify anlegen
Shopify-Admin → **Einstellungen → Benachrichtigungen → Webhooks** →
**Webhook erstellen**:
- Ereignis: **Bestellung bezahlt** (`orders/paid`)
- Format: **JSON**
- URL: `https://DEINE-DOMAIN/api/shopify/webhook`

Shopify zeigt dir danach das **Signatur-Secret** dieses Webhooks – genau
dieses gehört in `SHOPIFY_WEBHOOK_SECRET`.

### 3. Test
Eine Test-Bestellung auslösen (oder in Shopify „Webhook senden"). Danach
steht der Schlüssel an der Bestellung bzw. kommt per E-Mail an.

## Was der Webhook NICHT tut
- FREE, Ultra-Levelup, Setup- und Support-Pakete erhalten **keinen**
  Lizenzschlüssel (FREE braucht keinen; die Zusätze sind stufen-unabhängig).
- Ohne gültige HMAC-Signatur wird jede Anfrage mit `401` abgelehnt.
