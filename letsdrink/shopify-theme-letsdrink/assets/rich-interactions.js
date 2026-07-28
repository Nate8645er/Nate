(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var desktop = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  document.addEventListener("DOMContentLoaded", function () {
    initRipple();
    initMagnetic();
    initNavScroll();
    initGallery();
    initQtyStepper();
    initAjaxCart();
  });

  /* Ripple auf jeden .btn-Klick, kein Effekt auf Formular-Validierung/Submit */
  function initRipple() {
    if (reduced) return;
    document.addEventListener("click", function (e) {
      var btn = e.target.closest(".btn");
      if (!btn) return;
      var r = btn.getBoundingClientRect();
      var ripple = document.createElement("span");
      ripple.className = "ripple";
      var size = Math.max(r.width, r.height) * 2;
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - r.left - size / 2) + "px";
      ripple.style.top = (e.clientY - r.top - size / 2) + "px";
      btn.appendChild(ripple);
      window.setTimeout(function () { ripple.remove(); }, 600);
    }, { passive: true });
  }

  /* Magnetischer Haupt-CTA, nur Desktop */
  function initMagnetic() {
    if (reduced || !desktop) return;
    document.querySelectorAll(".magnetic").forEach(function (btn) {
      btn.addEventListener("mousemove", function (e) {
        var r = btn.getBoundingClientRect();
        btn.style.setProperty("--mag-x", (((e.clientX - r.left - r.width / 2) / r.width) * 10).toFixed(1) + "px");
        btn.style.setProperty("--mag-y", (((e.clientY - r.top - r.height / 2) / r.height) * 10).toFixed(1) + "px");
      });
      btn.addEventListener("mouseleave", function () {
        btn.style.setProperty("--mag-x", "0px");
        btn.style.setProperty("--mag-y", "0px");
      });
    });
  }

  /* Header: Glas-Look nach Scroll, versteckt sich beim Runterscrollen,
     zeigt sich wieder beim Hochscrollen (mehr Lesefläche auf mobil) */
  function initNavScroll() {
    var header = document.querySelector(".hd");
    if (!header) return;
    var lastY = window.scrollY, ticking = false;
    function update() {
      var y = window.scrollY;
      header.classList.toggle("is-scrolled", y > 12);
      if (!reduced) {
        if (y > 200 && y > lastY + 6) header.classList.add("hd-hidden");
        else if (y < lastY - 6 || y <= 200) header.classList.remove("hd-hidden");
      }
      lastY = y;
      ticking = false;
    }
    document.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(update);
    }, { passive: true });
    update();
  }

  /* Produktgalerie: Crossfade beim Bildwechsel, Preload, Skeleton bis geladen */
  function initGallery() {
    var hero = document.getElementById("pdp-hero-img");
    var frame = document.querySelector(".pdp-hero-frame");
    if (!hero) return;

    function markLoaded() { if (frame) frame.classList.add("img-loaded"); }
    if (hero.complete && hero.naturalWidth > 0) markLoaded();
    else { hero.addEventListener("load", markLoaded, { once: true }); hero.addEventListener("error", markLoaded, { once: true }); }

    var thumbs = document.querySelectorAll(".pdp-thumb");
    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        var full = thumb.getAttribute("data-full");
        if (!full || hero.src === full) return;
        thumbs.forEach(function (t) { t.classList.remove("is-active"); });
        thumb.classList.add("is-active");

        if (reduced) { hero.src = full; hero.alt = thumb.getAttribute("alt") || ""; return; }
        hero.classList.add("swapping");
        var pre = new Image();
        pre.onload = function () {
          hero.src = full;
          hero.alt = thumb.getAttribute("alt") || "";
          requestAnimationFrame(function () { hero.classList.remove("swapping"); });
        };
        pre.src = full;
      });
    });
  }

  /* Mengen-Stepper: +/- Buttons neben dem manuellen Mengenfeld */
  function initQtyStepper() {
    document.querySelectorAll("[data-qty-stepper]").forEach(function (stepper) {
      var input = stepper.querySelector("input");
      stepper.addEventListener("click", function (e) {
        var b = e.target.closest("button[data-step]");
        if (!b || !input) return;
        e.preventDefault();
        var min = parseInt(input.min || "1", 10);
        var next = Math.max(min, (parseInt(input.value, 10) || min) + parseInt(b.dataset.step, 10));
        input.value = next;
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
    });
  }

  /* Toast, global nutzbar */
  window.ldToast = function (msg, ok) {
    var wrap = document.getElementById("toast-wrap");
    if (!wrap) return;
    var t = document.createElement("div");
    t.className = "toast" + (ok === false ? " toast-error" : "");
    t.setAttribute("role", "status");
    t.textContent = msg;
    wrap.appendChild(t);
    requestAnimationFrame(function () { t.classList.add("in"); });
    window.setTimeout(function () {
      t.classList.remove("in");
      window.setTimeout(function () { t.remove(); }, 350);
    }, 3200);
  };

  /* Echtes AJAX-Add-to-Cart: kein Seiten-Neuladen, Button-Status,
     Warenkorb-Zähler mit Bump, Toast, dezenter Konfetti-Effekt */
  function initAjaxCart() {
    var form = document.getElementById("product-form");
    var btn = document.getElementById("pdp-add-btn");
    if (!form || !btn) return;

    var shopRoot = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || "/";
    var cartCountEls = document.querySelectorAll(".hd-cart-count");
    var isSubmitting = false;

    function bumpCartCount(n) {
      var hdCart = document.querySelector(".hd-cart");
      if (cartCountEls.length === 0 && hdCart && n > 0) {
        var span = document.createElement("span");
        span.className = "hd-cart-count";
        hdCart.appendChild(span);
        cartCountEls = document.querySelectorAll(".hd-cart-count");
      }
      cartCountEls.forEach(function (el) {
        el.textContent = n;
        el.classList.remove("bump");
        void el.offsetWidth;
        el.classList.add("bump");
      });
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (isSubmitting || btn.disabled) return;
      isSubmitting = true;
      var label = btn.querySelector(".pdp-add-label");
      var originalLabel = label ? label.textContent : "";
      btn.classList.add("is-loading");
      btn.disabled = true;

      fetch(shopRoot + "cart/add.js", { method: "POST", headers: { Accept: "application/json" }, body: new FormData(form) })
        .then(function (res) {
          if (!res.ok) return res.json().then(function (data) { throw new Error(data.description || "add failed"); });
          return fetch(shopRoot + "cart.js");
        })
        .then(function (res) { return res.json(); })
        .then(function (cart) {
          bumpCartCount(cart.item_count);
          btn.classList.remove("is-loading");
          btn.classList.add("is-success");
          if (label) label.textContent = "Im Warenkorb";
          if (!reduced) window.ldConfetti(btn);
          window.ldToast("🐾 Ab in den Rucksack!");
          window.setTimeout(function () {
            btn.classList.remove("is-success");
            if (label) label.textContent = originalLabel;
            btn.disabled = false;
          }, 1800);
        })
        .catch(function (err) {
          btn.classList.remove("is-loading");
          btn.disabled = false;
          if (label) label.textContent = originalLabel;
          window.ldToast(err.message || "Das hat leider nicht geklappt. Bitte erneut versuchen.", false);
        })
        .finally(function () { isSubmitting = false; });
    });
  }
})();
