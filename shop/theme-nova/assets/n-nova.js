/* =====================================================================
   n-nova.js — LET'SDRINK NOVA
   9.8.2026. Bauleitung.

   Rund 6 KB, keine Bibliothek. Sieben Aufgaben:
     1. Kopfzeile verglasen, sobald gescrollt wird
     2. Scroll-Reveal (IntersectionObserver, kein Scroll-Listener)
     3. Parallaxe der Flasche - EINE rAF-Schleife, sonst nichts
     4. Mobile Navigation
     5. Farbwechsel ohne Neuladen
     6. Warenkorb-Schublade ueber die Shopify-Cart-API
     7. Mitlaufende Kaufleiste

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
      D.body.style.overflow = auf ? "hidden" : "";
      var k = $("[data-mnav-auf]");
      if (k) k.setAttribute("aria-expanded", auf ? "true" : "false");
    };
    var kA = $("[data-mnav-auf]"); if (kA) kA.addEventListener("click", function () { navAuf(true); });
    var kZ = $("[data-mnav-zu]");  if (kZ) kZ.addEventListener("click", function () { navAuf(false); });
    $$("a", mnav).forEach(function (a) { a.addEventListener("click", function () { navAuf(false); }); });
  }

  /* ---------- 5. Farbwechsel ---------------------------------------- */
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

  function franken(rappen) {
    // Shopifys Betraege kommen in der kleinsten Einheit.
    var s = (rappen / 100).toFixed(2).replace(".", ".");
    return geld.replace(/\{\{\s*amount\s*\}\}/, s)
               .replace(/\{\{\s*amount_no_decimals\s*\}\}/, Math.round(rappen / 100))
               .replace(/\{\{\s*amount_with_comma_separator\s*\}\}/, s.replace(".", ","));
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
    D.body.style.overflow = auf ? "hidden" : "";
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
    return fetch(W.Shopify && W.Shopify.routes ? W.Shopify.routes.root + "cart.js" : "/cart.js",
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
      fetch("/cart/change.js", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ line: parseInt(zeile, 10), quantity: neu })
      }).then(function (r) { return r.json(); })
        .then(zeichneKorb)
        .catch(function () { W.location.href = "/cart"; });
    });
  }

  $$("[data-lade-auf]").forEach(function (k) {
    k.addEventListener("click", function (e) { e.preventDefault(); holeKorb(true); });
  });
  $$("[data-lade-zu]").forEach(function (k) {
    k.addEventListener("click", function () { ladeAuf(false); });
  });
  if (schleier) schleier.addEventListener("click", function () { ladeAuf(false); });
  D.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { ladeAuf(false); if (mnav) mnav.classList.remove("n-offen"), D.body.style.overflow = ""; }
  });

  // Kaufformulare abfangen und in die Schublade legen
  $$("form[data-kaufform]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!W.fetch) return;                       // altes Geraet: normal absenden
      e.preventDefault();
      var knopf = $("[type=submit]", f);
      var alt = knopf ? knopf.textContent : "";
      if (knopf) { knopf.disabled = true; knopf.textContent = "Wird hinzugefügt …"; }
      fetch("/cart/add.js", { method: "POST", body: new FormData(f) })
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

  W.__nNova = true;
})();
