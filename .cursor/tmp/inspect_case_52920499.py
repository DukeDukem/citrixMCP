from playwright.sync_api import sync_playwright

CASE = "6a6d8ec5fc7ca77679c1cef6"
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
    body = target.inner_text("body")
    print("---CASE LINES---")
    for line in body.splitlines():
        if any(k.lower() in line.lower() for k in [
            "fall", "52920499", "linkspatsche", "kundennummer", "anliegen",
            "28.07", "30. juli", "guten", "iban", "geburt", "name", "künd",
            "rechnung", "vertrag", "sim", "tarif"
        ]):
            print(line[:300])
    # try html message content
    try:
        msgs = target.locator("[data-testid='html-message-content']").all_inner_texts()
        print("---MSG COUNT---", len(msgs))
        for i, m in enumerate(msgs[:5]):
            print(f"---MSG {i} LEN {len(m)}---")
            print(m[:1500])
            print("---END---")
    except Exception as e:
        print("msg err", e)
