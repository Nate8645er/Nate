(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    initConsent();
    initGallery();
    initVariantPicker();
    initQtyPicker();
  });

  /* Cookie-Hinweis */
  function initConsent() {
    var bar = document.getElementById("consent-bar");
    if (!bar) return;
    if (!localStorage.getItem("ld_consent_ok")) {
      bar.hidden = false;
    }
    var btn = bar.querySelector("[data-consent]");
    if (btn) {
      btn.addEventListener("click", function () {
        localStorage.setItem("ld_consent_ok", "1");
        bar.hidden = true;
      });
    }
  }

  /* Bild-Galerie: Klick auf Thumbnail wechselt das Hauptbild */
  function initGallery() {
    var hero = document.getElementById("pdp-hero-img");
    if (!hero) return;
    var thumbs = document.querySelectorAll(".pdp-thumb");
    thumbs.forEach(function (thumb) {
      thumb.addEventListener("click", function () {
        var full = thumb.getAttribute("data-full");
        if (!full) return;
        hero.setAttribute("src", full);
        hero.setAttribute("alt", thumb.getAttribute("alt") || "");
        thumbs.forEach(function (t) { t.classList.remove("is-active"); });
        thumb.classList.add("is-active");
      });
    });
  }

  /* Varianten-Auswahl: setzt das echte id-Feld und aktualisiert den Preis */
  function initVariantPicker() {
    var selects = document.querySelectorAll("[data-option-selector]");
    var hiddenSelect = document.getElementById("pdp-variant-id");
    var priceEl = document.getElementById("pdp-price-current");
    var addBtn = document.getElementById("pdp-add-btn");
    if (!selects.length || !hiddenSelect) return;

    function currentTitleParts() {
      return Array.prototype.map.call(selects, function (s) { return s.value; });
    }

    function sync() {
      var parts = currentTitleParts();
      var match = null;
      Array.prototype.forEach.call(hiddenSelect.options, function (opt) {
        var title = opt.textContent.split(" / ").map(function (s) { return s.trim(); });
        var isMatch = parts.every(function (p, i) { return title[i] === p; });
        if (isMatch) match = opt;
      });
      if (!match) return;
      hiddenSelect.value = match.value;
      if (priceEl) {
        var price = parseInt(match.getAttribute("data-price"), 10);
        if (!isNaN(price)) {
          priceEl.textContent = formatMoney(price);
        }
      }
      var available = match.getAttribute("data-available") === "true";
      if (addBtn) {
        addBtn.disabled = !available;
        addBtn.textContent = available ? "In den Warenkorb" : "Zurzeit nicht verfügbar";
      }
    }

    selects.forEach(function (s) { s.addEventListener("change", sync); });
  }

  function formatMoney(cents) {
    var amount = (cents / 100).toFixed(2).replace(".", ".");
    return "CHF " + amount;
  }

  /* Mengen-Rabatt-Picker: "2 kaufen, 1 gratis" usw. setzt das Mengenfeld direkt */
  function initQtyPicker() {
    var picker = document.querySelector("[data-qty-picker]");
    if (!picker) return;
    var buttons = picker.querySelectorAll(".qty-opt");
    var input = picker.querySelector("[data-qty-input]");
    var hint = picker.querySelector("[data-qty-hint]");
    if (!input) return;

    function setActive(qty) {
      buttons.forEach(function (b) {
        b.classList.toggle("is-active", b.getAttribute("data-qty") === String(qty));
      });
      if (hint) hint.hidden = qty === "1";
    }

    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        var qty = btn.getAttribute("data-qty");
        input.value = qty;
        setActive(qty);
      });
    });

    input.addEventListener("input", function () {
      var qty = input.value;
      var known = Array.prototype.some.call(buttons, function (b) { return b.getAttribute("data-qty") === qty; });
      if (known) {
        setActive(qty);
      } else {
        buttons.forEach(function (b) { b.classList.remove("is-active"); });
        if (hint) hint.hidden = true;
      }
    });
  }
})();
