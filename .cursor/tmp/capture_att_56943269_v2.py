from pathlib import Path
from playwright.sync_api import sync_playwright
import time

dest = Path(r"C:\Users\PC ENTER\Downloads\yoummday temporaries")
dest.mkdir(parents=True, exist_ok=True)
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

    # Prefer images inside media cards / attachment drawer
    cards = page.locator(CARD)
    print("CARDS", cards.count())
    for i in range(cards.count()):
        card = cards.nth(i)
        card.scroll_into_view_if_needed()
        for img_i in range(card.locator("img").count()):
            el = card.locator("img").nth(img_i)
            src = el.get_attribute("src") or ""
            box = el.bounding_box()
            print(f"card{i}_img{img_i}", box, src[:120])
            path = dest / f"56943269_card{i}_img{img_i}.png"
            try:
                el.screenshot(path=str(path))
                print("saved", path.name, path.stat().st_size)
            except Exception as e:
                print("shot fail", e)
            if src:
                abs_url = page.evaluate(
                    "(s) => { try { return new URL(s, location.href).href } catch(e) { return s } }",
                    src,
                )
                try:
                    r = page.request.get(abs_url)
                    body = r.body()
                    raw = dest / f"56943269_fetched_card{i}_img{img_i}.png"
                    raw.write_bytes(body)
                    print("fetched", raw.name, len(body), "status", r.status)
                except Exception as e:
                    print("fetch fail", e)

    # click View Detail again and screenshot attachment side panel images
    try:
        card0 = cards.first
        card0.hover()
        time.sleep(0.4)
        card0.locator(VIEW_BTN).first.click(timeout=4000)
        time.sleep(1.2)
    except Exception as e:
        print("view", e)

    page.screenshot(path=str(dest / "56943269_after_view.png"), full_page=False)
    imgs = page.locator("img")
    for i in range(imgs.count()):
        el = imgs.nth(i)
        box = el.bounding_box()
        if not box:
            continue
        area = box["width"] * box["height"]
        if area < 25000:
            continue
        path = dest / f"56943269_large_{i}_{int(box['width'])}x{int(box['height'])}.png"
        el.screenshot(path=str(path))
        print("large", path.name, path.stat().st_size)
