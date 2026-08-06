#!/usr/bin/env python3
"""Misst am lokalen Spiegel, was der Kunde tatsaechlich sieht:
Kontrast jedes sichtbaren Textknotens gegen seinen wirksamen Grund,
Zahl der Uebergaenge, Endlosbewegungen, sofort sichtbarer Textanteil
und Querlauf bei sechs Breiten.
"""
import json, os, subprocess, sys, threading, http.server, functools

HIER = os.path.dirname(os.path.abspath(__file__))
SPIEGEL = HIER + "/spiegel"
PORT = 8731

JS = r"""
() => {
  const lum = (r, g, b) => {
    const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(r) + 0.7152*f(g) + 0.0722*f(b);
  };
  const parse = s => {
    const m = s && s.match(/rgba?\(([^)]+)\)/);
    if (!m) return null;
    const p = m[1].split(/[,\s\/]+/).filter(x => x !== '').map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const ueber = (fg, bg) => ({
    r: fg.a*fg.r + (1-fg.a)*bg.r,
    g: fg.a*fg.g + (1-fg.a)*bg.g,
    b: fg.a*fg.b + (1-fg.a)*bg.b, a: 1
  });
  const grundVon = el => {
    let bg = { r: 255, g: 255, b: 255, a: 1 };
    const kette = [];
    for (let n = el; n; n = n.parentElement) {
      const c = parse(getComputedStyle(n).backgroundColor);
      if (c && c.a > 0) kette.unshift(c);
    }
    for (const c of kette) bg = c.a >= 1 ? c : ueber(c, bg);
    return bg;
  };
  const pfad = el => {
    const t = [];
    for (let n = el; n && n.tagName && t.length < 5; n = n.parentElement)
      t.unshift(n.tagName.toLowerCase() + (n.className && typeof n.className === 'string'
        ? '.' + n.className.trim().split(/\s+/).slice(0,2).join('.') : ''));
    return t.join(' > ');
  };

  const res = { texte: [], unter45: [], blass: [], uebergaenge: 0, endlos: 0,
                sichtbar: 0, gesamt: 0 };

  for (const el of document.querySelectorAll('*')) {
    const st = getComputedStyle(el);
    if (st.transitionDuration && st.transitionDuration.split(',').some(d => parseFloat(d) > 0))
      res.uebergaenge++;
    if (st.animationIterationCount && st.animationIterationCount.split(',')
        .some(c => c.trim() === 'infinite') && st.animationName !== 'none')
      res.endlos++;

    // eigener Textinhalt?
    let txt = '';
    for (const n of el.childNodes)
      if (n.nodeType === 3) txt += n.textContent;
    txt = txt.trim();
    if (!txt) continue;
    const r = el.getBoundingClientRect();
    if (st.display === 'none' || st.visibility === 'hidden') continue;
    if (r.width < 1 || r.height < 1) continue;

    res.gesamt++;
    const op = parseFloat(st.opacity);
    if (op > 0.05) res.sichtbar++;
    else res.blass.push({ op, pfad: pfad(el), text: txt.slice(0, 40) });

    const fg0 = parse(st.color);
    if (!fg0) continue;
    const bg = grundVon(el);
    const fg = fg0.a >= 1 ? fg0 : ueber(fg0, bg);
    const l1 = lum(fg.r, fg.g, fg.b), l2 = lum(bg.r, bg.g, bg.b);
    const k = (Math.max(l1,l2) + 0.05) / (Math.min(l1,l2) + 0.05);
    const gross = parseFloat(st.fontSize) >= 24 ||
                  (parseFloat(st.fontSize) >= 18.66 && parseInt(st.fontWeight) >= 700);
    const schwelle = gross ? 3.0 : 4.5;
    const eintrag = { k: +k.toFixed(2), px: Math.round(parseFloat(st.fontSize)),
      fg: `rgb(${Math.round(fg.r)},${Math.round(fg.g)},${Math.round(fg.b)})`,
      bg: `rgb(${Math.round(bg.r)},${Math.round(bg.g)},${Math.round(bg.b)})`,
      pfad: pfad(el), text: txt.slice(0, 40), schwelle };
    res.texte.push(eintrag);
    if (k < schwelle && op > 0.05) res.unter45.push(eintrag);
  }
  res.hintergrund = getComputedStyle(document.body).backgroundColor;
  res.schrift = getComputedStyle(document.body).color;
  res.farbeAttr = document.documentElement.getAttribute('data-farbe');
  return res;
}
"""


def server():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SPIEGEL)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    from playwright.sync_api import sync_playwright
    server()
    aus = {}
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--no-proxy-server"])
        for seite in ["start", "produkt"]:
            for js_an in [True, False]:
                ctx = b.new_context(viewport={"width": 390, "height": 844},
                                    java_script_enabled=js_an)
                # Alles, was nicht im Spiegel liegt, wird abgewiesen.
                # Sonst haengt der Seitenaufbau an Shopify-Bausteinen,
                # die es hier nicht gibt - und das haette mit dem
                # Aussehen des Shops nichts zu tun.
                ctx.route("**/*", lambda r: r.abort()
                          if "127.0.0.1" not in r.request.url else r.continue_())
                pg = ctx.new_page()
                pg.goto(f"http://127.0.0.1:{PORT}/{seite}.html",
                        wait_until="domcontentloaded", timeout=30000)
                pg.wait_for_timeout(1500 if js_an else 300)
                r = pg.evaluate(JS)
                aus[f"{seite}/{'js' if js_an else 'ohne-js'}"] = r
                if js_an:
                    quer = []
                    for w in [320, 360, 390, 768, 1024, 1440]:
                        pg.set_viewport_size({"width": w, "height": 800})
                        pg.wait_for_timeout(200)
                        sw = pg.evaluate("document.documentElement.scrollWidth")
                        if sw > w + 1:
                            quer.append((w, sw))
                    r["querlauf"] = quer
                ctx.close()
        b.close()

    for k, r in aus.items():
        print(f"\n=== {k} ===")
        print(f"  Grund {r['hintergrund']}  Schrift {r['schrift']}  data-farbe={r['farbeAttr']}")
        print(f"  Textstellen {r['gesamt']}, davon sofort sichtbar {r['sichtbar']}"
              f" ({100*r['sichtbar']//max(r['gesamt'],1)} %)")
        print(f"  Uebergaenge {r['uebergaenge']}   Endlosbewegungen {r['endlos']}")
        print(f"  UNTER SCHWELLE: {len(r['unter45'])}")
        for e in sorted(r["unter45"], key=lambda x: x["k"])[:25]:
            print(f"    {e['k']:>5}:1 (Schwelle {e['schwelle']})  {e['fg']} auf {e['bg']}"
                  f"  {e['px']}px\n        {e['pfad']}\n        \"{e['text']}\"")
        if r.get("blass"):
            print(f"  NICHT SICHTBAR beim Laden: {len(r['blass'])}")
            for e in r["blass"][:10]:
                print(f"    Deckung {e['op']}  {e['pfad']}\n        \"{e['text']}\"")
        if "querlauf" in r:
            print(f"  Querlauf: {r['querlauf'] or 'keiner'}")

    json.dump(aus, open(HIER + "/messung.json", "w"), ensure_ascii=False)


main()
