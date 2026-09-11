from playwright.sync_api import sync_playwright
import time

CASE = "6a6d0ba36156a1e66de48c85"
time.sleep(1)
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    target = None
    for page in browser.contexts[0].pages:
        if CASE in (page.url or ""):
            target = page
            break
    if not target:
        raise SystemExit("case tab not found")
    target.bring_to_front()
    frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    text = frame.locator("body#tinymce").inner_text(timeout=5000) if frame else ""
    print("LEN", len(text))
    print("HAS_ANTWORT", "[Antwort]" in text)
    print("HAS_SURVEY", "Zur Verbesserung unseres Kundenservices" in text)
    print("HAS_SIG", "Freundliche Grüße" in text)
    print("HAS_BODY", "14.08.2026" in text and "Rufnummernmitnahme" in text)
    print("START", repr(text[:100]))
