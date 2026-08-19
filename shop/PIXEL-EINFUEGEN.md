# Pixel einbauen, ohne den Umweg ueber Meta oder den Shopify-Kanal

**Warum es diesen Weg gibt.** Am 19.8.2026 gemessen: der Laden meldet
an Pixel `1978393872804216` — den alten vom gesperrten KatzenUfo-Konto.
Der Pixel, den die laufenden Anzeigen brauchen, heisst
`883186891300328` und hat noch nie ein Ereignis bekommen.

Es gibt drei Wege, das zu aendern:

| Weg | Wer macht es | Haken |
|---|---|---|
| Shopify-Kanal → Datenfreigabe | Nate | Der neue Pixel taucht evtl. nicht in der Liste auf |
| Meta Events Manager → Partner-Integration | Nate | Fuehrt auf business.facebook.com — die Wand von gestern |
| **Kundenereignis in Shopify** | **Nate, einmal einfuegen** | **Braucht kein Facebook-Login** |

Der dritte Weg braucht weder Business Manager noch eine Verbindung
zwischen Meta und Shopify. Es ist reines JavaScript im Laden, das an
die Pixelnummer meldet. Deshalb steht er hier.

---

## So geht es

1. Shopify Admin → **Einstellungen** → **Kundenereignisse**
   (direkt: `https://admin.shopify.com/store/i0m1xi-h5/settings/customer_events`)
2. Oben rechts **Benutzerdefiniertes Pixel hinzufuegen**
3. Name: `Meta Pixel Let'sDrink`
4. **Kundenschutz** (Customer privacy):
   - Berechtigung: **Erforderlich**
   - Datenverkaufsbeschraenkung: **Marketing**

   Damit feuert der Pixel nur, wenn die Zustimmung vorliegt. Das ist
   nicht Vorsicht um der Vorsicht willen: ein Marketing-Pixel, der ohne
   Zustimmung laeuft, ist genau das, was das Datenschutzgesetz meint.
5. Den ganzen Code unten in das grosse Feld einfuegen
6. **Speichern** und dann **Verbinden**

Danach die Startseite einmal aufrufen. Sag mir Bescheid — ich sehe
dann in derselben Abfrage nach, die heute noch "1970" gemeldet hat.

---

## Der Code

```js
// Meta Pixel fuer Let'sDrink - Pixelnummer 883186891300328
// Eingebaut als Kundenereignis, damit weder Business Manager noch
// eine Verbindung zwischen Meta und Shopify noetig ist.

!function(f,b,e,v,n,t,s){if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];
t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window,document,'script',
'https://connect.facebook.net/en_US/fbevents.js');

fbq('init', '883186891300328');

// Seitenaufruf
analytics.subscribe('page_viewed', () => {
  fbq('track', 'PageView');
});

// Produktseite angesehen
analytics.subscribe('product_viewed', (event) => {
  const v = event.data.productVariant;
  fbq('track', 'ViewContent', {
    content_ids: [v.id],
    content_name: v.product.title,
    content_type: 'product',
    value: v.price.amount,
    currency: v.price.currencyCode
  });
});

// In den Warenkorb - das Ereignis, auf das die naechste Kampagne lernt
analytics.subscribe('product_added_to_cart', (event) => {
  const l = event.data.cartLine;
  fbq('track', 'AddToCart', {
    content_ids: [l.merchandise.id],
    content_name: l.merchandise.product.title,
    content_type: 'product',
    value: l.cost.totalAmount.amount,
    currency: l.cost.totalAmount.currencyCode
  });
});

// Kasse begonnen
analytics.subscribe('checkout_started', (event) => {
  const c = event.data.checkout;
  fbq('track', 'InitiateCheckout', {
    value: c.totalPrice.amount,
    currency: c.totalPrice.currencyCode,
    num_items: c.lineItems.length
  });
});

// Kauf abgeschlossen
analytics.subscribe('checkout_completed', (event) => {
  const c = event.data.checkout;
  fbq('track', 'Purchase', {
    content_ids: c.lineItems.map(i => i.variant.id),
    content_type: 'product',
    value: c.totalPrice.amount,
    currency: c.totalPrice.currencyCode,
    num_items: c.lineItems.length
  });
});
```

---

## Was dieser Weg kann und was nicht

**Kann:** Seitenaufruf, Produktansicht, Warenkorb, Kassenstart und Kauf
— mit Betrag und Waehrung. Das ist mehr, als der Shopify-Kanal auf der
Browserseite meldet, weil "Produkt angesehen" dort nur auf
`/products/...` feuert und die Startseite auslaesst. Genau diese
Messluecke hat gestern die Zahl 1.3 Prozent erzeugt, die ich
faelschlich fuer ein Verkaufsproblem gehalten hatte.

**Kann nicht:** die Conversions API. Das ist der zweite, serverseitige
Kanal, der auch dann meldet, wenn ein Browser blockt. Den gibt es nur
ueber die Partner-Integration. Fuer den Anfang ist der Browserkanal
genug — er reicht, damit eine Kampagne auf Warenkorb oder Kauf lernen
kann.

**Doppelte Ereignisse?** Nein. Der Shopify-Kanal meldet an
`1978393872804216`, dieser Code an `883186891300328`. Zwei
verschiedene Pixel, keine Ueberschneidung.

Wenn die Partner-Integration bei Meta doch klappt, gehoert dieser Code
wieder heraus — sonst zaehlt derselbe Kauf zweimal.
