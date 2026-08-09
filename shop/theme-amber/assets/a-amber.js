/* =====================================================================
   a-amber.js — die Kamerafahrt
   LET'SDRINK AMBER, 8.8.2026. Bauleitung.

   Nach dem Vorbild aus dem Video (DRIP): Das Produkt ist im Hero
   riesig und diagonal vom Bildrand angeschnitten. Beim Scrollen richtet
   es sich auf, faehrt in die Mitte, und links und rechts erscheinen
   knappe Beschriftungen. Danach die Nahaufnahme, dann die Farben, dann
   das Schlussbild in der Daemmerung.

   FUENF REGELN AUS DEM BAUTEAM, hier eingehalten:
   1. Kein gescrubbtes filter:blur() - die Unschaerfe ist gebacken und
      wird per Deckung ueberblendet.
   2. Kein src-Tausch fuer die Farben - alle sechs liegen
      deckungsgleich uebereinander.
   3. Keine zweite Vollbild-Leinwand.
   4. Kamera und Atem sind getrennte Wrapper.
   5. Die Nahaufnahme kommt aus einem eigenen, hochaufgeloesten Bild.

   ZUSAETZLICH GELERNT, aus dem eigenen Vorgaengerbau:
   Der Kamera-Wrapper braucht ein aspect-ratio. Seine Kinder sind
   absolut positioniert und geben ihm sonst keine Breite - er war 0
   Pixel breit und die Flasche in allen acht Prueffotos unsichtbar.
   ===================================================================== */
