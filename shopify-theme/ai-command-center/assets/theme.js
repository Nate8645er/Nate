/* AI COMMAND CENTER - Premium Theme v2
   Vanilla JS: Scroll-Reveal (mit Sicherheitsnetz), Warenkorb-Anzahl,
   Produkt-Galerie, Varianten-Sync, Direkt kaufen, Sticky-Kaufleiste.
   Keine externen Ressourcen. */
(function () {
  'use strict';

  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ------------------------------------------------------------------
     1) Scroll-Reveal via IntersectionObserver.
        Sicherheitsnetz: nach load (plus Timeout) wird alles sichtbar,
        egal was passiert. Ohne JS greift die CSS-Hide-Regel gar nicht.
  ------------------------------------------------------------------ */
  function revealAll() {
    var els = document.querySelectorAll('.acc-reveal');
    for (var i = 0; i < els.length; i++) els[i].classList.add('is-in');
  }

  function initReveal() {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      revealAll();
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-in');
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -10% 0px', threshold: 0.08 });

    document.querySelectorAll('.acc-reveal').forEach(function (el) {
      observer.observe(el);
    });

    /* Sicherheitsnetz 1: kurz nach vollständigem Laden alles zeigen,
       was bereits im Viewport hätte sein müssen. */
    window.addEventListener('load', function () {
      window.setTimeout(function () {
        document.querySelectorAll('.acc-reveal:not(.is-in)').forEach(function (el) {
          var rect = el.getBoundingClientRect();
          if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('is-in');
          }
        });
      }, 600);
    });

    /* Sicherheitsnetz 2: absoluter Fallback, nichts bleibt je unsichtbar. */
    window.setTimeout(revealAll, 6000);
  }

  /* ------------------------------------------------------------------
     2) Warenkorb-Anzahl via /cart.js
  ------------------------------------------------------------------ */
  function updateCartCount() {
    var bubbles = document.querySelectorAll('[data-cart-count]');
    if (!bubbles.length || !window.fetch) return;
    fetch('/cart.js', { headers: { Accept: 'application/json' } })
      .then(function (res) { return res.ok ? res.json() : null; })
      .then(function (cart) {
        if (!cart) return;
        bubbles.forEach(function (b) {
          b.textContent = cart.item_count;
          if (cart.item_count > 0) {
            b.removeAttribute('hidden');
          } else {
            b.setAttribute('hidden', '');
          }
        });
      })
      .catch(function () { /* Server-gerenderter Wert bleibt stehen */ });
  }

  /* ------------------------------------------------------------------
     3) Produkt-Galerie: Thumbnail-Klick tauscht Hauptbild
  ------------------------------------------------------------------ */
  function initGallery() {
    var main = document.querySelector('[data-gallery-main] img');
    var thumbs = document.querySelectorAll('[data-gallery-thumb]');
    if (!main || !thumbs.length) return;
    thumbs.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var full = btn.getAttribute('data-full');
        var alt = btn.getAttribute('data-alt') || '';
        if (!full) return;
        main.src = full;
        main.removeAttribute('srcset');
        main.alt = alt;
        thumbs.forEach(function (t) { t.classList.remove('is-active'); });
        btn.classList.add('is-active');
      });
    });
  }

  /* ------------------------------------------------------------------
     4) Varianten-Select: Preis + Kauf-Buttons synchron halten
  ------------------------------------------------------------------ */
  function initVariantSync() {
    var select = document.querySelector('[data-variant-select]');
    if (!select) return;
    select.addEventListener('change', function () {
      var opt = select.options[select.selectedIndex];
      var price = opt.getAttribute('data-price');
      var priceEls = document.querySelectorAll('[data-product-price]');
      if (price) {
        priceEls.forEach(function (el) { el.textContent = price; });
      }
      document.querySelectorAll('[data-buy-now]').forEach(function (btn) {
        btn.setAttribute('data-variant-id', opt.value);
      });
    });
  }

  /* ------------------------------------------------------------------
     5) Direkt kaufen: Variante in den Warenkorb, dann zur Kasse
  ------------------------------------------------------------------ */
  function initBuyNow() {
    document.querySelectorAll('[data-buy-now]').forEach(function (btn) {
      btn.addEventListener('click', function (evt) {
        evt.preventDefault();
        var id = btn.getAttribute('data-variant-id');
        if (!id || !window.fetch) return;
        btn.setAttribute('disabled', '');
        fetch('/cart/add.js', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
          body: JSON.stringify({ id: Number(id), quantity: 1 })
        })
          .then(function (res) {
            if (!res.ok) throw new Error('add failed');
            window.location.href = '/checkout';
          })
          .catch(function () {
            btn.removeAttribute('disabled');
            window.location.href = '/cart';
          });
      });
    });
  }

  /* ------------------------------------------------------------------
     6) Sticky-Kaufleiste (Mobile): erscheint, sobald der Haupt-Kaufbutton
        aus dem Sichtfeld gescrollt ist
  ------------------------------------------------------------------ */
  function initBuybar() {
    var bar = document.querySelector('[data-buybar]');
    var anchor = document.querySelector('[data-buybar-anchor]');
    if (!bar) return;
    if (!anchor || !('IntersectionObserver' in window)) {
      bar.classList.add('is-visible');
      return;
    }
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        bar.classList.toggle('is-visible', !entry.isIntersecting);
      });
    }, { threshold: 0 });
    obs.observe(anchor);
  }

  /* ------------------------------------------------------------------
     Init
  ------------------------------------------------------------------ */
  function init() {
    initReveal();
    updateCartCount();
    initGallery();
    initVariantSync();
    initBuyNow();
    initBuybar();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
