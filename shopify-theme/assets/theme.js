/* ==========================================================================
   Aurum Premium – Theme-JavaScript
   Ein einziges, kleines File (defer geladen, keine Frameworks, keine jQuery).
   Module: Scroll-Reveal, Ankündigungs-Rotation, Mobile-Nav, Produktgalerie,
   Variantenwahl, Mengensteuerung, Sticky Add-to-Cart, Countdown,
   Warenkorb-Auto-Update, Collection-Sortierung.
   ========================================================================== */
(function () {
  'use strict';

  /* ---------- Scroll-Reveal (IntersectionObserver, mit Fallback) ---------- */
  function initReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
      document.documentElement.classList.add('no-observer');
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: '0px 0px -8% 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Ankündigungsleiste: Botschaften rotieren ---------- */
  function initAnnouncement() {
    var bar = document.querySelector('[data-announcement]');
    if (!bar) return;
    var items = bar.querySelectorAll('.announcement__item');
    if (items.length < 2) return;
    var index = 0;
    setInterval(function () {
      items[index].classList.remove('is-active');
      index = (index + 1) % items.length;
      items[index].classList.add('is-active');
    }, 4000);
  }

  /* ---------- Mobile Navigation ---------- */
  function initMobileNav() {
    var toggle = document.querySelector('[data-menu-toggle]');
    var nav = document.querySelector('[data-mobile-nav]');
    var overlay = document.querySelector('[data-menu-overlay]');
    var close = document.querySelector('[data-menu-close]');
    if (!toggle || !nav) return;

    function open() {
      nav.hidden = false;
      overlay.hidden = false;
      requestAnimationFrame(function () { nav.classList.add('is-open'); });
      toggle.setAttribute('aria-expanded', 'true');
      document.body.style.overflow = 'hidden';
    }
    function shut() {
      nav.classList.remove('is-open');
      toggle.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      setTimeout(function () { nav.hidden = true; overlay.hidden = true; }, 250);
    }
    toggle.addEventListener('click', open);
    if (close) close.addEventListener('click', shut);
    if (overlay) overlay.addEventListener('click', shut);
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !nav.hidden) shut();
    });
  }

  /* ---------- Produktgalerie: Thumbnails ---------- */
  function initGallery() {
    var gallery = document.querySelector('[data-gallery]');
    if (!gallery) return;
    var images = gallery.querySelectorAll('.product__main-image .product__img');
    var thumbs = gallery.querySelectorAll('[data-thumb-index]');
    thumbs.forEach(function (thumb) {
      thumb.addEventListener('click', function () {
        var idx = parseInt(thumb.dataset.thumbIndex, 10);
        images.forEach(function (img, i) {
          img.classList.toggle('is-active', i === idx);
        });
        thumbs.forEach(function (t) { t.classList.toggle('is-active', t === thumb); });
      });
    });
  }

  /* ---------- Mengensteuerung (+/-) ---------- */
  function initQty() {
    document.querySelectorAll('[data-qty]').forEach(function (qty) {
      var input = qty.querySelector('.qty__input');
      var minus = qty.querySelector('[data-qty-minus]');
      var plus = qty.querySelector('[data-qty-plus]');
      if (!input) return;
      function step(delta) {
        var min = parseInt(input.min || '1', 10);
        var value = Math.max(min, (parseInt(input.value, 10) || min) + delta);
        input.value = value;
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
      if (minus) minus.addEventListener('click', function () { step(-1); });
      if (plus) plus.addEventListener('click', function () { step(1); });
    });
  }

  /* ---------- Geldformat ---------- */
  function formatMoney(cents) {
    var format = (window.themeSettings && window.themeSettings.moneyFormat) || '{{amount}}';
    var value = (cents / 100).toFixed(2);
    return format
      .replace(/\{\{\s*amount\s*\}\}/, value)
      .replace(/\{\{\s*amount_no_decimals\s*\}\}/, Math.round(cents / 100).toString())
      .replace(/\{\{\s*amount_with_comma_separator\s*\}\}/, value.replace('.', ','))
      .replace(/\{\{\s*amount_with_apostrophe_separator\s*\}\}/, value.replace(/\B(?=(\d{3})+(?!\d))/g, "'"));
  }

  /* ---------- Variantenwahl auf der Produktseite ---------- */
  function initVariantPicker() {
    var section = document.querySelector('[data-product]');
    if (!section) return;
    var jsonEl = section.querySelector('[data-variant-json]');
    var form = section.querySelector('[data-product-form]');
    if (!jsonEl || !form) return;

    var variants;
    try { variants = JSON.parse(jsonEl.textContent); } catch (e) { return; }

    var idInput = form.querySelector('[data-variant-id]');
    var atcBtn = form.querySelector('[data-atc]');
    var atcText = form.querySelector('[data-atc-text]');
    var priceWrapper = section.querySelector('[data-price-wrapper]');
    var stickyPrice = section.querySelector('[data-sticky-price]');
    var strings = {
      add: (atcText && atcText.textContent.trim()) || 'In den Warenkorb',
      soldOut: 'Ausverkauft'
    };

    function selectedOptions() {
      var options = [];
      section.querySelectorAll('.variant-picker').forEach(function (fieldset) {
        var checked = fieldset.querySelector('input:checked');
        options.push(checked ? checked.value : null);
      });
      return options;
    }

    function findVariant(options) {
      return variants.find(function (variant) {
        return options.every(function (value, i) { return variant.options[i] === value; });
      });
    }

    function updateUI(variant) {
      if (!variant) {
        if (atcBtn) { atcBtn.disabled = true; }
        if (atcText) { atcText.textContent = strings.soldOut; }
        return;
      }
      if (idInput) idInput.value = variant.id;
      if (atcBtn) atcBtn.disabled = !variant.available;
      if (atcText) atcText.textContent = variant.available ? strings.add : strings.soldOut;
      if (stickyPrice) stickyPrice.textContent = formatMoney(variant.price);

      if (priceWrapper) {
        var current = priceWrapper.querySelector('.price__current');
        var compare = priceWrapper.querySelector('.price__compare');
        var badge = priceWrapper.querySelector('.price__badge');
        if (current) current.textContent = formatMoney(variant.price);
        var onSale = variant.compare_at_price && variant.compare_at_price > variant.price;
        if (compare) compare.style.display = onSale ? '' : 'none';
        if (compare && onSale) compare.textContent = formatMoney(variant.compare_at_price);
        if (badge) badge.style.display = onSale ? '' : 'none';
        if (badge && onSale) {
          badge.textContent = '−' + Math.round((1 - variant.price / variant.compare_at_price) * 100) + '%';
        }
      }

      /* URL aktualisieren (teilen/zurück-Navigation) */
      if (history.replaceState) {
        var url = new URL(window.location.href);
        url.searchParams.set('variant', variant.id);
        history.replaceState({}, '', url.toString());
      }
    }

    section.querySelectorAll('[data-option-input]').forEach(function (input) {
      input.addEventListener('change', function () {
        var fieldset = input.closest('.variant-picker');
        var label = fieldset && fieldset.querySelector('[data-selected-value]');
        if (label) label.textContent = input.value;
        updateUI(findVariant(selectedOptions()));
      });
    });
  }

  /* ---------- Sticky Add-to-Cart ---------- */
  function initStickyAtc() {
    var bar = document.querySelector('[data-sticky-atc]');
    var mainBtn = document.querySelector('[data-atc]');
    var form = document.querySelector('[data-product-form]');
    if (!bar || !mainBtn || !form || !('IntersectionObserver' in window)) return;

    var io = new IntersectionObserver(function (entries) {
      var visible = entries[0].isIntersecting;
      bar.hidden = false;
      bar.classList.toggle('is-visible', !visible);
    }, { rootMargin: '-60px 0px 0px 0px' });
    io.observe(mainBtn);

    var stickyBtn = bar.querySelector('[data-sticky-atc-btn]');
    if (stickyBtn) {
      stickyBtn.addEventListener('click', function () {
        if (typeof form.requestSubmit === 'function') form.requestSubmit();
        else form.submit();
      });
    }
  }

  /* ---------- Countdown (blendet sich nach Ablauf aus) ---------- */
  function initCountdown() {
    document.querySelectorAll('[data-countdown]').forEach(function (el) {
      var end = new Date(el.dataset.end).getTime();
      if (isNaN(end)) return;
      var fields = {
        days: el.querySelector('[data-cd-days]'),
        hours: el.querySelector('[data-cd-hours]'),
        mins: el.querySelector('[data-cd-mins]'),
        secs: el.querySelector('[data-cd-secs]')
      };
      function tick() {
        var diff = end - Date.now();
        if (diff <= 0) { el.hidden = true; clearInterval(timer); return; }
        el.hidden = false;
        var s = Math.floor(diff / 1000);
        if (fields.days) fields.days.textContent = Math.floor(s / 86400);
        if (fields.hours) fields.hours.textContent = Math.floor((s % 86400) / 3600);
        if (fields.mins) fields.mins.textContent = Math.floor((s % 3600) / 60);
        if (fields.secs) fields.secs.textContent = s % 60;
      }
      tick();
      var timer = setInterval(tick, 1000);
    });
  }

  /* ---------- Warenkorb: Mengenänderung sendet das Formular ---------- */
  function initCartAutoUpdate() {
    var form = document.querySelector('[data-cart-form]');
    if (!form) return;
    var timeout;
    form.querySelectorAll('[data-cart-qty]').forEach(function (input) {
      input.addEventListener('change', function () {
        clearTimeout(timeout);
        timeout = setTimeout(function () { form.submit(); }, 400);
      });
    });
  }

  /* ---------- Kategorieseite: Sortierung ---------- */
  function initSort() {
    var form = document.querySelector('[data-sort-form]');
    if (!form) return;
    var select = form.querySelector('select');
    select.addEventListener('change', function () {
      var url = new URL(window.location.href);
      url.searchParams.set('sort_by', select.value);
      url.searchParams.delete('page');
      window.location.href = url.toString();
    });
  }

  /* ---------- Cross-Selling: native Produkt-Empfehlungen nachladen ---------- */
  function initRelatedProducts() {
    var section = document.querySelector('[data-related]');
    if (!section || section.querySelector('.product-card')) return;
    fetch(section.dataset.url)
      .then(function (res) { return res.text(); })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var fresh = doc.querySelector('[data-related]');
        if (fresh && fresh.querySelector('.product-card')) {
          section.innerHTML = fresh.innerHTML;
        }
      })
      .catch(function () { /* Empfehlungen sind optional – Fehler still schlucken */ });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initReveal();
    initAnnouncement();
    initMobileNav();
    initGallery();
    initQty();
    initVariantPicker();
    initStickyAtc();
    initCountdown();
    initCartAutoUpdate();
    initSort();
    initRelatedProducts();
  });
})();
