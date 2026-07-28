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
    initParallax();
    initHeroMotion();
    initNewsletterPopup();
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

  /* Add-to-Cart läuft jetzt als echter AJAX-Flow, siehe rich-interactions.js,
     initAjaxCart(). Der Konfetti-Effekt bleibt hier, global nutzbar. */
  window.ldConfetti = function (anchorEl) {
    if (reduceMotion) return;
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
      dot.addEventListener("animationend", function () { this.remove(); });
    }
  };

  /* Sehr dezenter Parallax auf dem Hero-Bild: nur EIN Element, gedeckelt,
     nur transform (GPU), kein Effekt auf Layout/Scroll-Performance */
  function initParallax() {
    if (reduceMotion) return;
    var el = document.querySelector("[data-parallax]");
    if (!el || window.innerWidth < 990) return;
    var ticking = false;
    function update() {
      var rect = el.getBoundingClientRect();
      var offset = Math.max(-24, Math.min(24, rect.top * 0.06));
      el.style.transform = "translateY(" + offset + "px)";
      ticking = false;
    }
    document.addEventListener("scroll", function () {
      if (!ticking) {
        window.requestAnimationFrame(update);
        ticking = true;
      }
    }, { passive: true });
    update();
  }

  /* Hero-Bild: sanftes Schweben (Zeit-basiert) + Maus-Tilt, EIN kombinierter
     Transform pro Frame, damit sich beide Effekte nicht überschreiben.
     Nur Desktop, nur wenn nicht reduced-motion. */
  function initHeroMotion() {
    if (reduceMotion || window.innerWidth < 990) return;
    var el = document.querySelector(".tilt-target");
    if (!el) return;

    var rx = 0, ry = 0; // Ziel-Rotation aus Mausposition
    var crx = 0, cry = 0; // aktuelle, sanft angenäherte Rotation
    var start = null;

    document.addEventListener("mousemove", function (e) {
      var rect = el.getBoundingClientRect();
      var relX = (e.clientX - rect.left) / rect.width - 0.5;
      var relY = (e.clientY - rect.top) / rect.height - 0.5;
      ry = relX * 6;
      rx = relY * -6;
    }, { passive: true });

    function frame(ts) {
      if (!start) start = ts;
      var t = (ts - start) / 1000;
      var bob = Math.sin(t * (Math.PI / 2.75)) * 8;
      crx += (rx - crx) * 0.06;
      cry += (ry - cry) * 0.06;
      el.style.transform =
        "perspective(900px) rotateX(" + crx.toFixed(2) + "deg) rotateY(" + cry.toFixed(2) + "deg) translateY(" + bob.toFixed(1) + "px)";
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /* Newsletter-Popup: erscheint einmal pro Sitzung, nach Verzögerung oder
     wenn die Seite zu 60% gescrollt wurde. Kein Effekt auf LCP (verzögert
     geladen), Escape und Klick auf Overlay schliessen. */
  function initNewsletterPopup() {
    var overlay = document.getElementById("nl-popup-overlay");
    if (!overlay) return;
    if (sessionStorage.getItem("ld_newsletter_seen")) return;

    function open() {
      if (sessionStorage.getItem("ld_newsletter_seen")) return;
      overlay.hidden = false;
      requestAnimationFrame(function () { overlay.classList.add("is-open"); });
      sessionStorage.setItem("ld_newsletter_seen", "1");
      var firstInput = overlay.querySelector("input");
      if (firstInput) firstInput.focus();
    }
    function close() {
      overlay.classList.remove("is-open");
      window.setTimeout(function () { overlay.hidden = true; }, 250);
    }

    overlay.querySelectorAll("[data-nl-close]").forEach(function (btn) {
      btn.addEventListener("click", close);
    });
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) close();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && overlay.classList.contains("is-open")) close();
    });

    window.setTimeout(open, 8000);
    window.addEventListener("scroll", function () {
      var doc = document.documentElement;
      var pct = (doc.scrollTop / (doc.scrollHeight - doc.clientHeight)) * 100;
      if (pct > 60) open();
    }, { passive: true });
  }

})();
