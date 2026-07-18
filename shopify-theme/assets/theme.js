/* ==========================================================================
   Aurum Premium – Theme-JavaScript
   Ein einziges, kleines File (defer geladen, keine Frameworks, keine jQuery).
   Animations-Doktrin: nur transform/opacity, ease-out, <300ms Feedback,
   prefers-reduced-motion respektiert, Tilt/Magnetic/Parallax nur auf
   Geräten mit feinem Zeiger (Desktop).
   ========================================================================== */
(function () {
  'use strict';

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(pointer: fine)').matches;

  /* ---------- Scroll-Reveal (IntersectionObserver, mit Stagger) ---------- */
  function initReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window) || reducedMotion) {
      document.documentElement.classList.add('no-observer');
      return;
    }
    /* Stagger: Kinder eines [data-reveal-stagger]-Containers versetzt einblenden */
    document.querySelectorAll('[data-reveal-stagger]').forEach(function (parent) {
      var children = parent.querySelectorAll('.reveal');
      children.forEach(function (child, i) {
        child.style.transitionDelay = Math.min(i * 70, 420) + 'ms';
      });
    });
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

  /* ---------- Header: beim Runterscrollen ausblenden, hoch einblenden ---------- */
  function initHeaderScroll() {
    var header = document.querySelector('[data-header]');
    if (!header || !header.classList.contains('header--sticky') || reducedMotion) return;
    var lastY = 0;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var y = window.scrollY;
        header.classList.toggle('header--scrolled', y > 8);
        /* Nie verstecken, solange das Mobile-Menü offen ist */
        var navOpen = document.querySelector('.mobile-nav.is-open');
        if (!navOpen && y > 160) {
          header.classList.toggle('header--hidden', y > lastY);
        } else {
          header.classList.remove('header--hidden');
        }
        lastY = y;
        ticking = false;
      });
    }, { passive: true });
  }

  /* ---------- Scroll-Fortschrittsbalken ---------- */
  function initScrollProgress() {
    var bar = document.querySelector('[data-scroll-progress]');
    if (!bar) return;
    var ticking = false;
    function update() {
      var max = document.documentElement.scrollHeight - window.innerHeight;
      var progress = max > 0 ? window.scrollY / max : 0;
      bar.style.transform = 'scaleX(' + Math.min(progress, 1) + ')';
      ticking = false;
    }
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /* ---------- Such-Overlay ---------- */
  function initSearchOverlay() {
    var toggle = document.querySelector('[data-search-toggle]');
    var overlay = document.querySelector('[data-search-overlay]');
    if (!toggle || !overlay) return;
    var input = overlay.querySelector('input[type="search"]');
    var close = overlay.querySelector('[data-search-close]');
    function open(e) {
      e.preventDefault();
      overlay.classList.add('is-open');
      setTimeout(function () { if (input) input.focus(); }, 120);
    }
    function shut() { overlay.classList.remove('is-open'); }
    toggle.addEventListener('click', open);
    if (close) close.addEventListener('click', shut);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) shut(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && overlay.classList.contains('is-open')) shut();
    });
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

  /* ---------- Ripple-Effekt auf Buttons (reines Feedback, verzögert nichts) ---------- */
  function initRipple() {
    if (reducedMotion) return;
    document.addEventListener('pointerdown', function (e) {
      var btn = e.target.closest('.btn');
      if (!btn) return;
      var rect = btn.getBoundingClientRect();
      var ripple = document.createElement('span');
      ripple.className = 'ripple';
      var size = Math.max(rect.width, rect.height) * 2;
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      btn.appendChild(ripple);
      setTimeout(function () { ripple.remove(); }, 500);
    });
  }

  /* ---------- Magnetische Buttons (dezent, nur Desktop) ---------- */
  function initMagnetic() {
    if (reducedMotion || !finePointer) return;
    document.querySelectorAll('.btn--lg, [data-magnetic]').forEach(function (btn) {
      btn.addEventListener('pointermove', function (e) {
        var rect = btn.getBoundingClientRect();
        var x = (e.clientX - rect.left - rect.width / 2) / rect.width;
        var y = (e.clientY - rect.top - rect.height / 2) / rect.height;
        btn.style.transform = 'translate(' + (x * 6) + 'px,' + (y * 4) + 'px)';
      });
      btn.addEventListener('pointerleave', function () {
        btn.style.transform = '';
      });
    });
  }

  /* ---------- Fake-3D-Tilt auf Karten & Produktbildern (nur Desktop) ---------- */
  function initTilt() {
    if (reducedMotion || !finePointer) return;
    document.querySelectorAll('[data-tilt]').forEach(function (el) {
      el.classList.add('tilt');
      el.addEventListener('pointermove', function (e) {
        var rect = el.getBoundingClientRect();
        var rx = ((e.clientY - rect.top) / rect.height - 0.5) * -6;
        var ry = ((e.clientX - rect.left) / rect.width - 0.5) * 6;
        el.style.setProperty('--tilt-x', rx.toFixed(2) + 'deg');
        el.style.setProperty('--tilt-y', ry.toFixed(2) + 'deg');
      });
      el.addEventListener('pointerleave', function () {
        el.style.setProperty('--tilt-x', '0deg');
        el.style.setProperty('--tilt-y', '0deg');
      });
    });
  }

  /* ---------- Sanfter Parallax auf Hero-Bild (rAF, nur transform) ---------- */
  function initParallax() {
    if (reducedMotion) return;
    var media = document.querySelector('.hero__img');
    if (!media) return;
    var ticking = false;
    window.addEventListener('scroll', function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        var y = Math.min(window.scrollY, 800);
        media.style.transform = 'translateY(' + (y * 0.12) + 'px) scale(1.06)';
        ticking = false;
      });
    }, { passive: true });
  }

  /* ---------- Zahlen hochzählen (einmalig, wenn sichtbar) ---------- */
  function initCounters() {
    var counters = document.querySelectorAll('[data-count-to]');
    if (!counters.length) return;
    function animate(el) {
      var target = parseInt(el.dataset.countTo, 10) || 0;
      if (reducedMotion) { el.textContent = target; return; }
      var start = null;
      var duration = 900;
      function step(ts) {
        if (!start) start = ts;
        var progress = Math.min((ts - start) / duration, 1);
        /* ease-out */
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(target * eased);
        if (progress < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    if (!('IntersectionObserver' in window)) {
      counters.forEach(function (el) { el.textContent = el.dataset.countTo; });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animate(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    counters.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Produktgalerie: Thumbnails mit Crossfade ---------- */
  function initGalleries() {
    document.querySelectorAll('[data-gallery]').forEach(function (gallery) {
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

  /* ---------- Variantenwahl (Produktseite UND Kauf-Modul auf der Startseite) ---------- */
  function initProductSection(section) {
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

    function pulse(el) {
      if (reducedMotion || !el) return;
      el.classList.remove('is-pulsing');
      void el.offsetWidth; /* Reflow, damit die Animation neu startet */
      el.classList.add('is-pulsing');
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
        if (current) { current.textContent = formatMoney(variant.price); pulse(current); }
        var onSale = variant.compare_at_price && variant.compare_at_price > variant.price;
        if (compare) compare.style.display = onSale ? '' : 'none';
        if (compare && onSale) compare.textContent = formatMoney(variant.compare_at_price);
        if (badge) badge.style.display = onSale ? '' : 'none';
        if (badge && onSale) {
          badge.textContent = '−' + Math.round((1 - variant.price / variant.compare_at_price) * 100) + '%';
        }
      }

      /* URL nur auf der echten Produktseite aktualisieren */
      if (section.hasAttribute('data-main-product') && history.replaceState) {
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

  /* ---------- Sticky Add-to-Cart (Produktseite) ---------- */
  function initStickyAtc() {
    var bar = document.querySelector('[data-sticky-atc]');
    if (!bar || !('IntersectionObserver' in window)) return;
    var section = bar.closest('[data-product]') || document;
    var mainBtn = section.querySelector('[data-atc]');
    var form = section.querySelector('[data-product-form]');
    if (!mainBtn || !form) return;

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

  /* ---------- Toast-Meldungen (aria-live, selbstauflösend) ---------- */
  var toastContainer = null;
  function showToast(message, linkText, linkHref, isError) {
    if (!toastContainer) {
      toastContainer = document.createElement('div');
      toastContainer.className = 'toast-container';
      toastContainer.setAttribute('aria-live', 'polite');
      document.body.appendChild(toastContainer);
    }
    var toast = document.createElement('div');
    toast.className = 'toast' + (isError ? ' toast--error' : '');
    toast.innerHTML = '<span class="toast__msg"></span>';
    toast.querySelector('.toast__msg').textContent = message;
    if (linkText && linkHref) {
      var a = document.createElement('a');
      a.href = linkHref;
      a.className = 'toast__link';
      a.textContent = linkText;
      toast.appendChild(a);
    }
    toastContainer.appendChild(toast);
    requestAnimationFrame(function () { toast.classList.add('is-visible'); });
    setTimeout(function () {
      toast.classList.remove('is-visible');
      setTimeout(function () { toast.remove(); }, 300);
    }, 4000);
  }

  /* ---------- AJAX Add-to-Cart: kein Seitenreload, Badge-Pop + Toast ---------- */
  function initAjaxCart() {
    document.querySelectorAll('[data-product-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        /* Nur den normalen ATC abfangen – Dynamic-Checkout-Buttons laufen nativ */
        e.preventDefault();
        var atcBtn = form.querySelector('[data-atc]');
        var atcText = form.querySelector('[data-atc-text]');
        var original = atcText ? atcText.textContent : '';
        if (atcBtn) { atcBtn.disabled = true; }
        if (atcText) { atcText.textContent = '…'; }

        fetch(window.Shopify && window.Shopify.routes ? window.Shopify.routes.root + 'cart/add.js' : '/cart/add.js', {
          method: 'POST',
          body: new FormData(form),
          headers: { 'Accept': 'application/json' }
        })
          .then(function (res) {
            if (!res.ok) return res.json().then(function (err) { throw err; });
            return res.json();
          })
          .then(function () { return fetch('/cart.js', { headers: { 'Accept': 'application/json' } }); })
          .then(function (res) { return res.json(); })
          .then(function (cart) {
            document.querySelectorAll('[data-cart-count]').forEach(function (el) {
              el.textContent = cart.item_count;
              el.classList.remove('is-hidden');
              el.classList.remove('is-pulsing');
              void el.offsetWidth;
              el.classList.add('is-pulsing');
            });
            showToast('Im Warenkorb!', 'Zur Kasse', '/cart');
          })
          .catch(function (err) {
            showToast((err && err.description) || 'Das hat leider nicht geklappt. Bitte versuche es erneut.', null, null, true);
          })
          .finally(function () {
            if (atcBtn) { atcBtn.disabled = false; }
            if (atcText) { atcText.textContent = original; }
          });
      });
    });
  }

  /* ---------- Produktbild-Zoom (Desktop): Lupe folgt der Maus ---------- */
  function initImageZoom() {
    if (reducedMotion || !finePointer) return;
    document.querySelectorAll('.product__main-image').forEach(function (frame) {
      frame.classList.add('zoomable');
      frame.addEventListener('pointermove', function (e) {
        var img = frame.querySelector('.product__img.is-active') || frame.querySelector('.product__img');
        if (!img) return;
        var rect = frame.getBoundingClientRect();
        var x = ((e.clientX - rect.left) / rect.width) * 100;
        var y = ((e.clientY - rect.top) / rect.height) * 100;
        img.style.transformOrigin = x + '% ' + y + '%';
      });
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

  /* ---------- Cross-Selling: Empfehlungen nachladen (mit Skeleton-Loader) ---------- */
  function initRelatedProducts() {
    var section = document.querySelector('[data-related]');
    if (!section || section.querySelector('.product-card')) return;
    /* Skeleton-Karten anzeigen, bis die Empfehlungen da sind */
    section.innerHTML = '<div class="page-width"><div class="product-grid product-grid--4">' +
      new Array(4).fill('<div class="skeleton"></div>').join('') + '</div></div>';
    fetch(section.dataset.url)
      .then(function (res) { return res.text(); })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, 'text/html');
        var fresh = doc.querySelector('[data-related]');
        if (fresh && fresh.querySelector('.product-card')) {
          section.innerHTML = fresh.innerHTML;
        } else {
          section.innerHTML = '';
        }
      })
      .catch(function () { section.innerHTML = ''; });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initReveal();
    initHeaderScroll();
    initScrollProgress();
    initSearchOverlay();
    initAnnouncement();
    initMobileNav();
    initRipple();
    initMagnetic();
    initTilt();
    initParallax();
    initCounters();
    initGalleries();
    initQty();
    document.querySelectorAll('[data-product]').forEach(initProductSection);
    initAjaxCart();
    initImageZoom();
    initStickyAtc();
    initCountdown();
    initCartAutoUpdate();
    initSort();
    initRelatedProducts();
  });
})();
