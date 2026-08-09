/* =====================================================================
   v-volt.js — LET'SDRINK VOLT
   9.8.2026. Bauleitung.

   Rund 2 KB, keine Bibliothek. Der vorherige Shop lud GSAP und
   ScrollTrigger - zusammen 116 KB - nur um eine Kamerafahrt zu
   rechnen. VOLT hat keine Kamerafahrt. Es braucht genau zwei Dinge:

     1. Die Kaufleiste einblenden, sobald der Kaufknopf im Hero
        aus dem Bild ist.
     2. Die Farbe wechseln, ohne die Seite neu zu laden.

   Beides ist Zugabe. Ohne JavaScript bleibt der Shop vollstaendig
   kaufbar: die Farbpunkte sind echte Verweise auf ?variant=, das
   Kaufformular ist ein echtes Formular, und die Kaufleiste ist dann
   schlicht nicht da.
   ===================================================================== */
(function () {
  "use strict";

  /* ---------- 1. Kaufleiste ---------------------------------------- */
  var leiste = document.querySelector("[data-leiste]");
  var anker  = document.querySelector("[data-leiste-anker]");

  if (leiste && anker && "IntersectionObserver" in window) {
    // Sichtbar, sobald der Anker (der Kaufknopf im Hero) oben raus ist.
    new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        leiste.classList.toggle("v-an", !e.isIntersecting && e.boundingClientRect.top < 0);
      });
    }, { rootMargin: "0px 0px -100% 0px" }).observe(anker);
  } else if (leiste && anker) {
    // Ohne IntersectionObserver: einfach immer zeigen, sobald gescrollt wurde.
    var pruefe = function () {
      leiste.classList.toggle("v-an", window.scrollY > 400);
    };
    window.addEventListener("scroll", pruefe, { passive: true });
    pruefe();
  }

  /* ---------- 2. Farbwechsel ohne Neuladen -------------------------- */
  var punkte = [].slice.call(document.querySelectorAll("[data-farbe]"));
  if (!punkte.length) return;

  var bild     = document.querySelector("[data-hauptbild]");
  var leistebd = document.querySelector("[data-leistenbild]");
  var name     = document.querySelector("[data-farbname]");
  var feld     = document.querySelector("[data-variantenfeld]");

  function waehle(p, e) {
    var neuesBild = p.getAttribute("data-bild");
    var neuerName = p.getAttribute("data-name");
    var neueId    = p.getAttribute("data-variante");
    if (!neuesBild || !neueId) return;   // unvollstaendig: Link normal folgen lassen

    if (e) e.preventDefault();

    if (bild)     { bild.src = neuesBild; bild.alt = bild.getAttribute("data-alt-vorlage")
                                 ? bild.getAttribute("data-alt-vorlage").replace("%s", neuerName)
                                 : bild.alt; }
    if (leistebd) leistebd.src = neuesBild;
    if (name)     name.textContent = neuerName;
    if (feld)     feld.value = neueId;

    punkte.forEach(function (q) {
      q.setAttribute("aria-pressed", q === p ? "true" : "false");
    });

    // Die Adresszeile mitfuehren, damit Neuladen und Teilen die
    // gewaehlte Farbe behalten.
    if (window.history && window.history.replaceState) {
      try {
        var u = new URL(window.location.href);
        u.searchParams.set("variant", neueId);
        window.history.replaceState({}, "", u);
      } catch (x) { /* aeltere Browser: nicht schlimm */ }
    }
  }

  punkte.forEach(function (p) {
    p.addEventListener("click", function (e) { waehle(p, e); });
    p.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); waehle(p, e); }
    });
  });

  window.__vVolt = true;
})();
