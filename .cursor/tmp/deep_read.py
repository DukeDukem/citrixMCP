from playwright.sync_api import sync_playwright
import re
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
    # Try broader content extraction
    body = page.inner_text("body")
    # Find Beschwerde-related chunks
    for key in ["Beschwerde", "Kuntz", "Monika", "Helfried", "4799", "Rechnung", "Kündigung"]:
        if key.lower() in body.lower():
            print(f"FOUND: {key}")
    # Get aria labels / case title
    title = page.locator('[data-testid="case-subject"], [aria-label*="Beschwerde"]').all_inner_texts()
    print("titles:", title[:5])
    # Search message list items
    items = page.locator('[data-testid*="message"], [class*="message"]').count()
    print("message-like:", items)
    # Dump a slice around Beschwerde if present
    idx = body.lower().find("beschwerde")
    if idx >= 0:
        print("---CONTEXT---")
        print(body[max(0,idx-500):idx+2000])
