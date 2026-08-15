/* =====================================================================
   n-nova.js — LET'SDRINK NOVA
   9.8.2026. Bauleitung.

   Keine Bibliothek. Neun Aufgaben:
     1. Kopfzeile verglasen, sobald gescrollt wird
     2. Scroll-Reveal (IntersectionObserver, kein Scroll-Listener)
     3. Parallaxe - EINE rAF-Schleife, sonst nichts
     4. Mobile Navigation
     5. Farbwechsel ohne Neuladen
     6. Warenkorb-Schublade ueber die Shopify-Cart-API
     7. Mitlaufende Kaufleiste
     8. Farbgalerie - Drehung, Groesse, Deckkraft ueber nativem Scrollen
     9. Rundumblick, sobald echte 360-Grad-Aufnahmen vorliegen

   GRUNDSATZ: alles ist Zugabe. Ohne JavaScript bleibt der Shop
   vollstaendig kaufbar - die Farbpunkte sind echte ?variant=-Verweise,
   das Kaufformular ist ein echtes Formular mit echtem Ziel, und der
   Warenkorb hat eine eigene Seite. Faellt das Skript aus, faellt nur
   der Komfort weg.
   ===================================================================== */
(function () {
  "use strict";

  var W = window, D = document;
  var ruhig = W.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* Scroll-Sperre fuer Menue und Warenkorb-Schublade. Sie MUSS auf
     <html> liegen, nicht nur auf <body>: mit overflow:hidden allein am
     body sass das fixierte Menue gemessen 22 px zu tief und der
     Ankuendigungsbalken blieb darueber stehen. */
  var gesperrt = 0;
  function sperren(an) {
    gesperrt = Math.max(0, gesperrt + (an ? 1 : -1));
    D.documentElement.classList.toggle("n-sperre", gesperrt > 0);
  }
  var $  = function (s, k) { return (k || D).querySelector(s); };
  var $$ = function (s, k) { return [].slice.call((k || D).querySelectorAll(s)); };

  D.documentElement.classList.add("n-js");

  /* ---------- 1. Kopfzeile ------------------------------------------ */
  var kopf = $("[data-kopf]");
  if (kopf) {
    var festMachen = function () { kopf.classList.toggle("n-fest", W.scrollY > 12); };
    W.addEventListener("scroll", festMachen, { passive: true });
    festMachen();
  }

  /* ---------- 2. Scroll-Reveal -------------------------------------- */
  var zuZeigen = $$("[data-auf]");
  if (zuZeigen.length) {
    // Staffelung: jede Karte kennt ihren Platz in der Reihe.
    $$("[data-staffel]").forEach(function (g) {
      [].slice.call(g.children).forEach(function (k, i) {
        k.style.setProperty("--i", i);
      });
    });
    if (ruhig || !("IntersectionObserver" in W)) {
      zuZeigen.forEach(function (e) { e.classList.add("n-da"); });
    } else {
      var beobachter = new IntersectionObserver(function (eintraege, selbst) {
        eintraege.forEach(function (e) {
          if (!e.isIntersecting) return;
          e.target.classList.add("n-da");
          selbst.unobserve(e.target);          // einmal reicht
        });
      }, { rootMargin: "0px 0px -12% 0px", threshold: 0.08 });
      zuZeigen.forEach(function (e) { beobachter.observe(e); });
    }
  }

  /* ---------- 3. Parallaxe ------------------------------------------ */
  /* Genau eine Schleife, nur waehrend das Element im Bild ist, und nur
     wenn der Zeiger nicht grob ist (Handys haben keinen Mauszeiger und
     bekommen die Bewegung ueber das Scrollen). */
  var schwebt = $$("[data-parallaxe]");
  if (schwebt.length && !ruhig) {
    var laeuft = false;
    var zeichne = function () {
      laeuft = false;
      var mitte = W.innerHeight / 2;
      schwebt.forEach(function (e) {
        var r = e.getBoundingClientRect();
        if (r.bottom < -200 || r.top > W.innerHeight + 200) return;
        var staerke = parseFloat(e.getAttribute("data-parallaxe")) || 12;
        var d = ((r.top + r.height / 2) - mitte) / mitte;   // -1 .. 1
        e.style.transform = "translate3d(0," + (d * staerke).toFixed(2) + "px,0)";
      });
    };
    var anstossen = function () {
      if (laeuft) return;
      laeuft = true;
      W.requestAnimationFrame(zeichne);
    };
    W.addEventListener("scroll", anstossen, { passive: true });
    W.addEventListener("resize", anstossen);
    anstossen();
  }

  /* ---------- 4. Mobile Navigation ---------------------------------- */
  var mnav = $("[data-mnav]");
  if (mnav) {
    var navAuf = function (auf) {
      mnav.classList.toggle("n-offen", auf);
      sperren(auf);
      var k = $("[data-mnav-auf]");
      if (k) k.setAttribute("aria-expanded", auf ? "true" : "false");
      mnav.setAttribute("aria-hidden", auf ? "false" : "true");
      // Gemessen: der Fokus blieb beim Oeffnen auf dem Burger hinter der
      // Glasflaeche stehen und kehrte beim Schliessen nicht zurueck.
      // Der Griff ins naechste Bild ist noetig, weil das Menue im
      // Moment des Umschaltens noch visibility:hidden traegt - focus()
      // greift dann nicht.
      if (auf) W.setTimeout(function () {
        var z = $("[data-mnav-zu]", mnav);
        // preventScroll: sonst zieht der Browser das Menue, das selbst
        // ein Scrollbehaelter ist, um die Kopfzeilenhoehe nach oben -
        // gemessen 22 px, wodurch der Ankuendigungsbalken darueber
        // wieder sichtbar wurde.
        if (z) { try { z.focus({ preventScroll: true }); } catch (e) { z.focus(); } }
      }, 60);
      else if (k) k.focus();
    };
    W.__nNavZu = function () { if (mnav.classList.contains("n-offen")) navAuf(false); };
    var kA = $("[data-mnav-auf]"); if (kA) kA.addEventListener("click", function () { navAuf(true); });
    var kZ = $("[data-mnav-zu]");  if (kZ) kZ.addEventListener("click", function () { navAuf(false); });
    $$("a", mnav).forEach(function (a) { a.addEventListener("click", function () { navAuf(false); }); });
  }

  /* ---------- 5. Farbwechsel ---------------------------------------- */
  // Die Galerie weiter unten waehlt ueber dieselbe Funktion aus, statt
  // die Zustandspflege ein zweites Mal zu schreiben.
  var waehleFarbe = null;
  var punkte = $$("[data-farbe]");
  if (punkte.length) {
    var haupt  = $("[data-hauptbild]");
    var lbild  = $("[data-leistenbild]");
    var fname  = $("[data-farbname]");
    var feld   = $("[data-variantenfeld]");

    var waehle = function (p, ev) {
      var bild = p.getAttribute("data-bild");
      var name = p.getAttribute("data-name");
      var id   = p.getAttribute("data-variante");
      if (!bild || !id) return;                 // unvollstaendig: Link folgen
      if (ev) ev.preventDefault();

      if (haupt) {
        // Kurzes Aufblenden, damit der Wechsel nicht hart springt.
        haupt.style.transition = "opacity .18s ease";
        haupt.style.opacity = "0";
        W.setTimeout(function () {
          haupt.src = bild;
          var v = haupt.getAttribute("data-alt-vorlage");
          if (v) haupt.alt = v.replace("%s", name);
          haupt.style.opacity = "1";
        }, 180);
      }
      // Ton der Produktflaeche mitfuehren - sonst verschwindet die
      // schwarze Flasche auf der tiefen bzw. die weisse auf der hellen.
      var ton = p.getAttribute("data-panel");
      if (ton) $$("[data-buehne]").forEach(function (fl) {
        fl.classList.toggle("n-hell", ton === "hell");
      });
      if (lbild) lbild.src = bild;
      if (fname) fname.textContent = name;
      if (feld)  feld.value = id;
      punkte.forEach(function (q) {
        q.setAttribute("aria-pressed", q === p ? "true" : "false");
      });
      if (W.history && W.history.replaceState) {
        try {
          var u = new URL(W.location.href);
          u.searchParams.set("variant", id);
          W.history.replaceState({}, "", u);
        } catch (x) {}
      }
    };
    waehleFarbe = waehle;
    punkte.forEach(function (p) {
      p.addEventListener("click", function (e) { waehle(p, e); });
      p.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); waehle(p, e); }
      });
    });
  }

  /* ---------- 6. Warenkorb-Schublade -------------------------------- */
  var lade    = $("[data-lade]");
  var schleier= $("[data-schleier]");
  var leib    = $("[data-lade-leib]");
  var fuss    = $("[data-lade-fuss]");
  var zahl    = $("[data-korbzahl]");
  var geld    = D.documentElement.getAttribute("data-geldform") || "CHF {{amount}}";

  /* Shopifys Betraege kommen in der kleinsten Einheit (Rappen).
     Dieser Shop steht heute auf "CHF {{amount}}", aber das ist EIN
     Klick im Admin von etwas anderem entfernt - Schweizer Laeden
     nehmen oft {{amount_with_apostrophe_separator}}. Stand der
     frueheren Fassung: sie kannte drei der acht Platzhalter und
     haette den Rest als Rohtext in die Warenkorb-Schublade
     geschrieben. Ausserdem fehlte die Tausendertrennung ganz - ab
     CHF 1000 stand dort "1039.90" statt "1'039.90".

     Darum: einmal richtig gruppieren, dann alle acht Platzhalter
     bedienen. */
  function gruppiert(betrag, stellen, tausender, komma) {
    var fest = betrag.toFixed(stellen);
    var teile = fest.split(".");
    var ganz = teile[0].replace(/\B(?=(\d{3})+(?!\d))/g, tausender);
    return stellen ? ganz + komma + teile[1] : ganz;
  }
  /* Alle Korb-Aufrufe gehen ueber dieselbe Wurzel. Zwei der drei
     Aufrufe standen fest auf "/cart/..." - das bricht, sobald ein
     zweiter Markt mit Sprachpraefix dazukommt (/de-ch/cart/add.js). */
  function wurzel() {
    return (W.Shopify && W.Shopify.routes && W.Shopify.routes.root) || "/";
  }

  function franken(rappen) {
    var b = rappen / 100;
    var muster = [
      ["amount",                                  2, ",",      "."],
      ["amount_no_decimals",                      0, ",",      "."],
      ["amount_with_comma_separator",             2, ".",      ","],
      ["amount_no_decimals_with_comma_separator", 0, ".",      ","],
      ["amount_with_apostrophe_separator",        2, "\u2019", "."],
      ["amount_with_space_separator",             2, "\u202F", ","],
      ["amount_no_decimals_with_space_separator", 0, "\u202F", ","],
      ["amount_with_period_and_space_separator",  2, "\u202F", "."]
    ];
    var aus = geld;
    // Die laengeren Namen zuerst, sonst frisst "amount" den Anfang
    // von "amount_with_comma_separator".
    muster.sort(function (a, c) { return c[0].length - a[0].length; });
    muster.forEach(function (m) {
      aus = aus.replace(new RegExp("\\{\\{\\s*" + m[0] + "\\s*\\}\\}", "g"),
                        gruppiert(b, m[1], m[2], m[3]));
    });
    return aus;
  }
  /* Bauhilfe: Element mit Eigenschaften und Kindern.
     Bewusst KEIN innerHTML - Produkt- und Variantennamen kommen zwar
     aus dem eigenen Shop, aber ueber die Cart-API zurueck. Wer den
     Umweg ueber Zeichenketten geht, baut sich frueher oder spaeter
     eine Skriptluecke ein. Mit textContent kann das nicht passieren. */
  function el(art, eigen, kinder) {
    var e = D.createElement(art);
    if (eigen) Object.keys(eigen).forEach(function (k) {
      if (k === "text") e.textContent = eigen[k];
      else if (k === "klasse") e.className = eigen[k];
      else e.setAttribute(k, eigen[k]);
    });
    (kinder || []).forEach(function (k) { if (k) e.appendChild(k); });
    return e;
  }

  function ladeAuf(auf) {
    if (!lade) return;
    lade.classList.toggle("n-offen", auf);
    if (schleier) schleier.classList.toggle("n-offen", auf);
    sperren(auf);
    lade.setAttribute("aria-hidden", auf ? "false" : "true");
    if (auf) { var z = $("[data-lade-zu]", lade); if (z) z.focus(); }
  }

  function zeichneKorb(korb) {
    if (zahl) {
      zahl.textContent = korb.item_count;
      zahl.hidden = korb.item_count === 0;
    }
    if (!leib) return;

    leib.textContent = "";

    if (!korb.items.length) {
      leib.appendChild(el("div", { klasse: "n-lade__leer" },
        [el("p", { text: "Dein Warenkorb ist leer." })]));
      if (fuss) fuss.hidden = true;
      return;
    }
    if (fuss) fuss.hidden = false;

    korb.items.forEach(function (p, i) {
      var nr = i + 1;
      var bildkasten = el("div", { klasse: "n-zeile__bild" });
      if (p.image) {
        bildkasten.appendChild(el("img", {
          src: p.image, alt: "", width: "72", height: "72", loading: "lazy"
        }));
      }
      var menge = el("div", { klasse: "n-menge" }, [
        el("button", { type: "button", "data-zeile": nr, "data-schritt": "-1",
                       "aria-label": "Weniger", text: "−" }),
        el("input", { type: "text", value: String(parseInt(p.quantity, 10) || 0),
                      readonly: "readonly", "aria-label": "Menge" }),
        el("button", { type: "button", "data-zeile": nr, "data-schritt": "1",
                       "aria-label": "Mehr", text: "+" })
      ]);
      leib.appendChild(el("div", { klasse: "n-zeile" }, [
        bildkasten,
        el("div", null, [
          el("p", { klasse: "n-zeile__name", text: p.product_title }),
          el("p", { klasse: "n-zeile__var",  text: p.variant_title || "" }),
          el("div", { klasse: "n-zeile__fuss" }, [
            menge,
            el("span", { klasse: "n-zeile__preis", text: franken(p.final_line_price) })
          ])
        ])
      ]));
    });

    // Zwischensumme UND Total tragen dasselbe Merkmal - in der Schweiz
    // ist der Versand gratis, beide Zahlen sind also gleich. Sobald ein
    // Land mit Versandkosten dazukommt, rechnet der Bestellabschluss.
    $$("[data-lade-summe]").forEach(function (s) {
      s.textContent = franken(korb.items_subtotal_price);
    });
  }

  function holeKorb(dannOeffnen) {
    return fetch(wurzel() + "cart.js",
                 { headers: { "Accept": "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (k) { zeichneKorb(k); if (dannOeffnen) ladeAuf(true); return k; })
      .catch(function () { /* Netz weg: die Korbseite funktioniert weiterhin */ });
  }

  // Mengen in der Schublade
  if (leib) {
    leib.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-zeile]");
      if (!b) return;
      var zeile = b.getAttribute("data-zeile");
      var eingabe = $("input", b.parentNode);
      var neu = Math.max(0, parseInt(eingabe.value, 10) + parseInt(b.getAttribute("data-schritt"), 10));
      b.disabled = true;
      fetch(wurzel() + "cart/change.js", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ line: parseInt(zeile, 10), quantity: neu })
      }).then(function (r) { return r.json(); })
        .then(zeichneKorb)
        .catch(function () { W.location.href = "/cart"; });
    });
  }

  $$("[data-lade-auf]").forEach(function (k) {
    k.addEventListener("click", function (e) {
      /* Erst abfangen, dann laden - aber wenn das Laden scheitert, den
         Besucher NICHT im Nichts stehen lassen. Vorher verschluckte ein
         leeres catch den Fehler, und weil preventDefault schon gelaufen
         war, fuehrte auch der Verweis auf /cart nicht mehr weiter: der
         Warenkorb war unerreichbar. Gemessen mit abgewiesenem fetch. */
      e.preventDefault();
      holeKorb(true).catch(function () {
        W.location.href = k.getAttribute("href") || (wurzel() + "cart");
      });
    });
  });
  $$("[data-lade-zu]").forEach(function (k) {
    k.addEventListener("click", function () { ladeAuf(false); });
  });
  if (schleier) schleier.addEventListener("click", function () { ladeAuf(false); });
  D.addEventListener("keydown", function (e) {
    if (e.key !== "Escape") return;
    ladeAuf(false);
    // Ueber dieselbe Funktion schliessen wie der Knopf, sonst bleibt
    // aria-expanded auf "true" und Vorleseprogramme melden das Menue
    // weiterhin als geoeffnet.
    if (W.__nNavZu) W.__nNavZu();
  });

  // Kaufformulare abfangen und in die Schublade legen
  $$("form[data-kaufform]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!W.fetch) return;                       // altes Geraet: normal absenden
      e.preventDefault();
      var knopf = $("[type=submit]", f);
      var alt = knopf ? knopf.textContent : "";
      if (knopf) { knopf.disabled = true; knopf.textContent = "Wird hinzugefügt …"; }
      fetch(wurzel() + "cart/add.js", { method: "POST", body: new FormData(f) })
        .then(function (r) {
          if (!r.ok) throw new Error("abgelehnt");
          return r.json();
        })
        .then(function () { return holeKorb(true); })
        .catch(function () { f.submit(); })       // im Zweifel echter Weg
        .then(function () {
          if (knopf) { knopf.disabled = false; knopf.textContent = alt; }
        });
    });
  });

  /* ---------- Mengen-Schrittschalter auf der Produktseite ----------- */
  $$("[data-mengenfeld]").forEach(function (feld) {
    var eltern = feld.parentNode;
    $$("button[data-mschritt]", eltern).forEach(function (b) {
      b.addEventListener("click", function () {
        var n = parseInt(feld.value, 10) || 1;
        feld.value = Math.max(1, n + parseInt(b.getAttribute("data-mschritt"), 10));
      });
    });
  });

  /* ---------- 7. Kaufleiste ----------------------------------------- */
  var leiste = $("[data-leiste]");
  var anker  = $("[data-leiste-anker]");
  if (leiste && anker && "IntersectionObserver" in W) {
    new IntersectionObserver(function (ein) {
      ein.forEach(function (e) {
        leiste.classList.toggle("n-an", !e.isIntersecting && e.boundingClientRect.top < 0);
      });
    }, { rootMargin: "0px 0px -100% 0px" }).observe(anker);
  }

  // Korbzahl beim Laden angleichen (Zurueck-Taste, Cache)
  if (zahl) holeKorb(false);

  /* ---------- 8. Farbgalerie ----------------------------------------
     Die Buehne ist wischbar. Gescrollt wird nativ (overflow-x +
     scroll-snap, siehe CSS); dieses Stueck legt nur Drehung, Groesse
     und Deckkraft darueber und meldet die Farbe an Abschnitt 5.

     Auf dem Handy und auf dem Trackpad genuegt das. Fuer die Maus
     kommt weiter unten ein Ziehen dazu - ohne das waere die Galerie
     am Rechner nur ueber die Pfeile bedienbar. */
  var gal = $("[data-gal]");
  if (gal) {
    var felder  = $$("[data-gal-feld]", gal);
    var zaehler = $("[data-gal-zaehler]");
    var pfeile  = $$("[data-gal-schritt]");
    var buehne  = gal.parentNode;
    var aktiv   = -1;
    var malt    = false;

    var mittePunkt = function (e) {
      var r = e.getBoundingClientRect();
      return r.left + r.width / 2;
    };

    // Nur die Anzeige: Zaehler, Ton der Flaeche, Pfeilzustand. Das
    // laeuft auch beim ersten Aufbau - sonst bliebe der linke Pfeil
    // beim ersten Feld anklickbar, weil sich der Index nie AENDERT.
    // Die Galerie ist gedreht, damit die gewaehlte Farbe in der Mitte
    // liegt (siehe n-start.liquid). Der Zaehler darf deshalb NICHT die
    // Galerieposition zeigen - sonst stuende bei der ersten Farbe
    // "3 von 6". Er zaehlt die Farbpunkte unter dem Preis, und die
    // behalten die urspruengliche Reihenfolge.
    var punktNummer = function (f) {
      var id = f.getAttribute("data-variante");
      for (var k = 0; k < punkte.length; k++) {
        if (punkte[k].getAttribute("data-variante") === id) return k + 1;
      }
      return 0;
    };

    var anzeigen = function (i) {
      var f = felder[i];
      if (!f) return;
      var nr = punktNummer(f) || (i + 1);
      var von = punkte.length || felder.length;
      if (zaehler) zaehler.textContent = nr + " von " + von + " · 550 ml";
      if (buehne && buehne.classList.contains("n-buehne")) {
        buehne.classList.toggle("n-hell", f.getAttribute("data-panel") === "hell");
      }
      pfeile.forEach(function (b) {
        var sch = parseInt(b.getAttribute("data-gal-schritt"), 10);
        b.disabled = (i + sch < 0) || (i + sch > felder.length - 1);
      });
    };

    var uebernehmen = function (i) {
      var f = felder[i];
      if (!f) return;
      anzeigen(i);
      // Preis, Kaufknopf und Farbname laufen ueber Abschnitt 5 mit.
      // Beim ersten Aufbau bewusst NICHT - das wuerde nur die Adresse
      // um ein ?variant= ergaenzen, das niemand gewaehlt hat.
      if (waehleFarbe) {
        var id = f.getAttribute("data-variante");
        for (var k = 0; k < punkte.length; k++) {
          if (punkte[k].getAttribute("data-variante") === id) { waehleFarbe(punkte[k]); break; }
        }
      }
      // Meldung fuer alles, was auf die Farbe reagieren muss, ohne dass
      // die Galerie davon wissen muesste. Zurzeit hoert nur der
      // Rundumblick zu: den gibt es nicht fuer jede Farbe.
      try {
        D.dispatchEvent(new CustomEvent("n:farbe", {
          detail: { platz: i, slug: f.getAttribute("data-slug") || "" } }));
      } catch (e) { /* aeltere Browser ohne CustomEvent: kein Verlust */ }
    };

    /* DIE FLASCHE SELBST IST ANTIPPBAR.
       Vorher war sie tot: das Bild stand auf pointer-events:none und
       kein Feld hatte einen Klick-Empfaenger. Das Groesste auf der
       Seite reagierte auf nichts - man tippt eine Flasche an und es
       passiert nichts. Genau das war die Rueckmeldung.

       Ein Wischen darf NICHT als Tipp gelten. Deshalb wird die
       Startposition gemerkt und nur gewaehlt, wenn der Finger sich um
       weniger als 12 Pixel bewegt hat. */
    (function () {
      var startX = 0, startY = 0, startZeit = 0;
      var merken = function (e) {
        var t = (e.touches && e.touches[0]) || e;
        startX = t.clientX; startY = t.clientY; startZeit = e.timeStamp || 0;
      };
      gal.addEventListener("pointerdown", merken, { passive: true });
      gal.addEventListener("touchstart", merken, { passive: true });

      gal.addEventListener("click", function (e) {
        var f = e.target.closest ? e.target.closest("[data-gal-feld]") : null;
        if (!f) return;
        var dx = Math.abs(e.clientX - startX), dy = Math.abs(e.clientY - startY);
        if (dx > 12 || dy > 12) return;              // war ein Wischen
        var i = felder.indexOf(f);
        if (i < 0) return;
        f.scrollIntoView({ behavior: ruhig ? "auto" : "smooth",
                           block: "nearest", inline: "center" });
        uebernehmen(i);
      });
    })();

    var malen = function () {
      malt = false;
      var r = gal.getBoundingClientRect();
      var m = r.left + r.width / 2;
      var halb = (r.width / 2) || 1;
      var nah = 0, nd = Infinity;
      felder.forEach(function (f, i) {
        var d = (mittePunkt(f) - m) / halb;          // -1 .. 1 vom Zentrum
        var a = Math.min(Math.abs(d), 1);
        // Begrenzen, sonst drehen die weit aussen liegenden Felder ueber
        // 90 Grad hinaus und stehen spiegelverkehrt.
        var dk = Math.max(-1, Math.min(1, d));
        if (!ruhig) {
          f.style.setProperty("--r", (-dk * 34).toFixed(2) + "deg");
          f.style.setProperty("--s", (1 - a * 0.28).toFixed(3));
        }
        if (a < nd) { nd = a; nah = i; }
      });
      /* --o wird NICHT mehr aus dem Abstand gerechnet. Zwei gleich
         weit entfernte Felder bekaemen denselben Wert, und beim
         Wischen standen dadurch zwei halbdurchsichtige Flaschen im
         Bild statt einer ganzen (gemessen: bei halbem Zug beide auf
         .41 bzw. .40). Hier faellt die Entscheidung: das naechste
         Feld bekommt 1, alle anderen 0. Die Blende macht das CSS
         ueber die Zeit. */
      if (!ruhig) {
        felder.forEach(function (f, i) {
          f.style.setProperty("--o", i === nah ? "1" : "0");
        });
      }
      /* Was man nicht sieht, darf man auch nicht treffen.
         Deckkraft 0 nimmt einem Feld nur das Aussehen, nicht die
         Klickflaeche. Die Nachbarflaschen sind unsichtbar, lagen aber
         weiter links und rechts der mittleren: man sah die Wiese,
         tippte darauf, und die Flasche wechselte die Farbe. Auf dem
         Handy trifft der Daumen diese Flaechen staendig.
         Nur bei !ruhig - bei reduzierter Bewegung setzt die Schleife
         oben kein --o, dann sind alle sechs sichtbar und muessen
         antippbar bleiben. Gewischt wird in beiden Faellen weiter:
         das Scrollen liegt auf der Liste, nicht auf den Feldern. */
      if (!ruhig) {
        felder.forEach(function (f, i) {
          f.style.pointerEvents = (i === nah) ? "" : "none";
        });
      }
      if (nah !== aktiv) { aktiv = nah; uebernehmen(nah); }
    };
    var anstoss = function () {
      if (malt) return;
      malt = true;
      W.requestAnimationFrame(malen);
    };

    var zu = function (i, hart) {
      i = Math.max(0, Math.min(felder.length - 1, i));
      var f = felder[i];
      var ziel = f.offsetLeft - (gal.clientWidth - f.offsetWidth) / 2;
      if (gal.scrollTo) gal.scrollTo({ left: ziel, behavior: (hart || ruhig) ? "auto" : "smooth" });
      else gal.scrollLeft = ziel;
    };

    gal.addEventListener("scroll", anstoss, { passive: true });
    W.addEventListener("resize", function () { zu(aktiv < 0 ? 0 : aktiv, true); anstoss(); });

    pfeile.forEach(function (b) {
      b.addEventListener("click", function () {
        zu(aktiv + parseInt(b.getAttribute("data-gal-schritt"), 10));
      });
    });

    gal.addEventListener("keydown", function (e) {
      if (e.key === "ArrowLeft")  { e.preventDefault(); zu(aktiv - 1); }
      if (e.key === "ArrowRight") { e.preventDefault(); zu(aktiv + 1); }
    });

    // Farbpunkte unter dem Preis fuehren die Galerie mit.
    punkte.forEach(function (p) {
      p.addEventListener("click", function () {
        var id = p.getAttribute("data-variante");
        for (var i = 0; i < felder.length; i++) {
          if (felder[i].getAttribute("data-variante") === id) { zu(i); return; }
        }
      });
    });

    /* Ziehen mit der Maus. Nur fuer die Maus - Finger und Stift
       scrollen bereits nativ, und beides gleichzeitig gaebe doppelte
       Bewegung. */
    if (W.PointerEvent) {
      var zieht = false, startX = 0, startL = 0, bewegt = 0;
      gal.addEventListener("pointerdown", function (e) {
        if (e.pointerType !== "mouse" || e.button !== 0) return;
        zieht = true; bewegt = 0;
        startX = e.clientX; startL = gal.scrollLeft;
        gal.style.scrollSnapType = "none";
        gal.style.cursor = "grabbing";
      });
      gal.addEventListener("pointermove", function (e) {
        if (!zieht) return;
        var dx = e.clientX - startX;
        bewegt = Math.max(bewegt, Math.abs(dx));
        gal.scrollLeft = startL - dx;
      });
      var loslassen = function () {
        if (!zieht) return;
        zieht = false;
        gal.style.cursor = "grab";
        gal.style.scrollSnapType = "";
        // Einrasten nachholen: ohne das bleibt die Spur zwischen zwei
        // Feldern stehen, weil scroll-snap waehrend des Zugs aus war.
        zu(aktiv);
      };
      gal.addEventListener("pointerup", loslassen);
      gal.addEventListener("pointerleave", loslassen);
      gal.addEventListener("pointercancel", loslassen);
      gal.style.cursor = "grab";
    }

    // Startstellung: die bereits gewaehlte Farbe in die Mitte.
    var start = 0;
    for (var i0 = 0; i0 < punkte.length; i0++) {
      if (punkte[i0].getAttribute("aria-pressed") === "true") {
        var sid = punkte[i0].getAttribute("data-variante");
        for (var j0 = 0; j0 < felder.length; j0++) {
          if (felder[j0].getAttribute("data-variante") === sid) { start = j0; break; }
        }
        break;
      }
    }
    aktiv = start;
    zu(start, true);
    anzeigen(start);
    anstoss();
    // Schriften kommen nach und koennen die Buehne noch um ein paar
    // Pixel verschieben. Danach einmal nachzentrieren.
    W.addEventListener("load", function () { zu(aktiv, true); anstoss(); });
  }

  /* ---------- 9. Rundumblick ----------------------------------------
     Der Knopf steht nur im HTML, wenn echte 360-Grad-Aufnahmen als
     Theme-Dateien liegen; die Begruendung steht im Kopf von
     n-start.liquid. Faellt auch nur ein Einzelbild aus, geht der
     Betrachter gar nicht erst auf - eine Drehung mit Luecken ist
     schlechter als keine. */
  var rundKnopf = $("[data-rundum]");
  if (rundKnopf && gal) {
    var anzahl  = parseInt(rundKnopf.getAttribute("data-bilder"), 10) || 0;
    var spalten = parseInt(rundKnopf.getAttribute("data-spalten"), 10) || 1;
    var zeilen  = Math.ceil(anzahl / spalten);
    var vorlage = rundKnopf.getAttribute("data-vorlage") || "";

    /* Es gibt die 36 Aufnahmen nicht von jeder Farbe. Welche sie hat,
       steht in data-farben. Fuer alle anderen verschwindet der Knopf,
       statt dass er dasteht und beim Druck nichts tut. Die Liste ist
       der einzige Ort, an dem das gepflegt wird - kommt eine Farbe
       dazu, wird sie in n-start.liquid ergaenzt, sonst nichts. */
    var habenBilder = (rundKnopf.getAttribute("data-farben") || "")
                        .split(",").map(function (s) { return s.trim(); })
                        .filter(function (s) { return s.length; });

    var knopfPruefen = function (slug) {
      var da = !habenBilder.length || habenBilder.indexOf(slug) !== -1;
      // Gemessen: das Attribut hidden allein reicht nicht. Die Regel
      // .n-gal__rundum setzt display, und display schlaegt hidden -
      // der Knopf blieb bei jeder Farbe stehen. Deshalb zusaetzlich
      // hart am Element, das gewinnt gegen jede Klasse.
      rundKnopf.hidden = !da;
      rundKnopf.style.display = da ? "" : "none";
    };
    D.addEventListener("n:farbe", function (e) {
      knopfPruefen((e.detail && e.detail.slug) || "");
    });

    var laden = function (slug) {
      // Ein einziger Auftrag: der Bogen mit allen Ansichten. Kommt er
      // nicht, gibt es auch keinen halben Rundumblick.
      return new Promise(function (fertig, daneben) {
        var b = new Image();
        b.onload = function () { fertig(b.src); };
        b.onerror = daneben;
        b.src = vorlage.replace("FARBE", slug);
      });
    };

    var oeffnen = function (bogen, name) {
      var stand = 0;
      // Kein img, sondern eine Flaeche mit dem Bogen als Hintergrund.
      // role und aria-label geben ihr denselben Rang wie ein Bild,
      // damit ein Vorleseprogramm nichts verliert.
      var bild = el("div", { klasse: "n-rund__bogen", role: "img",
        "aria-label": "Trinkflasche in " + name + ", rundum gedreht" });
      bild.style.backgroundImage = "url(" + bogen + ")";
      bild.style.setProperty("--sp", spalten);
      bild.style.setProperty("--ze", zeilen);

      var hinweis = el("p", { klasse: "n-rund__hinweis",
        text: "Ziehen zum Drehen · Escape schliesst" });
      var zu2 = el("button", { klasse: "n-rund__zu", type: "button",
        "aria-label": "Rundumblick schliessen", text: "✕" });
      var kasten = el("div", { klasse: "n-rund", role: "dialog",
        "aria-modal": "true", "aria-label": "Rundumblick" }, [bild, hinweis, zu2]);

      var zeigen = function (i) {
        stand = ((i % anzahl) + anzahl) % anzahl;
        // Bei background-size in Prozent zaehlt nicht der Pixelversatz,
        // sondern der Anteil an der UEBERSTEHENDEN Flaeche. Bei sechs
        // Spalten sind das fuenf Schritte, nicht sechs - deshalb der
        // Nenner minus eins.
        var sx = spalten > 1 ? (stand % spalten) * 100 / (spalten - 1) : 0;
        var sy = zeilen  > 1 ? Math.floor(stand / spalten) * 100 / (zeilen - 1) : 0;
        bild.style.backgroundPosition = sx + "% " + sy + "%";
      };
      zeigen(0);
      var aktivX = 0, haelt = false;
      kasten.addEventListener("pointerdown", function (e) {
        haelt = true; aktivX = e.clientX; kasten.setPointerCapture(e.pointerId);
      });
      kasten.addEventListener("pointermove", function (e) {
        if (!haelt) return;
        var dx = e.clientX - aktivX;
        var schritt = Math.round(dx / 12);
        if (schritt) { zeigen(stand - schritt); aktivX = e.clientX; }
      });
      kasten.addEventListener("pointerup",     function () { haelt = false; });
      kasten.addEventListener("pointercancel", function () { haelt = false; });

      var schliessen = function () {
        D.removeEventListener("keydown", taste);
        if (kasten.parentNode) kasten.parentNode.removeChild(kasten);
        D.body.style.overflow = "";
        rundKnopf.focus();
      };
      var taste = function (e) {
        if (e.key === "Escape") schliessen();
        if (e.key === "ArrowLeft")  zeigen(stand - 1);
        if (e.key === "ArrowRight") zeigen(stand + 1);
      };
      zu2.addEventListener("click", schliessen);
      D.addEventListener("keydown", taste);
      D.body.style.overflow = "hidden";
      D.body.appendChild(kasten);
      zu2.focus();
    };

    // Beim Aufbau einmal pruefen: die Galerie meldet die Farbe erst,
    // wenn sich etwas aendert, und beim ersten Bild aendert sich nichts.
    var erst = felder[aktiv] || felder[0];
    knopfPruefen(erst ? (erst.getAttribute("data-slug") || "") : "");

    rundKnopf.addEventListener("click", function () {
      var f = felder[aktiv] || felder[0];
      if (!f) return;
      var slug = f.getAttribute("data-slug");
      var name = f.getAttribute("aria-label") || "";
      rundKnopf.disabled = true;
      laden(slug).then(function (bilder) {
        rundKnopf.disabled = false;
        oeffnen(bilder, name.split(": ").pop());
      }).catch(function () {
        // Fehlt auch nur ein Bild, passiert nichts weiter, als dass der
        // Knopf verschwindet. Kein halber Rundumblick.
        rundKnopf.parentNode && rundKnopf.parentNode.removeChild(rundKnopf);
      });
    });
  }

  /* ---------- 10. Farbstreifen unter "Such dir eine aus" -------------
     Derselbe Gedanke wie bei der Galerie: gescrollt wird nativ, die
     Pfeile sind nur die Zugabe fuer alle Faelle, in denen Wischen nicht
     ankommt. Sie erscheinen nur, wenn es wirklich etwas zu scrollen
     gibt. */
  var streifen = D.querySelector("[data-streifen]");
  if (streifen) {
    var spur = $("[data-streifen-spur]", streifen);
    var spfeile = $$("[data-streifen-schritt]", streifen);
    if (spur && spfeile.length) {
      var pruefen = function () {
        var scrollbar = spur.scrollWidth > spur.clientWidth + 2;
        spfeile.forEach(function (b) {
          b.hidden = !scrollbar;
          var sch = parseInt(b.getAttribute("data-streifen-schritt"), 10);
          if (!scrollbar) return;
          b.disabled = sch < 0
            ? spur.scrollLeft <= 2
            : spur.scrollLeft >= spur.scrollWidth - spur.clientWidth - 2;
        });
      };
      spfeile.forEach(function (b) {
        b.addEventListener("click", function () {
          var sch = parseInt(b.getAttribute("data-streifen-schritt"), 10);
          var karte = spur.querySelector("li");
          var weite = karte ? karte.getBoundingClientRect().width + 13 : spur.clientWidth * 0.7;
          spur.scrollBy({ left: sch * weite * 2, behavior: ruhig ? "auto" : "smooth" });
        });
      });
      spur.addEventListener("scroll", pruefen, { passive: true });
      W.addEventListener("resize", pruefen);
      pruefen();
      W.addEventListener("load", pruefen);
    }
  }

  /* ---------- 11 · MENGE UND FARBE JE FLASCHE ----------------------
     Neun Feldgruppen stehen im HTML, eine je Flasche. Ausgeschaltet
     sind die Plaetze oberhalb der gewaehlten Menge - ein
     ausgeschaltetes Feld schickt der Browser nicht mit, genau das ist
     der Schalter. VERSTECKT sind alle ausser der gerade bearbeiteten;
     versteckte Felder schickt er sehr wohl mit.

     Der Konfigurator hat zwei Schritte: oben ein Streifen mit den
     echten Flaschenaufnahmen (antippen waehlt aus), darunter EINE
     Farbreihe fuer die gewaehlte Flasche. Damit stehen nie mehr als
     sechs Punkte gleichzeitig da, egal ob zwei oder neun Flaschen.

     Faellt dieses Skript aus, bleibt der ganze Block versteckt und
     der Kunde kauft genau eine Flasche in der oben gewaehlten Farbe.
     Das ist der gewollte Rueckfall. */
  (function () {
    var form = $("form[data-kaufform]");
    if (!form) return;
    var wahlen = $$("[data-mengenwahl]", form);
    if (!wahlen.length) return;
    var zusatz = $$("[data-zusatz]", form);
    /* Alle Knopfbeschriftungen, nicht nur die im Formular. Der
       Schlussknopf am Seitenende ist ein echter Kaufknopf (form=
       "kaufen"), steht aber ausserhalb des Formulars. Suchte man nur
       innerhalb, zeigte er dauerhaft den Preis fuer EINE Flasche,
       waehrend er die oben gewaehlte Menge abschickt - derselbe
       Fehler, der in der Kaufleiste schon behoben ist. */
    var texte  = $$("[data-knopftext]");
    var pfeld  = $("[data-variantenfeld]", form);

    var liste  = $("[data-farbliste]", form);
    var karten = $$("[data-flasche]", form);
    var alle   = $("[data-alle-gleich]", form);
    var aktiv  = 1;

    function istHauptzeile(fs) { return fs.getAttribute("data-zusatz") === "1"; }
    function platzVon(fs) { return parseInt(fs.getAttribute("data-zusatz"), 10); }

    /* Welche Flasche gerade bearbeitet wird. Sichtbar ist immer genau
       EINE Farbreihe - die der angetippten Karte. Die uebrigen sind
       nur VERSTECKT, nicht ausgeschaltet: versteckte Felder schickt
       der Browser mit, ausgeschaltete nicht. */
    function waehleFlasche(platz) {
      aktiv = platz;
      zusatz.forEach(function (fs) {
        var dran = platzVon(fs) === platz && !fs.disabled;
        if (dran) fs.removeAttribute("hidden");
        else      fs.setAttribute("hidden", "");
      });
      karten.forEach(function (k) {
        k.setAttribute("aria-pressed",
          parseInt(k.getAttribute("data-flasche"), 10) === platz ? "true" : "false");
      });
    }

    /* Karte und Beschriftung auf den Stand der Radiofelder bringen. */
    function nachfuehren() {
      zusatz.forEach(function (fs) {
        var an = fs.querySelector("input:checked");
        if (!an) return;
        var platz = platzVon(fs);
        var name  = an.getAttribute("data-name") || "";
        var bild  = an.getAttribute("data-bild");
        var etikett = fs.querySelector("[data-fz-name]");
        if (etikett) etikett.textContent = name;
        var karte = null;
        for (var i = 0; i < karten.length; i++) {
          if (parseInt(karten[i].getAttribute("data-flasche"), 10) === platz) { karte = karten[i]; break; }
        }
        if (karte) {
          var img = karte.querySelector("[data-karte-bild]");
          if (img && bild && img.getAttribute("src") !== bild) img.src = bild;
          karte.setAttribute("aria-label", "Flasche " + platz + ": " + name);
        }
      });
    }

    zusatz.forEach(function (fs) {
      fs.addEventListener("change", function (e) {
        if (istHauptzeile(fs)) {
          /* Flasche 1 ist dieselbe Wahl wie die grossen Farbpunkte
             oben. Der Klick wird dorthin weitergeschoben, damit Bild,
             Preis, Farbname und Adresszeile mitlaufen - statt das ein
             zweites Mal zu programmieren. */
          var id = e.target.value;
          for (var k = 0; k < punkte.length; k++) {
            if (punkte[k].getAttribute("data-variante") === id) { punkte[k].click(); break; }
          }
        } else {
          /* Wer eine Flasche selbst faerbt, soll sie behalten. Ab
             dann fasst das Angleichen sie nicht mehr an. */
          fs.setAttribute("data-selbst", "");
        }
        nachfuehren();
      });
    });

    karten.forEach(function (k) {
      k.addEventListener("click", function () {
        waehleFlasche(parseInt(k.getAttribute("data-flasche"), 10));
      });
    });

    /* "Alle gleich" nimmt die Marken zurueck und faerbt alles auf die
       Farbe von Flasche 1. Ohne diesen Knopf muesste man jede von
       Hand gefaerbte Flasche einzeln zurueckstellen. */
    if (alle) {
      alle.addEventListener("click", function () {
        zusatz.forEach(function (fs) { fs.removeAttribute("data-selbst"); });
        farbenAngleichen();
      });
    }

    /* Ohne das hier stuenden alle weiteren Flaschen auf Rosa, weil das
       die erste Variante im Sortiment ist - auch wenn oben Schwarz
       gewaehlt wurde. Wer mehrere Flaschen nimmt, will sie im Zweifel
       alle in derselben Farbe; wer es anders will, tippt es an. */
    function farbenAngleichen() {
      if (!pfeld || !pfeld.value) return;
      zusatz.forEach(function (fs) {
        if (fs.hasAttribute("data-selbst")) return;   // Hauptzeile hat sie nie
        var r = fs.querySelector('input[value="' + pfeld.value + '"]');
        if (r && !r.disabled) r.checked = true;
      });
      nachfuehren();
    }

    function setzen() {
      var n = 1, gewaehlt = null;
      for (var i = 0; i < wahlen.length; i++) {
        if (wahlen[i].checked) { n = parseInt(wahlen[i].value, 10) || 1; gewaehlt = wahlen[i]; }
      }
      zusatz.forEach(function (fs) {
        var noetig = platzVon(fs) <= n;
        /* Die Gruppe von Flasche 1 nie ausschalten - sie schickt
           ohnehin nichts mit (form="n-nichts") und dient nur der
           Bedienung. */
        if (!istHauptzeile(fs)) fs.disabled = !noetig;
      });
      karten.forEach(function (k) {
        var noetig = parseInt(k.getAttribute("data-flasche"), 10) <= n;
        if (noetig) k.removeAttribute("hidden");
        else        k.setAttribute("hidden", "");
      });
      /* Steht die bearbeitete Flasche nicht mehr im Warenkorb, faellt
         die Auswahl auf die erste zurueck - sonst zeigte der
         Konfigurator die Farbreihe einer Flasche, die es nicht gibt. */
      waehleFlasche(aktiv > n ? 1 : aktiv);
      /* Bei einer Flasche waere der ganze Block eine Wiederholung der
         grossen Punkte zwei Zeilen darueber. */
      if (liste) {
        if (n > 1) liste.removeAttribute("hidden");
        else       liste.setAttribute("hidden", "");
      }
      farbenAngleichen();
      if (texte.length) {
        /* Der Betrag steht am Feld selbst (data-preis) und kommt aus
           Liquid. Frueher wurde er aus der Beschriftung gelesen - das
           brach, sobald sich der Aufbau der Zeile aenderte. */
        var preis = gewaehlt ? (gewaehlt.getAttribute("data-preis") || "") : "";
        /* Frueher stand die Menge vorn ("9 in den Warenkorb · CHF
           239.40"). Auf einem 390er Handy brach das in zwei Zeilen um.
           Wie viele es sind, sagt die gewaehlte Stufe drei Zeilen
           darueber schon. */
        texte.forEach(function (t) {
          t.textContent = "In den Warenkorb · " + preis;
        });
      }
    }
    wahlen.forEach(function (r) { r.addEventListener("change", setzen); });
    setzen();

    /* Die Farbpunkte oben aendern Flasche 1. Sie schreiben in
       data-variantenfeld, das jetzt items[0][id] heisst - der Name
       hat sich geaendert, das Merkmal nicht. Die uebrigen Flaschen
       ziehen nach, sofern sie nicht von Hand gesetzt wurden. */
    if (pfeld && pfeld.name.indexOf("items[") !== 0) {
      pfeld.name = "items[0][id]";
    }
    D.addEventListener("click", function (e) {
      if (!e.target.closest) return;
      if (e.target.closest("[data-farbe], [data-gal-feld]")) setTimeout(farbenAngleichen, 0);
    });
  })();

  /* ---------- 12 · FRAGEN-CHAT ------------------------------------
     Er hat KEINEN eigenen Antworttext. Beim ersten Oeffnen liest er
     die Fragen und Antworten aus dem Wissensblock im Seitencode und
     gibt sie woertlich weiter. Steht etwas dort nicht, kann er es
     nicht sagen - dann bleibt der Weg zu einer echten Person.

     Kein Sprachmodell, kein Netzaufruf, kein Speichern, kein Cookie. */
  (function () {
    var auf   = $("[data-chat-auf]");
    var kasten= $("[data-chat]");
    if (!auf || !kasten) return;
    var lauf  = $("[data-chat-lauf]", kasten);
    var wahl  = $("[data-chat-wahl]", kasten);
    var zu    = $("[data-chat-zu]", kasten);

    // Quelle: der sichtbare Frageblock, sonst der versteckte im Kopf.
    var quelle = $("[data-wissen]");
    if (!quelle) return;

    var paare = [];
    $$("details", quelle).forEach(function (d) {
      var f = $("summary", d);
      var a = $(".n-frage__inhalt", d) || d;
      if (!f) return;
      paare.push({ frage: f.textContent.trim(), antwort: a.cloneNode(true) });
    });
    if (!paare.length) return;

    var gestartet = false;

    function blase(art, inhalt) {
      var b = el("div", { klasse: "n-chat__b n-chat__b--" + art });
      if (typeof inhalt === "string") b.textContent = inhalt;
      else {
        // Die Antwort wird als DOM uebernommen, damit Links erhalten
        // bleiben - aber ohne Skripte oder Formulare aus der Quelle.
        $$("script, form, iframe", inhalt).forEach(function (x) { x.remove(); });
        while (inhalt.firstChild) b.appendChild(inhalt.firstChild);
      }
      lauf.appendChild(b);
      lauf.scrollTop = lauf.scrollHeight;
      return b;
    }

    function knoepfe() {
      wahl.textContent = "";
      paare.forEach(function (p, i) {
        var k = el("button", { klasse: "n-chat__frage", type: "button", text: p.frage });
        k.addEventListener("click", function () {
          blase("ich", p.frage);
          var kopie = p.antwort.cloneNode(true);
          W.setTimeout(function () { blase("shop", kopie); }, ruhig ? 0 : 260);
        });
        wahl.appendChild(k);
      });
    }

    function oeffnen() {
      kasten.removeAttribute("hidden");
      // Ein Bild frueher als die Klasse, sonst faellt die Bewegung aus.
      W.requestAnimationFrame(function () { kasten.classList.add("n-offen"); });
      auf.setAttribute("aria-expanded", "true");
      if (!gestartet) {
        gestartet = true;
        blase("shop", "Hallo. Such dir eine Frage aus - die Antworten kommen "
                    + "direkt aus dem Shop, Wort fuer Wort.");
        knoepfe();
      }
      W.setTimeout(function () { if (zu) zu.focus({ preventScroll: true }); }, 60);
    }
    function schliessen() {
      kasten.classList.remove("n-offen");
      auf.setAttribute("aria-expanded", "false");
      W.setTimeout(function () {
        if (!kasten.classList.contains("n-offen")) kasten.setAttribute("hidden", "");
      }, 240);
      auf.focus({ preventScroll: true });
    }

    auf.addEventListener("click", function () {
      if (kasten.classList.contains("n-offen")) schliessen(); else oeffnen();
    });
    if (zu) zu.addEventListener("click", schliessen);
    D.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && kasten.classList.contains("n-offen")) schliessen();
    });
  })();

  W.__nNova = true;
})();

