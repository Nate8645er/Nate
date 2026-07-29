/* LET'SDRINK — See-Interaktionen
   Kinoreife Comic-Effekte, diszipliniert umgesetzt:
   nur transform/opacity, rAF-gebuendelt, Desktop-Gates fuer teure
   Effekte, prefers-reduced-motion ueberall respektiert. */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var desktop = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  document.documentElement.classList.add("js");

  /* ---------- Loader: kurzer Blubber, nie blockierend ---------- */
  var loader = document.getElementById("loader");
  function killLoader() {
    if (!loader) return;
    loader.classList.add("done");
    document.body.classList.remove("loading");
    setTimeout(function () { if (loader && loader.parentNode) loader.remove(); loader = null; }, 450);
  }
  if (loader) {
    var seen = false;
    try { seen = sessionStorage.getItem("ld_seen") === "1"; sessionStorage.setItem("ld_seen", "1"); } catch (e) {}
    if (reduced || seen) killLoader();
    else { setTimeout(killLoader, 600); window.addEventListener("load", killLoader, { once: true }); }
  } else {
    document.body.classList.remove("loading");
  }

  document.addEventListener("DOMContentLoaded", function () {

    /* ---------- Scroll-Progress ---------- */
    var progress = document.getElementById("scroll-progress");
    if (progress && !reduced) {
      var sTick = false;
      window.addEventListener("scroll", function () {
        if (sTick) return;
        sTick = true;
        requestAnimationFrame(function () {
          var h = document.documentElement.scrollHeight - window.innerHeight;
          progress.style.transform = "scaleX(" + (h > 0 ? window.scrollY / h : 0) + ")";
          sTick = false;
        });
      }, { passive: true });
    }

    /* ---------- Header: Sticker-Leiste, Hide/Show ---------- */
    var navbar = document.querySelector(".navbar");
    if (navbar) {
      var lastY = window.scrollY, nTick = false;
      var navUpdate = function () {
        var y = window.scrollY;
        navbar.classList.toggle("scrolled", y > 60);
        if (!reduced && !document.body.classList.contains("menu-open")) {
          if (y > 340 && y > lastY + 6) navbar.classList.add("nav-hidden");
          else if (y < lastY - 6 || y <= 340) navbar.classList.remove("nav-hidden");
        }
        lastY = y;
        nTick = false;
      };
      navUpdate();
      window.addEventListener("scroll", function () {
        if (nTick) return;
        nTick = true;
        requestAnimationFrame(navUpdate);
      }, { passive: true });
    }

    /* ---------- Mobile-Menue ---------- */
    var burger = document.getElementById("menu-toggle");
    var mobileMenu = document.getElementById("mobile-menu");
    if (burger && mobileMenu) {
      var setMenu = function (open) {
        document.body.classList.toggle("menu-open", open);
        burger.setAttribute("aria-expanded", open ? "true" : "false");
        mobileMenu.setAttribute("aria-hidden", open ? "false" : "true");
      };
      burger.addEventListener("click", function () {
        setMenu(!document.body.classList.contains("menu-open"));
      });
      mobileMenu.addEventListener("click", function (e) {
        if (e.target.tagName === "A" || e.target.classList.contains("mobile-menu-backdrop")) setMenu(false);
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") setMenu(false);
      });
      window.matchMedia("(min-width: 769px)").addEventListener("change", function (e) {
        if (e.matches) setMenu(false);
      });
    }

    /* ---------- Scroll-Reveal + Zahlen-Animation ---------- */
    function animateCounter(el) {
      var target = parseInt(el.dataset.target, 10) || 0;
      if (reduced) { el.textContent = target; return; }
      var start = null;
      function step(ts) {
        if (!start) start = ts;
        var p = Math.min((ts - start) / 1100, 1);
        el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3)));
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    var revealEls = document.querySelectorAll(".reveal, .reveal-stagger");
    if (reduced) {
      revealEls.forEach(function (el) { el.classList.add("is-visible"); });
      document.querySelectorAll(".counter").forEach(function (el) { el.textContent = el.dataset.target; });
    } else {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-visible");
          entry.target.querySelectorAll(".counter").forEach(animateCounter);
          io.unobserve(entry.target);
        });
      }, { threshold: 0.12, rootMargin: "0px 0px -5% 0px" });
      revealEls.forEach(function (el) { io.observe(el); });
    }

    /* ---------- 3D-Tilt (Desktop) ---------- */
    if (desktop && !reduced) {
      document.querySelectorAll(".tilt-media").forEach(function (card) {
        var raf = false, rx = 0, ry = 0, over = false;
        var apply = function () {
          if (over) {
            card.style.transform = "perspective(900px) translateY(-6px) rotateX(" + ry + "deg) rotateY(" + rx + "deg)";
          }
          raf = false;
        };
        card.addEventListener("mousemove", function (e) {
          var r = card.getBoundingClientRect();
          var px = (e.clientX - r.left) / r.width;
          var py = (e.clientY - r.top) / r.height;
          rx = (px - 0.5) * 7;
          ry = (py - 0.5) * -7;
          over = true;
          if (!raf) { raf = true; requestAnimationFrame(apply); }
        });
        card.addEventListener("mouseleave", function () {
          over = false;
          card.style.transform = "";
        });
      });

      /* Magnetische Buttons (subtil) */
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

    /* ---------- Ripple (nach dem Klick, verzoegert nichts) ---------- */
    document.addEventListener("click", function (e) {
      var btn = e.target.closest(".btn");
      if (!btn || reduced) return;
      var r = btn.getBoundingClientRect();
      var ripple = document.createElement("span");
      ripple.className = "ripple";
      var size = Math.max(r.width, r.height) * 2;
      ripple.style.width = ripple.style.height = size + "px";
      ripple.style.left = (e.clientX - r.left - size / 2) + "px";
      ripple.style.top = (e.clientY - r.top - size / 2) + "px";
      btn.appendChild(ripple);
      setTimeout(function () { ripple.remove(); }, 600);
    }, { passive: true });

    /* ---------- Toast ---------- */
    var toastWrap = document.getElementById("toast-wrap");
    window.ldToast = function (msg, ok) {
      if (!toastWrap) return;
      var t = document.createElement("div");
      t.className = "toast" + (ok === false ? " toast-error" : "");
      t.setAttribute("role", "status");
      t.textContent = msg;
      toastWrap.appendChild(t);
      requestAnimationFrame(function () { t.classList.add("in"); });
      setTimeout(function () {
        t.classList.remove("in");
        setTimeout(function () { t.remove(); }, 350);
      }, 3200);
    };

    /* ---------- AJAX Add-to-Cart + Badge-Bump (locale-sicher) ---------- */
    var shopRoot = (window.Shopify && window.Shopify.routes && window.Shopify.routes.root) || "/";
    var cartCountEls = document.querySelectorAll(".cart-count, .cart-count-num");
    function bumpCartCount(n) {
      cartCountEls.forEach(function (el) {
        el.textContent = n;
        el.classList.remove("bump");
        void el.offsetWidth;
        el.classList.add("bump");
      });
    }
    var isSubmitting = false;
    document.querySelectorAll("form[action$='/cart/add']").forEach(function (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        if (isSubmitting) return;
        isSubmitting = true;
        var btn = form.querySelector("[type=submit]");
        var stickyBtn = document.querySelector(".sticky-atc-btn");
        var original = btn ? btn.innerHTML : "";
        if (btn) { btn.classList.add("is-loading"); btn.disabled = true; }
        if (stickyBtn) stickyBtn.disabled = true;
        fetch(shopRoot + "cart/add.js", { method: "POST", headers: { "Accept": "application/json" }, body: new FormData(form) })
          .then(function (res) {
            if (!res.ok) throw new Error("add failed");
            return fetch(shopRoot + "cart.js");
          })
          .then(function (res) { return res.json(); })
          .then(function (cart) {
            bumpCartCount(cart.item_count);
            if (btn) {
              btn.classList.remove("is-loading");
              btn.classList.add("is-success");
              btn.innerHTML = "✓ Eingepackt!";
              setTimeout(function () {
                btn.classList.remove("is-success");
                btn.innerHTML = original;
                btn.disabled = false;
              }, 1800);
            }
            window.ldToast("🐾 Ab in den Rucksack!");
          })
          .catch(function () {
            if (btn) { btn.classList.remove("is-loading"); btn.disabled = false; btn.innerHTML = original; }
            window.ldToast("Das hat leider nicht geklappt. Bitte erneut versuchen.", false);
          })
          .finally(function () {
            isSubmitting = false;
            if (stickyBtn) stickyBtn.disabled = false;
          });
      });
    });

    /* ---------- Sticky Add-to-Cart-Bar ---------- */
    var stickyBar = document.getElementById("sticky-atc");
    var atcAnchor = document.querySelector(".add-to-cart-btn");
    if (stickyBar && atcAnchor) {
      new IntersectionObserver(function (entries) {
        var show = !entries[0].isIntersecting;
        stickyBar.classList.toggle("show", show);
        stickyBar.setAttribute("aria-hidden", show ? "false" : "true");
      }, { rootMargin: "-80px 0px 0px 0px" }).observe(atcAnchor);
      var stickyBtn2 = stickyBar.querySelector(".sticky-atc-btn");
      if (stickyBtn2) {
        stickyBtn2.addEventListener("click", function () {
          var form = atcAnchor.closest("form");
          if (form) { if (form.requestSubmit) form.requestSubmit(); else form.submit(); }
        });
      }
    }

    /* ---------- Produktgalerie: Crossfade + aktiver Thumb ---------- */
    var mainImg = document.getElementById("ProductMainImage");
    if (mainImg) {
      document.querySelectorAll(".thumb-btn").forEach(function (btn, idx) {
        if (idx === 0) btn.classList.add("active");
        btn.addEventListener("click", function () {
          var src = btn.dataset.full;
          if (!src || mainImg.src === src) return;
          document.querySelectorAll(".thumb-btn.active").forEach(function (b) { b.classList.remove("active"); });
          btn.classList.add("active");
          if (reduced) { mainImg.removeAttribute("srcset"); mainImg.src = src; return; }
          mainImg.classList.add("swapping");
          var pre = new Image();
          pre.onload = function () {
            mainImg.removeAttribute("srcset");
            mainImg.src = src;
            requestAnimationFrame(function () { mainImg.classList.remove("swapping"); });
          };
          pre.src = src;
        });
      });
    }

    /* ---------- Variantenwahl: Preis mit Mikro-Puls ---------- */
    var select = document.getElementById("ProductSelect");
    var priceEl = document.querySelector(".price-main-lg");
    if (select && priceEl) {
      select.addEventListener("change", function () {
        var opt = select.options[select.selectedIndex];
        if (!opt.dataset.price) return;
        priceEl.classList.add("price-flash");
        priceEl.textContent = opt.dataset.price;
        var stickyPrice = document.querySelector(".sticky-atc-price");
        if (stickyPrice) stickyPrice.textContent = opt.dataset.price;
        var compareEl = document.getElementById("ComparePrice");
        var badgeEl = document.getElementById("SaleBadge");
        var compare = opt.dataset.compare || "";
        if (compareEl) { compareEl.hidden = !compare; compareEl.textContent = compare; }
        if (badgeEl) badgeEl.hidden = !compare;
        setTimeout(function () { priceEl.classList.remove("price-flash"); }, 450);
      });
    }

    /* ---------- Mengen-Stepper ---------- */
    document.querySelectorAll(".qty-stepper").forEach(function (stepper) {
      var input = stepper.querySelector("input");
      stepper.addEventListener("click", function (e) {
        var b = e.target.closest("button[data-step]");
        if (!b || !input) return;
        e.preventDefault();
        var min = parseInt(input.min || "0", 10);
        input.value = Math.max(min, (parseInt(input.value, 10) || 0) + parseInt(b.dataset.step, 10));
        input.dispatchEvent(new Event("input", { bubbles: true }));
      });
    });

    /* ---------- Mengen-Deal-Picker: 2 kaufen 1 gratis usw. ----------
       Klick setzt das echte Mengenfeld auf 3/6/9 - der automatische
       Shopify-Rabatt zieht die Gratis-Flaschen an der Kasse ab. */
    var qtyInput = document.getElementById("Quantity");
    var dealOpts = document.querySelectorAll(".deal-opt");
    var dealHint = document.getElementById("DealHint");
    if (qtyInput && dealOpts.length) {
      function syncDeal(qty) {
        var matched = false;
        dealOpts.forEach(function (o) {
          var on = o.dataset.qty === String(qty);
          o.classList.toggle("active", on);
          if (on) matched = true;
        });
        if (dealHint) dealHint.hidden = !(matched && String(qty) !== "1");
      }
      dealOpts.forEach(function (o) {
        o.addEventListener("click", function () {
          qtyInput.value = o.dataset.qty;
          syncDeal(o.dataset.qty);
        });
      });
      qtyInput.addEventListener("input", function () { syncDeal(qtyInput.value); });
      syncDeal(qtyInput.value);
    }

    /* ---------- Bild-Skeletons ---------- */
    document.querySelectorAll(".product-img-wrap img, .product-gallery-main img").forEach(function (img) {
      var wrap = img.closest(".product-img-wrap, .product-gallery-main");
      if (!wrap) return;
      var done = function () { wrap.classList.add("img-loaded"); };
      if (img.complete && img.naturalWidth > 0) done();
      else { img.addEventListener("load", done, { once: true }); img.addEventListener("error", done, { once: true }); }
    });
  });
})();
