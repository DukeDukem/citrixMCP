from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for c in b.contexts:
        for pg in c.pages:
            if "sprinklr" in (pg.url or ""):
                page = pg
                break
        if page:
            break
    msgs = page.locator('[data-testid="html-message-content"]')
    n = msgs.count()
    for i in range(3, n):
        t = msgs.nth(i).inner_text().strip().replace("\r", "")
        print(f"---MSG{i}---")
        print(t[:3000])
        print()
