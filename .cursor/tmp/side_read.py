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
    kn = page.query_selector('div[data-entityid="Kundennummer"][aria-label="Kundennummer"]')
    kn_txt = ""
    if kn:
        ht = kn.query_selector('[data-testid="htmlText"]')
        spr = kn.query_selector("span.spr-text-03")
        kn_txt = (ht.inner_text() if ht else (spr.inner_text() if spr else kn.inner_text())).strip()
    for eid in ["Fallnummer", "Quelle", "Ziel"]:
        el = page.query_selector(f'div[data-entityid="{eid}"]')
        val = ""
        if el:
            ht = el.query_selector('[data-testid="htmlText"]')
            val = (ht.inner_text() if ht else el.inner_text()).strip()[:150]
        print(f"{eid}: {val}")
    print(f"Kundennummer: {kn_txt}")
    print("Im Gespräch:", page.locator("text=Im Gespräch").count())
    print("html-message:", page.locator('[data-testid="html-message-content"]').count())
    msgs = page.locator('[data-testid="html-message-content"]')
    n = msgs.count()
    print(f"MSG_COUNT: {n}")
    for i in range(min(n, 4)):
        t = msgs.nth(i).inner_text().strip().replace("\r", "")
        print(f"---MSG{i}---")
        print(t[:2000])
        print()
