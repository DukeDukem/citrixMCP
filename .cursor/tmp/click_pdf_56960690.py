from pathlib import Path
from playwright.sync_api import sync_playwright
import time

dest = Path(r"C:\Users\PC ENTER\Downloads\yoummday temporaries")
CARD = 'section[data-tracker-event-id="@conversation/chatItemsList/mediaPreviewCard"]'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "sprinklr" in (pg.url or "").lower():
                page = pg
                break
        if page:
            break
    page.bring_to_front()
    card = page.locator(CARD).first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    print("BOX", box)
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    time.sleep(1.5)
    out = dest / "56960690_att_click.png"
    page.screenshot(path=str(out), full_page=False)
    print("SHOT", out, out.stat().st_size)
