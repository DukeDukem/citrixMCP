from playwright.sync_api import sync_playwright

CASE = "6a6932006156a1e66d9393e7"
MARKERS = ["Sicherheitsmaßnahme", "Vertragsverlängerung", "Kundennummer", "IBAN"]

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
    body = target.inner_text("body")[:1500]
    print("---PAGE---")
    for line in body.splitlines():
        if any(k in line for k in ["Fall", "52546594", "Homaei", "Solmaz"]):
            print(line[:200])
    frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    text = frame.locator("body#tinymce").inner_text(timeout=5000) if frame else ""
    print("---EDITOR---")
    print("LEN", len(text))
    print("HAS_ANTWORT", "[Antwort]" in text)
    print("FIRST", text.splitlines()[0] if text else "")
    for m in MARKERS:
        print(f"HAS_{m}", m in text)
    print(text[:400])