/* =====================================================================
   Intro-Vorhang — Zeitplan und Notausgang
   9.8.2026.

   Der Vorhang selbst ist reines CSS: der Regen faellt, die Wortmarke
   zieht sich aus der Unschaerfe scharf, der Claim steigt auf. Dieses
   Stueck macht nur zweierlei: es hebt ihn zum richtigen Zeitpunkt, und
   es sorgt dafuer, dass er sich immer heben laesst.

   Gehoben wird, wenn die Wortmarke fertig aufgezogen ist - nicht nach
   einer festen Zahl Millisekunden ab Skriptstart. Gemessen lag der
   Abstand zwischen Kopf-Skript und erstem Bildaufbau zwischen 0.15 s
   und 0.8 s; mit einer festen Wartezeit haette der Vorhang genau dort
   die Marke mitten in der Bewegung abgeschnitten.
   ===================================================================== */
(function () {
  "use strict";

  var W = window, D = document;
  var wurzel = D.documentElement;
  if (!wurzel.classList.contains("n-intro")) return;

  var vorhang = D.querySelector("[data-vorhang]");
  if (!vorhang) { wurzel.classList.remove("n-intro"); return; }

  var NACHLAUF = 800;               // Atempause, nachdem die Marke steht
  var MINDEST  = 1700;              // Standzeit ab dem ersten gezeichneten Bild
  var DECKEL   = 3000;              // spaetestens dann hebt er, egal was war
  var LIFT     = 1000;              // Hebe-Bewegung, siehe CSS
  var weg      = false;

  function heben() {
    if (weg) return;
    weg = true;

    // Einmal pro Sitzung. Wer weiterklickt, sieht ihn nicht noch mal.
    try { sessionStorage.setItem("n-vorhang", "1"); } catch (e) {}

    var hero = D.querySelector(".n-hero");
    if (hero) hero.classList.add("n-eintritt");

    vorhang.classList.add("n-hebt");
    W.setTimeout(function () {
      wurzel.classList.remove("n-intro");        // gibt das Scrollen frei
      if (vorhang.parentNode) vorhang.parentNode.removeChild(vorhang);
    }, LIFT);
  }

  /* Der Vorhang haengt an der Animation, nicht an einer Stoppuhr.
     Eine feste Wartezeit ab Skriptstart schneidet die Wortmarke auf
     langsamen Geraeten ab - gemessen lag der Abstand zwischen Kopf-
     Skript und erstem Bildaufbau zwischen 0.15 s und 0.8 s. Darum:
     abwarten, bis die Wortmarke wirklich scharf steht, dann noch
     einen Atemzug, dann heben. */
  /* Zwei Uhren, und es gilt die spaetere.

     Die eine haengt an der Wortmarke: ist sie scharf, noch ein
     Atemzug, dann heben. Die andere ist eine Mindeststandzeit ab dem
     ersten gezeichneten Bild. Beide allein sind falsch: kommt das
     Ereignis nie (weil die Marke schon fertig war, als wir zuhoerten),
     haengt die erste; und die zweite allein wuerde eine langsam
     nachziehende Marke abschneiden. */
  var raf0 = Date.now();
  W.requestAnimationFrame(function () { raf0 = Date.now(); });

  var geplant = false;
  function planen(verzug) {
    if (geplant || weg) return;
    geplant = true;
    var mindestens = raf0 + MINDEST - Date.now();
    W.setTimeout(heben, Math.max(verzug, mindestens, 0));
  }

  var marke = vorhang.querySelector(".n-vorhang__marke");
  if (marke) {
    marke.addEventListener("animationend", function () { planen(NACHLAUF); });
    /* Kein laufender Ablauf heisst entweder "schon fertig" oder "noch
       nicht gestartet" - das laesst sich nicht unterscheiden. Also
       planen und die Mindeststandzeit den Rest machen lassen. */
    if (marke.getAnimations && marke.getAnimations().length === 0) planen(NACHLAUF);
  }
  W.setTimeout(function () { planen(0); }, DECKEL);   // harte Obergrenze

  // Drei Wege hinaus: Taste, Klick irgendwohin, Escape.
  var knopf = D.querySelector("[data-vorhang-weg]");
  if (knopf) knopf.addEventListener("click", heben);
  vorhang.addEventListener("click", heben);
  D.addEventListener("keydown", function (e) {
    if (e.key === "Escape" || e.key === "Enter" || e.key === " ") heben();
  });

  // Wer sofort scrollt, will den Laden sehen, nicht den Vorhang.
  W.addEventListener("wheel", heben, { passive: true, once: true });
  W.addEventListener("touchmove", heben, { passive: true, once: true });
})();

