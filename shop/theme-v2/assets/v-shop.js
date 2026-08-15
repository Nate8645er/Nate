/* ===================================================================
   LET'SDRINK — v2
   15.8.2026. Neubau.

   GRUNDSATZ: Ohne dieses Skript muss die Seite VERKAUFEN KOENNEN.
   Das Kaufformular ist ein echtes Formular mit echten Feldern. Die
   Farbpunkte sind Links auf ?variant=. Faellt das Skript aus, laedt
   ein Klick die Seite neu und alles funktioniert weiter - langsamer,
   aber vollstaendig. Nichts hier ist Voraussetzung fuer einen Kauf.

   Vier Aufgaben, mehr nicht:
     1  der Demoknopf
     2  die Farbwahl ohne Neuladen
     3  die mitlaufende Kaufleiste
     4  die Knopfbeschriftungen gleich halten
   =================================================================== */
(function () {
  "use strict";

  var D = document;
  var $  = function (w, e) { return (e || D).querySelector(w); };
  var $$ = function (w, e) { return Array.prototype.slice.call((e || D).querySelectorAll(w)); };

  var ruhig = window.matchMedia &&
              window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------------------------------------------------------------
     1 · DER DEMOKNOPF

     Halten laesst den Wasserstand steigen, Loslassen laesst ihn
     zurueckfliessen. Die Zeiten sind absichtlich ungleich: 1.2 s
     hoch, 0.8 s runter. Wasser, das zurueckfliesst, ist schneller
     als Wasser, das hochgedrueckt wird - und genau dieser
     Unterschied ist es, der die Bewegung echt wirken laesst.

     Die Zeitsteuerung liegt im CSS (transition auf der Hoehe), nicht
     hier. Das Skript setzt nur zwei Zustaende: voll oder leer.
     --------------------------------------------------------------- */
  (function () {
    var knopf = $("[data-demo]");
    if (!knopf) return;
    var wasser = $(".v-demo__wasser", knopf);
    var text   = $("[data-demo-text]", knopf);
    if (!wasser) return;

    var urtext = text ? text.textContent : "";
    var haelt = false;

    function fuellen() {
      if (haelt) return;
      haelt = true;
      knopf.removeAttribute("data-los");
      wasser.style.setProperty("--stand", "100%");
      if (text) text.textContent = "Napf füllt sich …";
      /* Ein kurzer Stups, sofern das Geraet es kann. Zehn
         Millisekunden sind unter der Schwelle, ab der es stoert -
         man spuert es, ohne dass es vibriert. */
      if (navigator.vibrate && !ruhig) { try { navigator.vibrate(10); } catch (e) {} }
    }

    function leeren() {
      if (!haelt) return;
      haelt = false;
      knopf.setAttribute("data-los", "");
      wasser.style.setProperty("--stand", "0%");
      if (text) text.textContent = "Wasser läuft zurück – nochmal?";
      window.setTimeout(function () {
        if (!haelt && text) text.textContent = urtext;
      }, 1400);
    }

    /* Pointer-Ereignisse decken Maus, Finger und Stift gemeinsam ab.
       pointercancel muss mit: wer waehrend des Haltens scrollt,
       bekommt sonst einen Knopf, der fuer immer voll bleibt. */
    knopf.addEventListener("pointerdown", function (e) { e.preventDefault(); fuellen(); });
    knopf.addEventListener("pointerup", leeren);
    knopf.addEventListener("pointerleave", leeren);
    knopf.addEventListener("pointercancel", leeren);

    /* Mit der Tastatur bedienbar: Leertaste oder Eingabe halten.
       Ohne das waere die einzige Interaktion der Seite fuer alle
       unerreichbar, die keine Maus benutzen. */
    knopf.addEventListener("keydown", function (e) {
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); fuellen(); }
    });
    knopf.addEventListener("keyup", function (e) {
      if (e.key === " " || e.key === "Enter") { e.preventDefault(); leeren(); }
    });
    knopf.addEventListener("blur", leeren);
  })();

  /* ---------------------------------------------------------------
     2 · FARBWAHL

     Die Punkte sind echte Links auf ?variant=. Das Skript faengt den
     Klick ab und tauscht Bild, Name und das versteckte Variantenfeld
     aus, statt die Seite neu zu laden. Die Adresszeile laeuft mit,
     damit ein geteilter Link die richtige Farbe zeigt.
     --------------------------------------------------------------- */
  (function () {
    var punkte = $$("[data-farbe]");
    if (!punkte.length) return;
    var bild  = $("[data-flaschenbild]");
    var name  = $("[data-farbname]");
    var feld  = $("[data-variantenfeld]");

    punkte.forEach(function (p) {
      p.addEventListener("click", function (e) {
        if (!window.history || !window.history.replaceState) return;  /* dann eben neu laden */
        e.preventDefault();

        punkte.forEach(function (q) { q.setAttribute("aria-pressed", "false"); });
        p.setAttribute("aria-pressed", "true");

        var neu = p.getAttribute("data-bild");
        if (bild && neu) {
          bild.src = neu;
          bild.alt = "Trinkflasche mit fest angebautem Napf für Hund und Katze, 550 ml, in "
                   + (p.getAttribute("data-name") || "");
        }
        if (name) name.textContent = p.getAttribute("data-name") || "";
        if (feld) feld.value = p.getAttribute("data-variante") || feld.value;

        try { window.history.replaceState({}, "", p.getAttribute("href")); } catch (err) {}
      });
    });
  })();

  /* ---------------------------------------------------------------
     3 · DIE MITLAUFENDE KAUFLEISTE

     Sie erscheint, sobald der Kaufknopf oben aus dem Bild ist, und
     verschwindet wieder, wenn er zurueckkommt. Sie zeigt BEWUSST
     keinen Betrag: sie kennt die gewaehlte Menge nicht, und ein
     falscher Preis am Ort des Kaufs ist schlimmer als gar keiner.
     Genau dieser Fehler steckte in der alten Fassung - dort stand
     der Einzelpreis daneben, waehrend der Knopf ein Buendel
     abschickte.
     --------------------------------------------------------------- */
  (function () {
    var leiste = $("[data-leiste]");
    var anker  = $("[data-leiste-anker]");
    if (!leiste || !anker || !window.IntersectionObserver) return;

    new IntersectionObserver(function (eintraege) {
      eintraege.forEach(function (e) {
        if (e.isIntersecting) leiste.removeAttribute("data-an");
        else if (e.boundingClientRect.top < 0) leiste.setAttribute("data-an", "");
        else leiste.removeAttribute("data-an");
      });
    }, { threshold: 0 }).observe(anker);
  })();

  /* ---------------------------------------------------------------
     4 · KNOPFBESCHRIFTUNGEN GLEICH HALTEN

     Es gibt drei Kaufknoepfe auf der Seite: oben im Formular, unten
     im Plakat und in der Leiste. Die ersten beiden tragen einen
     Betrag. Sollte spaeter wieder eine Mengenwahl dazukommen, muss
     sie ALLE Beschriftungen nachfuehren - sonst steht auf einem
     Knopf ein anderer Betrag als auf dem naechsten. Deshalb wird
     hier dokumentweit gesucht und nicht innerhalb des Formulars.
     --------------------------------------------------------------- */
  window.vSetzeKnopftext = function (txt) {
    $$("[data-knopftext]").forEach(function (t) { t.textContent = txt; });
  };
})();
