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
    checks = {
        "Im Gespräch": page.locator("text=Im Gespräch").count(),
        "Eingehender Anruf": page.locator("text=Eingehender Anruf").count(),
        "Disposition": page.locator("text=Disposition").count(),
        "html-message": page.locator('[data-testid="html-message-content"]').count(),
        "Nachricht verfassen": page.locator('section[aria-label="Nachricht verfassen"]').count(),
        "Anruf beendet": page.locator("text=Anruf beendet").count(),
    }
    for k,v in checks.items():
        print(f"{k}: {v}")
