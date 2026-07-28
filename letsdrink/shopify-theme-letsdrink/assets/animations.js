(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.addEventListener("DOMContentLoaded", function () {
    initSmoothAnchors();
    initScrollProgress();
    initStickyHeader();
    initReveal();
    initCountUp();
    initStickyAtc();
    initAddToCartFeedback();
  });

  /* Sanftes Scrollen zu Anker-Links (#faq, #angebot etc.) */
  function initSmoothAnchors() {
    if (reduceMotion) return;
    document.querySelectorAll('a[href*="#"]').forEach(function (link) {
      var url;
      try { url = new URL(link.href); } catch (e) { return; }
      if (url.pathname !== window.location.pathname || !url.hash) return;
      link.addEventListener("click", function (e) {
        var target = document.querySelector(url.hash);
        if (!target) return;
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  /* Fortschrittsbalken oben, zeigt Scroll-Position auf der Seite */
  function initScrollProgress() {
    var bar = document.createElement("div");
    bar.className = "scroll-progress";
    document.body.appendChild(bar);
    function update() {
      var doc = document.documentElement;
      var scrollable = doc.scrollHeight - doc.clientHeight;
      var pct = scrollable > 0 ? (doc.scrollTop / scrollable) * 100 : 0;
      bar.style.width = pct + "%";
    }
    document.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* Header schrumpft leicht nach dem ersten Scrollen */
  function initStickyHeader() {
    var header = document.querySelector(".hd");
    if (!header) return;
    function update() {
      header.classList.toggle("is-scrolled", window.scrollY > 12);
    }
    document.addEventListener("scroll", update, { passive: true });
    update();
  }

  /* Sections/Blöcke sanft einblenden, sobald sichtbar */
  function initReveal() {
    var items = document.querySelectorAll(".reveal");
    if (!items.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("in"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("in");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* Zahlen hochzählen, sobald sichtbar - nur einmal, kurz */
  function initCountUp() {
    var items = document.querySelectorAll("[data-count-to]");
    if (!items.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.textContent = el.getAttribute("data-count-to"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        animateCount(entry.target);
      });
    }, { threshold: 0.4 });
    items.forEach(function (el) { io.observe(el); });
  }

  function animateCount(el) {
    var to = parseInt(el.getAttribute("data-count-to"), 10);
    if (isNaN(to)) return;
    var duration = 900;
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var progress = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(to * eased).toString();
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  /* Sticky Add-to-Cart-Bar: erscheint, sobald der Haupt-Button aus dem Bild scrollt */
  function initStickyAtc() {
    var mainBtn = document.getElementById("pdp-add-btn");
    var bar = document.getElementById("sticky-atc");
    if (!mainBtn || !bar) return;
    if (!("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        bar.classList.toggle("is-visible", !entry.isIntersecting && entry.boundingClientRect.top < 0);
      });
    }, { threshold: 0 });
    io.observe(mainBtn);

    var barBtn = bar.querySelector("[data-sticky-submit]");
    var form = document.getElementById("product-form");
    if (barBtn && form) {
      barBtn.addEventListener("click", function () {
        if (typeof form.requestSubmit === "function") form.requestSubmit();
        else form.submit();
      });
    }
  }

  /* Kurzes, dezentes Erfolgs-Feedback nach "In den Warenkorb" */
  function initAddToCartFeedback() {
    var form = document.getElementById("product-form");
    var btn = document.getElementById("pdp-add-btn");
    if (!form || !btn) return;

    form.addEventListener("submit", function () {
      // Aktion zuerst, Feedback verzögert den Klick nicht.
      window.setTimeout(function () {
        btn.classList.add("is-success");
        if (!reduceMotion) burstConfetti(btn);
        window.setTimeout(function () { btn.classList.remove("is-success"); }, 1400);
      }, 50);
    });
  }

  /* Sehr dezenter Konfetti-Effekt: wenige Punkte, kurz, kein externes Skript */
  function burstConfetti(anchorEl) {
    var rect = anchorEl.getBoundingClientRect();
    var count = 8;
    for (var i = 0; i < count; i++) {
      var dot = document.createElement("span");
      dot.className = "confetti-dot";
      var angle = (Math.PI * 2 * i) / count;
      var dist = 28 + Math.random() * 14;
      dot.style.setProperty("--dx", Math.cos(angle) * dist + "px");
      dot.style.setProperty("--dy", Math.sin(angle) * dist + "px");
      dot.style.left = rect.left + rect.width / 2 + "px";
      dot.style.top = rect.top + window.scrollY + rect.height / 2 + "px";
      document.body.appendChild(dot);
      /* eslint-disable-next-line no-loop-func */
      dot.addEventListener("animationend", function () { this.remove(); });
    }
  }
})();
