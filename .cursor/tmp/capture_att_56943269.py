from pathlib import Path
from playwright.sync_api import sync_playwright
import time

dest = Path(r"C:\Users\PC ENTER\Downloads\yoummday temporaries")
dest.mkdir(parents=True, exist_ok=True)
out = dest / "56943269_attachment_capture.png"
CARD = 'section[data-tracker-event-id="@conversation/chatItemsList/mediaPreviewCard"]'
VIEW_BTN = 'button[data-testid="VIEW_DETAIL-iconBtn-with-tooltip"], button[data-entityid="VIEW_DETAIL"]'

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
    img = card.locator('img[data-testid="lazyloadedImg"]').first
    src = img.get_attribute("src") if img.count() else None
    print("THUMB_SRC", (src or "")[:300])
    card.scroll_into_view_if_needed()
    card.hover()
    time.sleep(0.4)
    card.locator(VIEW_BTN).first.click(timeout=5000)
    time.sleep(1.5)
    page.screenshot(path=str(out), full_page=False)
    print("SCREENSHOT", out, out.stat().st_size)
    # try download via API response / blob from largest img
    imgs = page.locator("img")
    n = imgs.count()
    print("IMG_COUNT", n)
    best = None
    best_area = 0
    for i in range(min(n, 30)):
        el = imgs.nth(i)
        try:
            box = el.bounding_box()
            s = el.get_attribute("src") or ""
            if box and s:
                area = (box.get("width") or 0) * (box.get("height") or 0)
                if area > best_area and area > 20000:
                    best_area = area
                    best = (i, s, box)
        except Exception:
            pass
    if best:
        i, s, box = best
        print("BEST", i, "area", best_area, "src", s[:200], "box", box)
        crop = dest / "56943269_attachment_crop.png"
        el = imgs.nth(i)
        el.screenshot(path=str(crop))
        print("CROP", crop, crop.stat().st_size)
        if s.startswith("http"):
            raw = dest / "56943269_fileUpload_1.png"
            r = page.request.get(s)
            raw.write_bytes(r.body())
            print("FETCHED", raw, raw.stat().st_size)
