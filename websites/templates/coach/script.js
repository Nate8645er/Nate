/* ============================================================
   VORLAGE: COACH / BERATER — Script
   Rein progressiv: ohne JS bleibt die Seite voll nutzbar.
   ============================================================ */
(function () {
  'use strict';

  // JS-Marker: erst jetzt werden Reveal-Elemente initial versteckt
  document.documentElement.classList.add('js');

  document.addEventListener('DOMContentLoaded', function () {

    /* ---------- Reveal-Animationen ---------- */
    var revealEls = document.querySelectorAll('.reveal');
    if ('IntersectionObserver' in window) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('in-view');
            observer.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });
      revealEls.forEach(function (el) { observer.observe(el); });
    } else {
      revealEls.forEach(function (el) { el.classList.add('in-view'); });
    }

    /* ---------- Header-Linie beim Scrollen ---------- */
    var header = document.querySelector('.site-header');
    var onScroll = function () {
      header.classList.toggle('is-scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    /* ---------- Mobile-Menü nach Klick schliessen ---------- */
    var navToggle = document.getElementById('nav-toggle');
    document.querySelectorAll('.nav-links a').forEach(function (link) {
      link.addEventListener('click', function () {
        if (navToggle) { navToggle.checked = false; }
      });
    });

    /* ---------- Aktuelles Jahr im Footer ---------- */
    var jahr = document.getElementById('jahr');
    if (jahr) { jahr.textContent = String(new Date().getFullYear()); }

    /* ---------- Kontaktformular (nur Frontend) ----------
       CUSTOMIZE: Im Submit-Handler unten den eigenen
       Versand-Endpoint (fetch/E-Mail-Dienst) einsetzen. */
    var form = document.getElementById('kontakt-formular');
    if (!form) { return; }

    var fields = [
      {
        input: document.getElementById('f-name'),
        error: document.getElementById('f-name-error'),
        valid: function (el) { return el.value.trim().length > 1; }
      },
      {
        input: document.getElementById('f-email'),
        error: document.getElementById('f-email-error'),
        valid: function (el) {
          return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(el.value.trim());
        }
      },
      {
        input: document.getElementById('f-nachricht'),
        error: document.getElementById('f-nachricht-error'),
        valid: function (el) { return el.value.trim().length > 4; }
      },
      {
        input: document.getElementById('f-datenschutz'),
        error: document.getElementById('f-datenschutz-error'),
        valid: function (el) { return el.checked; }
      }
    ];

    function checkField(field) {
      var ok = field.valid(field.input);
      field.error.hidden = ok;
      field.input.closest('.form-field').classList.toggle('has-error', !ok);
      field.input.setAttribute('aria-invalid', ok ? 'false' : 'true');
      if (!ok) {
        field.input.setAttribute('aria-describedby', field.error.id);
      }
      return ok;
    }

    // Validierung beim Verlassen des Feldes
    fields.forEach(function (field) {
      field.input.addEventListener('blur', function () { checkField(field); });
      field.input.addEventListener('input', function () {
        if (!field.error.hidden) { checkField(field); }
      });
    });

    form.addEventListener('submit', function (event) {
      event.preventDefault();

      var firstInvalid = null;
      fields.forEach(function (field) {
        if (!checkField(field) && !firstInvalid) { firstInvalid = field.input; }
      });
      if (firstInvalid) {
        firstInvalid.focus();
        return;
      }

      // CUSTOMIZE: Hier echten Versand einbauen, z. B.:
      // fetch('/api/kontakt', { method: 'POST', body: new FormData(form) })
      var success = document.getElementById('form-erfolg');
      form.reset();
      success.hidden = false;
      success.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    });
  });
})();

/* Sicherheitsnetz: nichts bleibt dauerhaft unsichtbar (Screenshots, Print, exotische Browser) */
window.addEventListener('load', function () {
  setTimeout(function () {
    document.querySelectorAll('.reveal').forEach(function (el) { el.classList.add('in-view'); });
  }, 2000);
});