(function () {
  "use strict";
  var W = window, D = document, wurzel = D.documentElement;
  var RUHE = W.matchMedia("(prefers-reduced-motion: reduce)");
  W.__aAmber = true;

  function el(s) { return D.querySelector(s); }

  function starten() {
    if (!W.gsap || !W.ScrollTrigger) { wurzel.classList.remove("a-js"); return; }
    gsap.registerPlugin(ScrollTrigger);
    var film = el("[data-film]");
    if (!film) return;
    if (RUHE.matches) { wurzel.classList.add("a-ruhe"); return; }
    fahrt(film);
    atmen();
  }

  function fahrt(film) {
    var buehne = el("[data-buehne]"), kamera = el("[data-kamera]");
    var tiefe = el("[data-tiefe]"), nacht = el("[data-nacht]");
    var scharf = el('[data-fl="tuerkis"]'), unscharf = el("[data-fl-unscharf]");
    var lupe = el("[data-lupe]"), strich = el("[data-strich]");
    var farbname = el("[data-farbname]"), scroll = el("[data-scroll]");
    var s = function (n) { return D.querySelector('[data-szene="' + n + '"]'); };
    var m = function (n) { return D.querySelector('[data-mark="' + n + '"]'); };

    var handy = W.matchMedia("(max-width: 767px)").matches;
    var weg = handy ? 0.5 : 1;

    var tl = gsap.timeline({
      defaults: { ease: "power2.inOut" },
      scrollTrigger: { trigger: film, start: "top top", end: "bottom bottom", scrub: 1 }
    });

    /* --- 0-14  DER HERO -----------------------------------------------
       Die Flasche steht gross und schraeg, vom unteren Rand
       angeschnitten. Beim ersten Scrollen richtet sie sich auf. Der
       Text bewegt sich langsamer als das Produkt - daher die Tiefe. */
    tl.set(kamera, { transformOrigin: "50% 78%" })
      .fromTo(kamera,
        { scale: 1.55, rotate: -17 * weg, xPercent: 16 * weg, yPercent: 26 },
        { scale: 1.42, rotate: -13 * weg, xPercent: 12 * weg, yPercent: 20,
          duration: 14, ease: "power1.inOut" }, 0)
      .fromTo(unscharf, { opacity: 1 }, { opacity: 0, duration: 7, ease: "power1.in" }, 0)
      .fromTo(scharf, { opacity: 0 }, { opacity: 1, duration: 7, ease: "power1.out" }, 0)
      .fromTo(s("hero"), { opacity: 0, yPercent: 14 },
        { opacity: 1, yPercent: 0, duration: 7, ease: "power3.out" }, 1)
      .to(s("hero"), { opacity: 0, yPercent: -10, duration: 6, ease: "power2.in" }, 15)
      .to(scroll, { opacity: 0, duration: 4 }, 6)

    /* --- 14-38  AUFRICHTEN, BESCHRIFTUNGEN -----------------------------
       Das Produkt richtet sich auf und faehrt in die Mitte. Die tiefe
       Zone des Grundes zieht mit, damit die helle Flasche nie auf dem
       hellen Rand steht. Erst danach kommen die Beschriftungen. */
      .to(kamera, { scale: .82, rotate: 0, xPercent: 0, yPercent: 0,
                    duration: 18, ease: "power3.inOut" }, 14)
      .to(tiefe, { xPercent: 0, yPercent: 0, scale: 1, duration: 18, ease: "power3.inOut" }, 14)
      .fromTo(m("l"), { opacity: 0, xPercent: -12 },
        { opacity: 1, xPercent: 0, duration: 6, ease: "power3.out" }, 24)
      .fromTo(m("r"), { opacity: 0, xPercent: 12 },
        { opacity: 1, xPercent: 0, duration: 6, ease: "power3.out" }, 26)
      .to([m("l"), m("r")], { opacity: 0, duration: 5, ease: "power2.in" }, 35)

    /* --- 38-56  DIE NAHAUFNAHME ---------------------------------------
       Die Kamera faehrt an den Knopf. Das Produkt geht teilweise aus
       dem Bild; die Lupe zeigt das Detail scharf. Erst waechst der
       Strich, dann erscheint die Beschriftung. */
      .to(kamera, { scale: 2.0, xPercent: 54 * weg, yPercent: 14,
                    duration: 15, ease: "power2.inOut" }, 38)
      .to(tiefe, { xPercent: 30 * weg, scale: 1.15, duration: 15, ease: "power2.inOut" }, 38)
      .fromTo(lupe, { opacity: 0, scale: .82 },
        { opacity: 1, scale: 1, duration: 7, ease: "power3.out" }, 43)
      .fromTo(strich, { scaleX: 0, opacity: 1 },
        { scaleX: 1, duration: 5, ease: "power2.out" }, 46)
      .fromTo(m("knopf"), { opacity: 0, xPercent: -6 },
        { opacity: 1, xPercent: 0, duration: 4, ease: "power2.out" }, 48.5)
      .to([lupe, strich, m("knopf")], { opacity: 0, duration: 4, ease: "power2.in" }, 53)

    /* --- 56-78  DIE FARBEN --------------------------------------------
       Nicht als Farbfelder, sondern als Kampagne: jede Farbe kommt
       leicht zu gross herein und setzt sich, die vorige geht zurueck. */
      .to(kamera, { scale: .88, xPercent: 0, yPercent: 0, duration: 10, ease: "power3.inOut" }, 55)
      .to(tiefe, { xPercent: 0, scale: 1, duration: 10, ease: "power3.inOut" }, 55)
      .fromTo(farbname, { opacity: 0 }, { opacity: 1, duration: 3 }, 59);

    var F = ["tuerkis", "gruen", "rosa", "grau", "schwarz", "weiss"];
    var N = { tuerkis: "Türkis", gruen: "Grün", rosa: "Rosa",
              grau: "Grau", schwarz: "Schwarz", weiss: "Weiss" };
    F.forEach(function (f, i) {
      if (!i) return;
      var t = 61 + (i - 1) * 2.6;
      tl.to(D.querySelector('[data-fl="' + F[i - 1] + '"]'),
            { opacity: 0, duration: 1.5, ease: "power2.inOut" }, t)
        .fromTo(D.querySelector('[data-fl="' + f + '"]'), { opacity: 0 },
            { opacity: 1, duration: 1.5, ease: "power2.inOut" }, t)
        // Das Produkt setzt sich: leicht zu gross herein, dann auf Mass.
        .fromTo(kamera, { scale: .93 }, { scale: .88, duration: 2.2, ease: "power2.out" }, t)
        .call(function () { if (farbname) farbname.textContent = N[f]; }, null, t + .8);
    });
    // Beim Zurueckscrollen muss der Name wieder stimmen.
    tl.call(function () { if (farbname) farbname.textContent = N.tuerkis; }, null, 60.9);

    /* --- 78-100  DAS SCHLUSSBILD ---------------------------------------
       Die Daemmerung kommt, das Produkt bleibt an derselben Stelle
       stehen. Dadurch liest es sich als Kamerabewegung, nicht als neuer
       Abschnitt. */
    tl.to(farbname, { opacity: 0, duration: 3 }, 76)
      .to(D.querySelector('[data-fl="weiss"]'), { opacity: 0, duration: 5 }, 77)
      .to(scharf, { opacity: 1, duration: 5 }, 77)
      .to(nacht, { opacity: 1, duration: 12, ease: "power2.inOut" }, 78)
      .to(tiefe, { opacity: .35, duration: 12 }, 78)
      .call(function () { buehne.classList.add("a-nachtmodus"); }, null, 82)
      .call(function () { buehne.classList.remove("a-nachtmodus"); }, null, 81.9)
      .to(kamera, { scale: 1.12, duration: 14, ease: "power3.inOut" }, 78)
      .fromTo(s("ende"), { opacity: 0, yPercent: 8 },
        { opacity: 1, yPercent: 0, duration: 8, ease: "power3.out" }, 86);
  }

  /* --- Der Atem: laeuft unabhaengig vom Scroll weiter ----------------- */
  function atmen() {
    var e = el("[data-atem]"); if (!e) return;
    var t0 = 0, id = 0;
    function rahmen(t) {
      if (!t0) t0 = t;
      var s = (t - t0) / 1000;
      e.style.transform = "translate3d(0," + (Math.sin(s * .72) * 5).toFixed(2) + "px,0) rotate("
                        + (Math.sin(s * .48) * .4).toFixed(3) + "deg)";
      id = requestAnimationFrame(rahmen);
    }
    id = requestAnimationFrame(rahmen);
    D.addEventListener("visibilitychange", function () {
      if (D.hidden) { cancelAnimationFrame(id); id = 0; }
      else if (!id) { t0 = 0; id = requestAnimationFrame(rahmen); }
    });
  }

  /* --- Kaufkarte ------------------------------------------------------ */
  function kauf() {
    [].forEach.call(D.querySelectorAll(".a-knopf"), function (k) {
      k.addEventListener("pointermove", function (e) {
        var r = k.getBoundingClientRect();
        k.style.setProperty("--mx", ((e.clientX - r.left) / r.width * 100) + "%");
        k.style.setProperty("--my", ((e.clientY - r.top) / r.height * 100) + "%");
      }, { passive: true });
      k.addEventListener("pointerleave", function () {
        k.style.removeProperty("--mx"); k.style.removeProperty("--my");
      }, { passive: true });
    });

    var p = [].slice.call(D.querySelectorAll("[data-wahl]"));
    var feld = el("[data-variante]"), name = el("[data-kaufname]"), vor = el("[data-vorschau]");
    p.forEach(function (x) {
      x.addEventListener("click", function (e) {
        e.preventDefault();
        p.forEach(function (y) { y.setAttribute("aria-pressed", y === x ? "true" : "false"); });
        if (feld) feld.value = x.getAttribute("data-variante");
        if (name) name.textContent = x.getAttribute("data-name");
        if (vor) vor.setAttribute("src", x.getAttribute("data-bild"));
        if (W.history && history.replaceState) {
          try { var u = new URL(location.href);
                u.searchParams.set("variant", x.getAttribute("data-variante"));
                history.replaceState({}, "", u); } catch (f) {}
        }
      });
    });
  }

  if (D.readyState === "loading")
    D.addEventListener("DOMContentLoaded", function () { starten(); kauf(); });
  else { starten(); kauf(); }
})();
