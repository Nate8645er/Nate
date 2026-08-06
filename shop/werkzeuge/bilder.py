#!/usr/bin/env python3
import functools, http.server, os, threading

HIER = os.path.dirname(os.path.abspath(__file__))
SPIEGEL = HIER + "/spiegel"
PORT = 8732

h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=SPIEGEL)
srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), h)
threading.Thread(target=srv.serve_forever, daemon=True).start()

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(args=["--no-proxy-server"])
    for seite in ["start", "produkt"]:
        for name, vp in [("handy", {"width": 390, "height": 844}),
                         ("breit", {"width": 1280, "height": 900})]:
            ctx = b.new_context(viewport=vp, device_scale_factor=1)
            ctx.route("**/*", lambda r: r.abort()
                      if "127.0.0.1" not in r.request.url else r.continue_())
            pg = ctx.new_page()
            pg.goto(f"http://127.0.0.1:{PORT}/{seite}.html",
                    wait_until="domcontentloaded", timeout=30000)
            pg.wait_for_timeout(1800)
            pg.screenshot(path=f"{HIER}/bild-{seite}-{name}.png",
                          full_page=True)
            print("geschrieben", seite, name)
            ctx.close()
    b.close()
