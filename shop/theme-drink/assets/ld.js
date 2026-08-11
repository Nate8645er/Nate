/* ====================================================================
   LET'SDRINK — ld.js

   WAS DIESE DATEI IST UND WAS SIE NICHT IST

   Sie ist kein Framework und benutzt keins. Keine Bibliothek wird
   nachgeladen, kein CDN angefragt. Das ist keine Sparsamkeit um ihrer
   selbst willen: eine Animationsbibliothek waere hier 40 bis 70 KB,
   die vor dem ersten Bild geladen und ausgewertet werden muessten -
   auf einer Seite, deren ganzer Zweck der erste Eindruck ist.

   DAS GRUNDPRINZIP: EINE SCHLEIFE, EINE ZAHL
   Es gibt genau EINEN requestAnimationFrame-Lauf fuer die ganze
   Seite. Er schreibt auf jede Szene eine Zahl zwischen 0 und 1
   (--p) und sonst nichts. Wie diese Zahl aussieht, entscheidet
   allein das CSS. Deshalb steht in dieser Datei kein einziger
   Farbwert und keine Pixelangabe fuer ein Aussehen.

   Zwoelf Szenen kosten so zwoelf Zuweisungen pro Bild - nicht zwoelf
   Animationen. Und weil nur eine Custom Property gesetzt wird,
   rechnet der Browser kein Layout neu.

   DIE SEITE FUNKTIONIERT OHNE DIESE DATEI
   Faellt sie aus, bleibt .ld-js weg, und das CSS zeigt alles im
   Ruhezustand: sichtbar, lesbar, kaufbar. Diese Datei macht die
   Seite schoener, nicht benutzbar.

   INHALT
   1  Handwerkszeug
   2  Der Bildlauf (--p)
   3  Hereingleiten
   4  Filme
   5  Kopf und Menue
   6  Warenkorb (Lade, Hinzufuegen, Mengen)
   7  Produktseite
   8  Erkunden
   9  Enthuellung
   ==================================================================== */

