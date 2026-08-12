from playwright.sync_api import sync_playwright
import pathlib
p = pathlib.Path(".").resolve()
with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page(viewport={"width":1080,"height":1920}, device_scale_factor=1)
    pg.goto("file://%s/marke.html" % p)
    pg.wait_for_timeout(800)
    pg.locator("#ab").screenshot(path="abspann.png")
    for el in ("ecke","satz1","satz2","satz3","satz4"):
        pg.locator("#"+el).screenshot(path=el+".png", omit_background=True)
    print("ok")
    b.close()
