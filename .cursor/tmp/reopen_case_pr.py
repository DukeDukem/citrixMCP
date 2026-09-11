from playwright.sync_api import sync_playwright
import urllib.request
import json

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "sprinklr" in (pg.url or ""):
                page = pg
                break
        if page:
            break
    if not page:
        print("no sprinklr page")
        raise SystemExit(1)
    print("url", page.url)
    checks = [
        '[data-testid="html-message-content"]',
        'section[aria-label="Nachricht verfassen"]',
        '[data-testid="collapsed-case-item"]',
    ]
    for sel in checks:
        print(sel, page.locator(sel).count())
    # Prefer clicking Fall # in UI
    for text in ["#53995997", "53995997", "Bendert", "Lukas"]:
        loc = page.get_by_text(text, exact=False)
        print("text", text, loc.count())
    # Click first collapsed case item if present
    collapsed = page.locator('[data-testid="collapsed-case-item"]')
    if collapsed.count():
        print("clicking collapsed-case-item 0")
        collapsed.first.click(timeout=5000)
        page.wait_for_timeout(2500)
    else:
        # try case id text click
        loc = page.get_by_text("53995997", exact=False)
        if loc.count():
            loc.first.click(timeout=5000)
            page.wait_for_timeout(2500)
    for sel in checks:
        print("after", sel, page.locator(sel).count())
    print("url_after", page.url)