(function () {
  "use strict";

  /* ==================================================================
     1 · HANDWERKSZEUG
     ================================================================== */

  var wurzel = document.documentElement;
  var K = window.LD || {};
  var ruhig = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function $(w, in_) { return (in_ || document).querySelector(w); }
  function $$(w, in_) { return Array.prototype.slice.call((in_ || document).querySelectorAll(w)); }
  function klemm(z, min, max) { return z < min ? min : z > max ? max : z; }

  /* Geldbetraege kommen von Shopify in Rappen. Das Format steht im
     Konto und wird aus Liquid durchgereicht - hier wird kein
     Waehrungszeichen erfunden. */
  function geld(rappen) {
    var form = K.geldform || "CHF {{amount}}";
    var z = (rappen || 0) / 100;
    function mitPunkt(n, tr, dez) {
      var teile = n.toFixed(2).split(".");
      teile[0] = teile[0].replace(/\B(?=(\d{3})+(?!\d))/g, tr);
      return dez ? teile.join(dez) : teile[0];
    }
    return form
      .replace(/\{\{\s*amount\s*\}\}/g, mitPunkt(z, "'", "."))
      .replace(/\{\{\s*amount_no_decimals\s*\}\}/g, mitPunkt(Math.round(z), "'", ""))
      .replace(/\{\{\s*amount_with_comma_separator\s*\}\}/g, mitPunkt(z, ".", ","))
      .replace(/\{\{\s*amount_no_decimals_with_comma_separator\s*\}\}/g, mitPunkt(Math.round(z), ".", ""));
  }

  /* Alles, was aus /cart.js in HTML wandert, geht vorher hier durch.
     Produkttitel und Variantennamen kommen zwar aus dem eigenen
     Shopify-Konto und nicht von Fremden - aber eine Zeichenkette,
     die ungeprueft in innerHTML landet, ist eine Luecke, die man
     spaeter uebersieht. Einmal entschaerfen kostet nichts. */
  function sicher(text) {
    return String(text == null ? "" : text)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  /* Der Fokus darf eine offene Lade oder ein offenes Menue nicht
     verlassen - sonst tippt man sich blind durch die Seite
     dahinter. */
  function fokusFangen(kasten, ereignis) {
    if (ereignis.key !== "Tab") return;
    var koenner = $$('a[href],button:not([disabled]),input:not([disabled]),select,textarea,[tabindex]:not([tabindex="-1"])', kasten)
      .filter(function (e) { return e.offsetParent !== null; });
    if (!koenner.length) return;
    var erst = koenner[0], letzt = koenner[koenner.length - 1];
    if (ereignis.shiftKey && document.activeElement === erst) { ereignis.preventDefault(); letzt.focus(); }
    else if (!ereignis.shiftKey && document.activeElement === letzt) { ereignis.preventDefault(); erst.focus(); }
  }


  /* ==================================================================
     2 · DER BILDLAUF

     Fuer jede Szene: wie weit ist sie durch das Fenster gewandert?
     0 = sie kommt gerade oben an, 1 = sie geht gerade hinaus.

     Eine sticky-Szene ist hoeher als das Fenster; dann ist die
     Strecke (Hoehe - Fensterhoehe). Eine Szene, die genau so hoch
     ist wie das Fenster (der Hero), hat diese Strecke nicht - dort
     wird an der Fensterhoehe gemessen.
     ================================================================== */

  var szenen = [];
  var laeuftSchon = false;

  function szenenSammeln() {
    szenen = $$("[data-szene]").map(function (el) {
      return { el: el, letzt: -1 };
    });
  }

  function szenenRechnen() {
    laeuftSchon = false;
    var fenster = window.innerHeight;

    for (var i = 0; i < szenen.length; i++) {
      var s = szenen[i];
      var r = s.el.getBoundingClientRect();

      /* Ausserhalb des Blickfelds gar nicht erst rechnen. Der Wert
         wird trotzdem einmal auf 0 bzw. 1 festgesetzt, damit keine
         Szene auf halbem Stand einfriert. */
      if (r.bottom < -200 || r.top > fenster + 200) {
        var rand = r.bottom < 0 ? 1 : 0;
        if (s.letzt !== rand) { s.el.style.setProperty("--p", rand); s.letzt = rand; }
        continue;
      }

      var strecke = s.el.offsetHeight - fenster;
      var p = strecke > 40 ? -r.top / strecke : -r.top / fenster;
      p = klemm(p, 0, 1);

      /* Auf drei Stellen runden: das Auge sieht keinen Unterschied,
         der Browser spart sich tausende Neuzeichnungen. */
      p = Math.round(p * 1000) / 1000;
      if (p !== s.letzt) { s.el.style.setProperty("--p", p); s.letzt = p; }
    }

    schritteSetzen();
  }

  function anstossen() {
    if (laeuftSchon) return;
    laeuftSchon = true;
    requestAnimationFrame(szenenRechnen);
  }


  /* ==================================================================
     3 · HEREINGLEITEN
     ================================================================== */

  function gleitenStarten() {
    var elemente = $$("[data-auf]");
    if (!elemente.length) return;

    if (!("IntersectionObserver" in window)) {
      elemente.forEach(function (e) { e.classList.add("ist-da"); });
      return;
    }

    var waechter = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (!e.isIntersecting) return;
        e.target.classList.add("ist-da");
        waechter.unobserve(e.target);   /* genau einmal, nie wieder */
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.05 });

    elemente.forEach(function (e) { waechter.observe(e); });
  }


  /* ==================================================================
     4 · FILME

     Die Quellen stehen als data-quelle im HTML und werden erst hier
     gesetzt. Vorher laedt kein Byte. Das ist der Unterschied
     zwischen einer Seite, die auf dem Handy in zwei Sekunden steht,
     und einer, die zwanzig Megabyte zieht, bevor der erste Satz
     lesbar ist.

     Bei "Bewegung reduzieren" wird gar nichts geladen - dann bleibt
     das Standbild stehen, das ohnehin schon da ist.
     ================================================================== */

  function filmeStarten() {
    var filme = $$("[data-film]");
    if (!filme.length || ruhig) return;

    function anwerfen(v) {
      if (v.dataset.geladen) return;
      $$("source", v).forEach(function (q) {
        if (q.dataset.quelle) q.src = q.dataset.quelle;
      });
      v.dataset.geladen = "1";
      v.load();
      var versuch = v.play();
      if (versuch && versuch.catch) versuch.catch(function () { /* Autoplay abgelehnt: Standbild bleibt. */ });
      var sektion = v.closest("section");
      if (sektion) sektion.classList.add("ist-film");
    }

    if (!("IntersectionObserver" in window)) { filme.forEach(anwerfen); return; }

    var waechter = new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (e.isIntersecting) {
          anwerfen(e.target);
          if (e.target.paused && !e.target.dataset.handbetrieb) {
            var p = e.target.play(); if (p && p.catch) p.catch(function () {});
          }
        } else if (!e.target.paused && !e.target.dataset.handbetrieb) {
          /* Ausserhalb des Bilds anhalten spart Akku und Rechenzeit. */
          e.target.pause();
        }
      });
    }, { rootMargin: "220px 0px", threshold: 0.01 });

    filme.forEach(function (v) { waechter.observe(v); });
  }

  /* Tonknopf am Filmstreifen. */
  function tonStarten() {
    $$("[data-ton]").forEach(function (knopf) {
      knopf.addEventListener("click", function () {
        var v = $("video", knopf.closest(".ld-streifen__fenster"));
        if (!v) return;
        v.muted = !v.muted;
        knopf.setAttribute("aria-pressed", String(!v.muted));
        var an = $("[data-ton-an]", knopf), aus = $("[data-ton-aus]", knopf);
        if (an) an.hidden = v.muted;
        if (aus) aus.hidden = !v.muted;
        $(".ld-nur-lese", knopf).textContent = v.muted ? "Ton einschalten" : "Ton ausschalten";
      });
    });
  }


  /* ==================================================================
     5 · KOPF UND MENUE
     ================================================================== */

  function kopfStarten() {
    var kopf = $("[data-kopf]");
    if (!kopf) return;
    var fest = false;
    function pruefen() {
      var soll = window.scrollY > 24;
      if (soll !== fest) { fest = soll; kopf.classList.toggle("ist-fest", soll); }
    }
    pruefen();
    window.addEventListener("scroll", pruefen, { passive: true });
  }

  function menueStarten() {
    var menue = $("[data-menue]");
    var auf = $("[data-menue-auf]");
    if (!menue || !auf) return;
    var vorher = null;

    function oeffnen() {
      vorher = document.activeElement;
      menue.hidden = false;
      requestAnimationFrame(function () { menue.classList.add("ist-auf"); });
      auf.setAttribute("aria-expanded", "true");
      document.body.style.overflow = "hidden";
      var erst = $("a, button", menue);
      if (erst) erst.focus();
    }
    function schliessen() {
      menue.classList.remove("ist-auf");
      auf.setAttribute("aria-expanded", "false");
      document.body.style.overflow = "";
      setTimeout(function () { menue.hidden = true; }, 280);
      if (vorher) vorher.focus();
    }

    auf.addEventListener("click", oeffnen);
    $$("[data-menue-zu]").forEach(function (z) { z.addEventListener("click", schliessen); });
    $$("a", menue).forEach(function (a) { a.addEventListener("click", schliessen); });
    menue.addEventListener("keydown", function (e) {
      if (e.key === "Escape") schliessen();
      fokusFangen(menue, e);
    });
  }


  /* ==================================================================
     6 · WARENKORB
     ================================================================== */

  var lade = $("[data-lade]");

  function korbZahlSetzen(anzahl) {
    var z = $("[data-korb-zahl]");
    if (!z) return;
    z.textContent = anzahl;
    z.hidden = anzahl === 0;
  }

  function ladeFuellen(korb) {
    var leib = $("[data-lade-leib]");
    var fuss = $("[data-lade-fuss]");
    if (!leib) return;

    if (!korb.items || !korb.items.length) {
      leib.innerHTML = '<p class="ld-lade__leer">Dein Warenkorb ist leer.</p>';
      if (fuss) fuss.hidden = true;
      return;
    }

    leib.innerHTML = korb.items.map(function (z) {
      var bild = z.image
        ? '<img src="' + sicher(z.image.replace(/(\.[a-z]+)(\?|$)/i, "_160x$1$2")) + '" alt="" width="62" height="62" loading="lazy">'
        : "<span></span>";
      var farbe = z.variant_title ? "<span>" + sicher(z.variant_title) + "</span>" : "";
      return '<div class="ld-ladezeile">' + bild +
             '<div class="ld-ladezeile__wort"><b>' + sicher(z.product_title) + "</b>" + farbe +
             "<span>" + sicher(z.quantity) + " × " + sicher(geld(z.final_price)) + "</span></div>" +
             '<span class="ld-ladezeile__geld">' + sicher(geld(z.final_line_price)) + "</span></div>";
    }).join("");

    if (fuss) {
      fuss.hidden = false;
      var summe = $("[data-lade-summe]");
      if (summe) summe.textContent = geld(korb.total_price);
    }
  }

  function korbHolen() {
    return fetch(K.korbUrl || "/cart.js", { headers: { Accept: "application/json" } })
      .then(function (a) { return a.json(); })
      .then(function (korb) {
        korbZahlSetzen(korb.item_count);
        ladeFuellen(korb);
        return korb;
      });
  }

  function ladeOeffnen() {
    if (!lade) return;
    lade.hidden = false;
    requestAnimationFrame(function () { lade.classList.add("ist-auf"); });
    document.body.style.overflow = "hidden";
    var zu = $("[data-lade-zu]", lade);
    if (zu) zu.focus();
  }
  function ladeSchliessen() {
    if (!lade) return;
    lade.classList.remove("ist-auf");
    document.body.style.overflow = "";
    setTimeout(function () { lade.hidden = true; }, 340);
  }

  function korbStarten() {
    if (lade) {
      $$("[data-lade-zu]").forEach(function (z) { z.addEventListener("click", ladeSchliessen); });
      lade.addEventListener("keydown", function (e) {
        if (e.key === "Escape") ladeSchliessen();
        fokusFangen(lade, e);
      });
      /* Der Knopf im Kopf ist ein echter Verweis auf /cart. Erst
         wenn JS da ist, faengt er den Klick ab und oeffnet die
         Lade. Ohne JS landet man auf der Warenkorbseite - beides
         fuehrt zum Ziel. */
      var korbAuf = $("[data-korb-auf]");
      if (korbAuf) {
        korbAuf.addEventListener("click", function (e) {
          e.preventDefault();
          korbHolen().then(ladeOeffnen);
        });
      }
    }

    /* --- Hinzufuegen --- */
    var form = $("#ld-kauf-form");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var knopf = $("[data-kaufknopf]", form);
        var wort = $("[data-kaufwort]", knopf);
        var fehler = $("[data-kauf-fehler]");
        var alt = wort ? wort.textContent : "";

        knopf.disabled = true;
        if (wort) wort.textContent = "Einen Moment …";
        if (fehler) fehler.hidden = true;

        fetch("/cart/add.js", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({
            id: Number($("[data-variante-feld]", form).value),
            quantity: Number($("[data-menge-feld]", form).value) || 1
          })
        })
          .then(function (a) { return a.json().then(function (d) { return { ok: a.ok, d: d }; }); })
          .then(function (r) {
            if (!r.ok) throw new Error(r.d.description || r.d.message || "Das hat nicht geklappt.");
            return korbHolen();
          })
          .then(function () {
            ladeOeffnen();
          })
          .catch(function (f) {
            if (fehler) { fehler.textContent = f.message; fehler.hidden = false; }
          })
          .then(function () {
            knopf.disabled = false;
            if (wort) wort.textContent = alt;
          });
      });
    }

    /* --- Mengen auf der Warenkorbseite --- */
    var korbform = $("[data-korbform]");
    if (korbform) {
      function aendern(schluessel, menge) {
        fetch("/cart/change.js", {
          method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ id: schluessel, quantity: menge })
        }).then(function () { window.location.reload(); });
      }

      korbform.addEventListener("click", function (e) {
        var stufe = e.target.closest("[data-korb-menge]");
        if (stufe) {
          e.preventDefault();
          var feld = $('[data-korb-feld][data-schluessel="' + stufe.dataset.schluessel + '"]', korbform);
          var neu = Math.max(0, (Number(feld.value) || 0) + Number(stufe.dataset.korbMenge));
          aendern(stufe.dataset.schluessel, neu);
          return;
        }
        var weg = e.target.closest("[data-korb-weg]");
        if (weg) { e.preventDefault(); aendern(weg.dataset.schluessel, 0); }
      });

      $$("[data-korb-feld]", korbform).forEach(function (feld) {
        feld.addEventListener("change", function () {
          aendern(feld.dataset.schluessel, Math.max(0, Number(feld.value) || 0));
        });
      });
    }
  }


  /* ==================================================================
     7 · PRODUKTSEITE
     ================================================================== */

  function pdpStarten() {
    var pdp = $("[data-pdp]");
    if (!pdp) return;

    var daten = null;
    try { daten = JSON.parse(pdp.dataset.produkt); } catch (e) { daten = null; }

    /* --- Menge --- */
    $$("[data-menge]", pdp).forEach(function (knopf) {
      knopf.addEventListener("click", function () {
        var feld = $("[data-menge-feld]", pdp);
        var neu = klemm((Number(feld.value) || 1) + Number(knopf.dataset.menge), 1, 99);
        feld.value = neu;
      });
    });

    /* --- Galerie --- */
    function bildZeigen(id) {
      $$("[data-medium]", pdp).forEach(function (f) {
        var trifft = f.dataset.medium === String(id);
        if (trifft) f.removeAttribute("data-versteckt");
        else f.setAttribute("data-versteckt", "1");
        var v = $("video", f);
        if (v) { if (trifft) { var p = v.play(); if (p && p.catch) p.catch(function(){}); } else v.pause(); }
      });
      $$("[data-daumen]", pdp).forEach(function (d) {
        d.setAttribute("aria-pressed", String(d.dataset.daumen === String(id)));
      });
    }

    $$("[data-daumen]", pdp).forEach(function (d) {
      d.addEventListener("click", function () { bildZeigen(d.dataset.daumen); });
    });

    /* --- Bildlupe --- */
    var lupe = $("[data-lupe]", pdp);
    if (lupe) {
      var lupeBild = $("[data-lupe-bild]", lupe);
      var lupeAuf = $("[data-lupe-auf]", pdp);
      if (lupeAuf) {
        lupeAuf.addEventListener("click", function () {
          var sichtbar = $$("[data-medium]", pdp).filter(function (f) { return !f.hasAttribute("data-versteckt"); })[0];
          var img = sichtbar && $("img", sichtbar);
          if (!img) return;
          lupeBild.src = img.dataset.lupe || img.src;
          lupeBild.alt = img.alt;
          lupe.hidden = false;
          requestAnimationFrame(function () { lupe.classList.add("ist-auf"); });
          document.body.style.overflow = "hidden";
          $("[data-lupe-zu]", lupe).focus();
        });
      }
      function lupeZu() {
        lupe.classList.remove("ist-auf");
        document.body.style.overflow = "";
        setTimeout(function () { lupe.hidden = true; }, 260);
      }
      $("[data-lupe-zu]", lupe).addEventListener("click", lupeZu);
      lupe.addEventListener("click", function (e) { if (e.target === lupe) lupeZu(); });
      document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !lupe.hidden) lupeZu(); });
    }

    /* --- Variante waehlen ---
       Aus den angehakten Radios wird die Kombination gebildet und
       in den Produktdaten gesucht. Danach wandern Preis, Bild,
       Knopfzustand und die Adresszeile mit. */
    function varianteFinden() {
      if (!daten) return null;
      var gewaehlt = $$('input[data-option]:checked', pdp).map(function (r) { return r.value; });
      for (var i = 0; i < daten.variants.length; i++) {
        var v = daten.variants[i];
        var passt = true;
        for (var o = 0; o < gewaehlt.length; o++) {
          if (v.options[o] !== gewaehlt[o]) { passt = false; break; }
        }
        if (passt) return v;
      }
      return null;
    }

    function variantenWechsel() {
      var v = varianteFinden();
      if (!v) return;

      $("[data-variante-feld]", pdp).value = v.id;

      /* Preis: dieselbe Rechnung wie in snippets/ld-preis.liquid.
         Sie steht hier ein zweites Mal, weil JS nicht auf Liquid
         zugreifen kann - der Faktor kommt aber aus derselben
         Quelle, die Liquid in window.LD schreibt. Es gibt also
         weiterhin genau EINE Zahl, die gepflegt werden muss. */
      var echt = Math.ceil(v.price * (K.rabattFaktor != null ? K.rabattFaktor : 1));
      var preis = $("[data-preis]", pdp);
      if (preis) preis.textContent = geld(echt);

      var alt = $("[data-alt]", pdp);
      if (alt) {
        if (v.compare_at_price && v.compare_at_price > v.price) { alt.textContent = geld(v.compare_at_price); alt.hidden = false; }
        else alt.hidden = true;
      }

      var name = $('[data-wahl-name="1"]', pdp);
      if (name) name.textContent = v.options[0];

      var knopf = $("[data-kaufknopf]", pdp);
      var wort = $("[data-kaufwort]", pdp);
      if (knopf) knopf.disabled = !v.available;
      if (wort) wort.textContent = v.available ? "In den Warenkorb" : "Ausverkauft";

      var lPreis = $("[data-leiste-preis]", pdp);
      if (lPreis) lPreis.textContent = geld(echt);
      var lFarbe = $("[data-leiste-farbe]", pdp);
      if (lFarbe) lFarbe.textContent = v.options[0];
      var lBild = $("[data-leiste-bild]", pdp);
      if (lBild && v.featured_image) lBild.src = v.featured_image.src.replace(/(\.[a-z]+)(\?|$)/i, "_120x$1$2");

      if (v.featured_image && v.featured_image.id) bildZeigen(v.featured_image.id);

      /* Die Adresszeile mitfuehren, damit ein geteilter Link die
         gewaehlte Farbe zeigt. replaceState statt pushState: der
         Zurueck-Knopf soll die Seite verlassen, nicht durch sechs
         Farben zurueckklicken. */
      if (window.history && history.replaceState) {
        var u = new URL(window.location.href);
        u.searchParams.set("variant", v.id);
        history.replaceState({}, "", u.toString());
      }
    }

    $$('input[data-option]', pdp).forEach(function (r) {
      r.addEventListener("change", variantenWechsel);
    });

    /* --- mitlaufende Leiste ---
       Sie erscheint genau dann, wenn der echte Kaufknopf aus dem
       Bild ist. Nie beide gleichzeitig. */
    var leiste = $("[data-leiste]", pdp);
    var kaufknopf = $("[data-kaufknopf]", pdp);
    if (leiste && kaufknopf && "IntersectionObserver" in window) {
      leiste.hidden = false;
      var waechter = new IntersectionObserver(function (eintraege) {
        var drin = eintraege[0].isIntersecting;
        leiste.classList.toggle("ist-da", !drin);
      }, { threshold: 0 });
      waechter.observe(kaufknopf);

      var lKaufen = $("[data-leiste-kaufen]", leiste);
      if (lKaufen) {
        lKaufen.addEventListener("click", function () {
          if (kaufknopf.disabled) return;
          $("#ld-kauf-form").requestSubmit ? $("#ld-kauf-form").requestSubmit() : kaufknopf.click();
        });
      }
    }
  }


  /* ==================================================================
     8 · ERKUNDEN

     Ziehen verschiebt die Abspielposition des Dreh-Films. Der Film
     wird dafuer angehalten (data-handbetrieb), damit die Schleife
     aus Abschnitt 4 ihn nicht wieder anwirft.
     ================================================================== */

  function erkundenStarten() {
    var teil = $("[data-erkunden]");
    if (!teil) return;

    /* --- Farbe --- */
    $$("[data-farbe]", teil).forEach(function (knopf) {
      knopf.addEventListener("click", function () {
        if (knopf.hasAttribute("data-weg")) return;
        $$("[data-farbe]", teil).forEach(function (k) { k.setAttribute("aria-pressed", "false"); });
        knopf.setAttribute("aria-pressed", "true");

        $$("[data-farbbild]", teil).forEach(function (b) {
          b.hidden = b.dataset.farbbild !== knopf.dataset.farbe;
        });
        var name = $("[data-farbname]", teil);
        if (name) name.textContent = knopf.dataset.name;

        /* Wer eine Farbe waehlt, will das Standbild sehen, nicht
           den Dreh-Film. */
        var rahmen = $("[data-dreh]", teil);
        if (rahmen) rahmen.classList.remove("ist-dreh");
      });
    });

    /* --- Punkte am Produkt --- */
    $$("[data-punkt]", teil).forEach(function (punkt) {
      punkt.addEventListener("click", function () {
        $$("[data-punkt]", teil).forEach(function (p) { p.setAttribute("aria-pressed", "false"); });
        punkt.setAttribute("aria-pressed", "true");
        $$("[data-tafel]", teil).forEach(function (t) {
          t.hidden = t.dataset.tafel !== punkt.dataset.punkt;
        });
      });
    });
    var ersterPunkt = $("[data-punkt]", teil);
    if (ersterPunkt) ersterPunkt.setAttribute("aria-pressed", "true");

    /* --- Drehen --- */
    var rahmen = $("[data-drehbar]", teil);
    var film = $("[data-dreh-film]", teil);
    if (!rahmen || !film || ruhig) return;

    var zieht = false, startX = 0, startZeit = 0, dauer = 0;

    function quellenSetzen() {
      if (film.dataset.geladen) return;
      $$("source", film).forEach(function (q) { if (q.dataset.quelle) q.src = q.dataset.quelle; });
      film.dataset.geladen = "1";
      film.dataset.handbetrieb = "1";
      film.load();
    }

    film.addEventListener("loadedmetadata", function () {
      dauer = film.duration || 0;
      rahmen.classList.add("ist-dreh");
    });

    /* Erst laden, wenn der Abschnitt wirklich in Sicht kommt. */
    if ("IntersectionObserver" in window) {
      var w = new IntersectionObserver(function (e) {
        if (e[0].isIntersecting) { quellenSetzen(); w.disconnect(); }
      }, { rootMargin: "260px 0px" });
      w.observe(rahmen);
    } else { quellenSetzen(); }

    function los(x) { zieht = true; startX = x; startZeit = film.currentTime || 0; rahmen.classList.add("ist-gedreht"); }
    function zieh(x) {
      if (!zieht || !dauer) return;
      /* Die volle Rahmenbreite entspricht einer ganzen Filmlaenge.
         So fuehlt sich das Ziehen auf jedem Bildschirm gleich an. */
      var anteil = (x - startX) / rahmen.offsetWidth;
      var neu = startZeit + anteil * dauer;
      /* Umlaufend: ueber das Ende hinaus geht es vorn weiter -
         genau wie bei einem echten Drehteller. */
      neu = ((neu % dauer) + dauer) % dauer;
      film.currentTime = neu;
    }
    function halt() { zieht = false; }

    rahmen.addEventListener("pointerdown", function (e) { rahmen.setPointerCapture(e.pointerId); los(e.clientX); });
    rahmen.addEventListener("pointermove", function (e) { if (zieht) { e.preventDefault(); zieh(e.clientX); } });
    rahmen.addEventListener("pointerup", halt);
    rahmen.addEventListener("pointercancel", halt);

    /* Mit der Tastatur ebenfalls drehbar. */
    rahmen.setAttribute("tabindex", "0");
    rahmen.addEventListener("keydown", function (e) {
      if (!dauer) return;
      if (e.key === "ArrowRight") { film.currentTime = (film.currentTime + dauer / 12) % dauer; e.preventDefault(); }
      if (e.key === "ArrowLeft")  { film.currentTime = (film.currentTime - dauer / 12 + dauer) % dauer; e.preventDefault(); }
      rahmen.classList.add("ist-gedreht");
    });
  }


  /* ==================================================================
     9 · ENTHUELLUNG

     Die vier Zeilen loesen einander ab. Welche gilt, ergibt sich aus
     --p der Sektion: bei vier Zeilen gehoert das erste Viertel der
     ersten Zeile, und so weiter. Die letzte Zeile bleibt bis zum
     Ende stehen, statt am Schluss zu verschwinden - der Gedanke soll
     ankommen, nicht verpuffen.
     ================================================================== */

  var schrittGruppen = [];

  function schritteSammeln() {
    schrittGruppen = $$(".ld-schritte").map(function (gruppe) {
      return {
        szene: gruppe.closest("[data-szene]"),
        zeilen: $$(".ld-schritt", gruppe),
        letzt: -1
      };
    }).filter(function (g) { return g.szene && g.zeilen.length; });
  }

  function schritteSetzen() {
    for (var i = 0; i < schrittGruppen.length; i++) {
      var g = schrittGruppen[i];
      var p = parseFloat(g.szene.style.getPropertyValue("--p")) || 0;
      /* Die ersten 12 Prozent gehoeren noch der Ueberschrift. */
      var lauf = klemm((p - 0.12) / 0.82, 0, 0.9999);
      var jetzt = Math.floor(lauf * g.zeilen.length);
      if (jetzt === g.letzt) continue;
      g.letzt = jetzt;
      for (var z = 0; z < g.zeilen.length; z++) {
        g.zeilen[z].classList.toggle("ist-da", z === jetzt);
      }
    }
  }


  /* ==================================================================
     START
     ================================================================== */

  function start() {
    szenenSammeln();
    schritteSammeln();
    szenenRechnen();

    gleitenStarten();
    filmeStarten();
    tonStarten();
    kopfStarten();
    menueStarten();
    korbStarten();
    pdpStarten();
    erkundenStarten();

    window.addEventListener("scroll", anstossen, { passive: true });
    window.addEventListener("resize", function () { szenenSammeln(); anstossen(); }, { passive: true });

    /* Im Theme-Editor werden Sektionen neu geladen, ohne dass die
       Seite neu laedt. Ohne diese Haken waere der Editor nach der
       ersten Aenderung tot. */
    document.addEventListener("shopify:section:load", function () {
      szenenSammeln(); schritteSammeln(); anstossen();
      gleitenStarten(); filmeStarten(); pdpStarten(); erkundenStarten();
    });
    document.addEventListener("shopify:section:unload", function () {
      szenenSammeln(); schritteSammeln();
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();

  void wurzel;
})();
