/* ==========================================================================
   BAU- & HOLZWERKER AG  |  script.js  (Demo von NATE.digital)
   Rein clientseitig, keine Abhängigkeiten.
   ========================================================================== */
(function () {
  "use strict";

  /* ------------------------------------------------------------------
     0. Demo-Hinweis-Banner (schliessbar)
     ------------------------------------------------------------------ */
  var demoBanner = document.getElementById("demo-banner");
  var demoBannerClose = demoBanner && demoBanner.querySelector(".demo-banner-close");
  if (demoBanner && demoBannerClose) {
    demoBannerClose.addEventListener("click", function () {
      demoBanner.classList.add("is-hidden");
    });
  }

  /* ------------------------------------------------------------------
     1. Mobile Navigation
     ------------------------------------------------------------------ */
  var navToggle = document.querySelector(".nav-toggle");
  var siteNav = document.getElementById("hauptnavigation");

  function closeNav() {
    document.body.classList.remove("nav-open");
    if (navToggle) {
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "Menü öffnen");
    }
  }

  if (navToggle && siteNav) {
    navToggle.addEventListener("click", function () {
      var open = document.body.classList.toggle("nav-open");
      navToggle.setAttribute("aria-expanded", String(open));
      navToggle.setAttribute("aria-label", open ? "Menü schliessen" : "Menü öffnen");
    });

    siteNav.addEventListener("click", function (event) {
      if (event.target.closest("a")) closeNav();
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape") closeNav();
    });
  }

  /* ------------------------------------------------------------------
     2. Header-Schatten beim Scrollen
     ------------------------------------------------------------------ */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ------------------------------------------------------------------
     3. Scroll-Reveal (respektiert prefers-reduced-motion via CSS)
     ------------------------------------------------------------------ */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.1 }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ------------------------------------------------------------------
     4. Offerten-Formular (nur Frontend)
        ANPASSEN: Versand an ein Backend/Formular-Dienst anbinden.
     ------------------------------------------------------------------ */
  var form = document.getElementById("offerte-formular");
  if (form) {
    var successBox = document.getElementById("formular-erfolg");

    function fieldWrapper(input) {
      return input.closest(".form-field");
    }

    function validateField(input) {
      var wrapper = fieldWrapper(input);
      if (!wrapper || !input.required) return true;
      var valid = input.type === "checkbox" ? input.checked : input.checkValidity();
      wrapper.classList.toggle("is-invalid", !valid);
      input.setAttribute("aria-invalid", String(!valid));
      return valid;
    }

    form.querySelectorAll("input, select, textarea").forEach(function (input) {
      input.addEventListener("blur", function () { validateField(input); });
      input.addEventListener("input", function () {
        if (fieldWrapper(input) && fieldWrapper(input).classList.contains("is-invalid")) {
          validateField(input);
        }
      });
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var firstInvalid = null;
      form.querySelectorAll("input, select, textarea").forEach(function (input) {
        if (!validateField(input) && !firstInvalid) firstInvalid = input;
      });

      if (firstInvalid) {
        firstInvalid.focus();
        return;
      }

      /* Demo-Verhalten: Erfolgsmeldung anzeigen und Formular zurücksetzen.
         Hier den echten Versand einbauen, z. B.:
         fetch("/api/offerte", { method: "POST", body: new FormData(form) }) */
      form.reset();
      if (successBox) {
        successBox.classList.add("is-visible");
        successBox.setAttribute("tabindex", "-1");
        successBox.focus();
      }
    });
  }

  /* ------------------------------------------------------------------
     5. Rechtliche Dialoge (Impressum / Datenschutz)
     ------------------------------------------------------------------ */
  document.querySelectorAll("[data-dialog]").forEach(function (trigger) {
    var dialog = document.getElementById(trigger.getAttribute("data-dialog"));
    if (!dialog || typeof dialog.showModal !== "function") return;
    trigger.addEventListener("click", function () { dialog.showModal(); });
  });

  document.querySelectorAll("dialog .dialog-close").forEach(function (button) {
    button.addEventListener("click", function () {
      button.closest("dialog").close();
    });
  });

  document.querySelectorAll("dialog.legal-dialog").forEach(function (dialog) {
    dialog.addEventListener("click", function (event) {
      if (event.target === dialog) dialog.close(); // Klick auf Backdrop
    });
  });

  /* ------------------------------------------------------------------
     6. Jahreszahl im Footer
     ------------------------------------------------------------------ */
  var yearEl = document.getElementById("jahr");
  if (yearEl) yearEl.textContent = String(new Date().getFullYear());
})();

/* Sicherheitsnetz: nichts bleibt dauerhaft unsichtbar (Screenshots, Print, exotische Browser) */
window.addEventListener('load', function () {
  setTimeout(function () {
    document.querySelectorAll('.reveal').forEach(function (el) {
      el.classList.add('is-visible'); el.classList.add('in-view'); el.classList.add('in');
    });
  }, 2000);
});
