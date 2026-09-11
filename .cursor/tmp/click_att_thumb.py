from pathlib import Path
from playwright.sync_api import sync_playwright
import time

dest = Path(r"C:\Users\PC ENTER\Downloads\yoummday temporaries")
dest.mkdir(parents=True, exist_ok=True)
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
    if not page:
        raise SystemExit("no page")
    page.bring_to_front()
    card = page.locator(CARD).first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    print("CARD_BOX", box)
    if not box:
        raise SystemExit("no box")
    # click center of thumbnail/card only — no View Detail / Download
    x = box["x"] + box["width"] / 2
    y = box["y"] + box["height"] / 2
    print(f"CLICK {x:.0f},{y:.0f}")
    page.mouse.click(x, y)
    time.sleep(1.2)
    out = dest / "56943269_after_thumb_click.png"
    page.screenshot(path=str(out), full_page=False)
    print("SCREENSHOT", out, out.stat().st_size)
    # also try screenshot of any large overlay image
    imgs = page.locator("img")
    for i in range(imgs.count()):
        el = imgs.nth(i)
        b = el.bounding_box()
        if not b:
            continue
        if b["width"] * b["height"] < 40000:
            continue
        path = dest / f"56943269_after_click_img_{i}.png"
        el.screenshot(path=str(path))
        print("IMG", path.name, int(b["width"]), int(b["height"]), path.stat().st_size)
