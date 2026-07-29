/* ============================================================
   RESTAURANT-VORLAGE · script.js
   Reines Vanilla-JS, keine Abhaengigkeiten.
   Bausteine: Mobile-Navigation, Header-Zustand, Scroll-Reveal,
   Heute-Markierung der Oeffnungszeiten, Formular-Validierung.
   ============================================================ */

(function () {
  "use strict";

  var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Mobile-Navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var panel = document.getElementById("nav-panel");

  if (toggle && panel) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.setAttribute("aria-label", open ? "Menü öffnen" : "Menü schliessen");
      panel.classList.toggle("is-open", !open);
    });

    // Menue schliessen, sobald ein Ziel gewaehlt wurde
    panel.addEventListener("click", function (event) {
      if (event.target.closest("a")) {
        toggle.setAttribute("aria-expanded", "false");
        toggle.setAttribute("aria-label", "Menü öffnen");
        panel.classList.remove("is-open");
      }
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && panel.classList.contains("is-open")) {
        toggle.setAttribute("aria-expanded", "false");
        panel.classList.remove("is-open");
        toggle.focus();
      }
    });
  }

  /* ---------- Header: Linie erst nach dem Scrollen ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- Scroll-Reveal (deaktiviert bei reduced motion) ---------- */
  var revealTargets = document.querySelectorAll(".reveal");
  if (revealTargets.length && "IntersectionObserver" in window && !prefersReducedMotion) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
    );
    revealTargets.forEach(function (el) { observer.observe(el); });
  } else {
    revealTargets.forEach(function (el) { el.classList.add("is-visible"); });
  }

  /* ---------- Oeffnungszeiten: heutigen Tag markieren ---------- */
  var todayRow = document.querySelector(
    '#hours-table tr[data-day="' + new Date().getDay() + '"]'
  );
  if (todayRow) {
    todayRow.classList.add("is-today");
    var badge = document.createElement("span");
    badge.className = "today-badge";
    badge.textContent = "Heute";
    todayRow.querySelector("th").appendChild(badge);
  }

  /* ---------- Formular: reine Frontend-Validierung ---------- */
  var form = document.getElementById("reservation-form");
  var success = document.getElementById("form-success");

  if (form && success) {
    var setFieldState = function (input, valid) {
      var field = input.closest(".form-field");
      var error = field ? field.querySelector(".field-error") : null;
      if (!field) { return; }
      field.classList.toggle("has-error", !valid);
      input.setAttribute("aria-invalid", valid ? "false" : "true");
      if (error) {
        if (valid) {
          input.removeAttribute("aria-describedby");
        } else {
          input.setAttribute("aria-describedby", error.id);
        }
      }
    };

    var validateInput = function (input) {
      var valid = input.checkValidity();
      setFieldState(input, valid);
      return valid;
    };

    // Validierung beim Verlassen des Feldes, Korrektur live
    form.querySelectorAll("input, select, textarea").forEach(function (input) {
      input.addEventListener("blur", function () {
        if (input.hasAttribute("required")) { validateInput(input); }
      });
      input.addEventListener("input", function () {
        if (input.closest(".form-field").classList.contains("has-error")) {
          validateInput(input);
        }
      });
    });

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var allValid = true;
      var firstInvalid = null;

      form.querySelectorAll("[required]").forEach(function (input) {
        var valid = validateInput(input);
        if (!valid && !firstInvalid) { firstInvalid = input; }
        allValid = allValid && valid;
      });

      if (!allValid) {
        if (firstInvalid) { firstInvalid.focus(); }
        return;
      }

      /* Nur Frontend: Hier wuerde der Versand an ein Backend oder
         einen Formulardienst stehen, z.B.:
         fetch("/api/reservation", { method: "POST", body: new FormData(form) })
      */
      form.hidden = true;
      success.hidden = false;
      success.focus && success.setAttribute("tabindex", "-1");
      success.focus();
    });
  }

  /* ---------- Footer-Jahr ---------- */
  var year = document.getElementById("year");
  if (year) { year.textContent = String(new Date().getFullYear()); }
})();

/* Sicherheitsnetz: nichts bleibt dauerhaft unsichtbar (Screenshots, Print, exotische Browser) */
window.addEventListener("load", function () {
  setTimeout(function () {
    document.querySelectorAll(".reveal").forEach(function (el) { el.classList.add("is-visible"); });
  }, 2000);
});
