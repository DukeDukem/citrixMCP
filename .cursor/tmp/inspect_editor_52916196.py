from playwright.sync_api import sync_playwright

CASE = "6a6d079d6156a1e66d6982b4"
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
    print("HAS_SECURITY", "letzten 4 Stellen Ihrer IBAN" in text)
    print("HAS_FULL_IBAN", "DE91" in text or "401545300035281294" in text)
    print("START", repr(text[:100]))
