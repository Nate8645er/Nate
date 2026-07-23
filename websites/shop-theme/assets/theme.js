// Leichtgewichtige, abhängigkeitsfreie Mikro-Animationen fürs Theme.
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Zahlen zählen hoch, sobald die Sektion sichtbar wird.
  function countUp(el) {
    var target = el.getAttribute("data-count");
    var suffix = el.getAttribute("data-suffix") || "";
    var num = parseInt(target, 10);
    if (isNaN(num) || reduce) { el.textContent = target + suffix; return; }
    var start = null, dur = 1400;
    function step(ts) {
      if (start === null) start = ts;
      var p = Math.min((ts - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.round(eased * num).toLocaleString("de-CH") + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  function init() {
    var nums = document.querySelectorAll("[data-count]");
    if (!nums.length) return;
    if (!("IntersectionObserver" in window)) {
      nums.forEach(function (n) { countUp(n); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { countUp(e.target); io.unobserve(e.target); }
      });
    }, { threshold: 0.4 });
    nums.forEach(function (n) { io.observe(n); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else { init(); }
})();

// Cookie-/Consent-Hinweis: schlicht, ohne Tracking. Speichert die Bestätigung
// lokal, damit der Hinweis nur einmal erscheint.
(function () {
  "use strict";
  var KEY = "acc-consent-v1";
  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }
  ready(function () {
    var bar = document.getElementById("consent-bar");
    if (!bar) return;
    var gesetzt;
    try { gesetzt = localStorage.getItem(KEY); } catch (e) { gesetzt = "1"; }
    if (gesetzt) { bar.parentNode && bar.parentNode.removeChild(bar); return; }
    bar.hidden = false;
    bar.addEventListener("click", function (e) {
      var t = e.target;
      if (t && t.hasAttribute && t.hasAttribute("data-consent")) {
        try { localStorage.setItem(KEY, t.getAttribute("data-consent")); } catch (err) {}
        bar.parentNode && bar.parentNode.removeChild(bar);
      }
    });
  });
})();
