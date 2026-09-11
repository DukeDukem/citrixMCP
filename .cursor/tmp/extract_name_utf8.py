from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in b.contexts:
        for pg in ctx.pages:
            if "sprinklr.com" in (pg.url or ""):
                page = pg
                break
        if page:
            break
    html = page.eval_on_selector(
        '[data-testid="html-message-content"]', "el => el.innerText"
    )
    print(html)
    # also dump relevant lines
    for line in html.splitlines():
        if any(k in line for k in ("Bisheriger", "Neuer", "Name:", "Vorname", "Nachname", "Bankverbindung")):
            print("LINE:", repr(line))
