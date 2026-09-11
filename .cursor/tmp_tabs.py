from playwright.sync_api import sync_playwright
p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
for c in b.contexts:
    for pg in c.pages:
        u = pg.url or ""
        print(u[:140])
p.stop()