/* ======================================================================
   DER FILM IM BRIEFKASTEN HAELT AN, WENN JEMAND BEWEGUNG ABGESTELLT HAT
   15.8.2026.

   Der Film laeuft stumm in Schleife. Das ist fuer die meisten Leute
   harmlos - fuer manche nicht: wer im Betriebssystem "Bewegung
   reduzieren" gesetzt hat, tut das oft wegen Schwindel oder Migraene,
   und eine Endlosschleife im Blickfeld ist genau der Fall.

   CSS kann ein Video nicht anhalten - deshalb hier. Wir nehmen dem
   Element autoplay weg und halten es an; das Standbild aus poster
   bleibt stehen. Wer die Einstellung waehrend des Besuchs aendert,
   wird gehoert (change am MediaQueryList), damit die Entscheidung in
   beide Richtungen gilt.

   Bewusst KEIN eigener Abspielknopf: er waere ein Bedienelement fuer
   etwas, das nichts erklaert, was nicht auch danebensteht.
   ------------------------------------------------------------------- */
(function () {
  var filme = document.querySelectorAll(".n-brief__film");
  if (!filme.length || !window.matchMedia) return;

  var frage = window.matchMedia("(prefers-reduced-motion: reduce)");

  function richten() {
    for (var i = 0; i < filme.length; i++) {
      var f = filme[i];
      if (frage.matches) {
        f.removeAttribute("autoplay");
        if (!f.paused) f.pause();
      } else if (f.paused && f.readyState > 0) {
        var v = f.play();
        /* play() gibt ein Versprechen zurueck, das der Browser
           ablehnen darf - etwa im Sparmodus. Das ist kein Fehler,
           es bleibt dann eben das Standbild stehen. */
        if (v && v.catch) v.catch(function () {});
      }
    }
  }

  richten();
  if (frage.addEventListener) frage.addEventListener("change", richten);
  else if (frage.addListener) frage.addListener(richten);
})();
