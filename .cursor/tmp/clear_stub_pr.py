from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for pg in browser.contexts[0].pages:
        u = pg.url or ""
        if "sprinklr.com" in u and "/console/" in u:
            page = pg
            break
    if not page:
        raise SystemExit("no sprinklr tab")
    page.bring_to_front()
    print("URL", page.url)
    body = page.inner_text("body")[:2000]
    for line in body.splitlines():
        if any(k in line for k in ["Fall", "52546594", "Homaei", "Solmaz", "Guten Tag", "[Antwort]"]):
            print(line[:220])
    frame = page.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    if not frame:
        raise SystemExit("no editor frame")
    text = frame.locator("body#tinymce").inner_text(timeout=5000)
    print("BEFORE_LEN", len(text))
    print("HAS_ANTWORT", "[Antwort]" in text)
    print(text[:500])
    frame.locator("body#tinymce").click()
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    time.sleep(0.4)
    after = frame.locator("body#tinymce").inner_text(timeout=5000).strip()
    print("AFTER_LEN", len(after))
    print("CLEARED", after == "")
