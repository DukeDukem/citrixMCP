"""
Open or download Sprinklr case attachments on the visible EMAIL case.

Usage:
  uv run python .cursor/skills/sprinklr-read-answer-email/open_case_attachments.py --view
  uv run python .cursor/skills/sprinklr-read-answer-email/open_case_attachments.py --download
  uv run python .cursor/skills/sprinklr-read-answer-email/open_case_attachments.py --list

Requires Chrome CDP on port 9222 (login first).
Downloads always go to: C:\\Users\\PC ENTER\\Downloads\\yoummday temporaries
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("ERROR: Playwright not installed", file=sys.stderr)
    sys.exit(1)

CDP_ENDPOINT = "http://127.0.0.1:9222"
DOWNLOAD_DIR = Path(r"C:\Users\PC ENTER\Downloads\yoummday temporaries")
CARD = 'section[data-tracker-event-id="@conversation/chatItemsList/mediaPreviewCard"]'
VIEW_BTN = 'button[data-testid="VIEW_DETAIL-iconBtn-with-tooltip"], button[data-entityid="VIEW_DETAIL"]'
DL_BTN = 'button[data-testid="DOWNLOAD-iconBtn-with-tooltip"], button[data-entityid="DOWNLOAD"]'


def _sprinklr_page(browser):
    for ctx in browser.contexts:
        for page in ctx.pages:
            url = (page.url or "").lower()
            if "sprinklr" in url or "space" in url or "care" in url:
                return page, ctx
    if browser.contexts and browser.contexts[0].pages:
        return browser.contexts[0].pages[0], browser.contexts[0]
    return None, None


def _set_download_path(page, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    try:
        cdp = page.context.new_cdp_session(page)
        cdp.send(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": str(dest.resolve())},
        )
    except Exception as e:
        print(f"WARN: could not set download path via CDP: {e}", flush=True)


def _card_name(card) -> str:
    try:
        img = card.locator('img[data-testid="lazyloadedImg"]').first
        if img.count():
            alt = (img.get_attribute("alt") or "").strip()
            if alt:
                return alt
    except Exception:
        pass
    try:
        t = card.locator('[data-spaceweb="typography-l4"]').first
        if t.count():
            return (t.inner_text(timeout=500) or "").strip() or "?"
    except Exception:
        pass
    return "?"


def list_cards(page) -> list:
    cards = page.locator(CARD).all()
    return cards


def cmd_list(page) -> int:
    cards = list_cards(page)
    n = len(cards)
    if n == 0:
        print("ATTACHMENTS_NONE")
        return 0
    print(f"ATTACHMENTS_FOUND N={n}")
    for i, c in enumerate(cards):
        print(f"ATTACHMENT[{i}] name={_card_name(c)}")
    return 0


def cmd_view(page) -> int:
    cards = list_cards(page)
    n = len(cards)
    if n == 0:
        print("ATTACHMENTS_NONE")
        return 0
    print(f"ATTACHMENTS_FOUND N={n}")
    for i, card in enumerate(cards):
        name = _card_name(card)
        lower = (name or "").lower()
        try:
            card.scroll_into_view_if_needed(timeout=3000)
            # .png → click the card itself (not View Detail / Download)
            if lower.endswith(".png"):
                card.click(timeout=5000)
                print(f"ATTACHMENT_CLICKED index={i} name={name} mode=png_direct")
                time.sleep(0.8)
                continue
            card.hover(timeout=3000)
            time.sleep(0.35)
            btn = card.locator(VIEW_BTN).first
            if not btn.count():
                btn = page.locator(VIEW_BTN).nth(i)
            btn.click(timeout=5000)
            print(f"ATTACHMENT_VIEWED index={i} name={name} mode=view_detail")
            time.sleep(0.8)
        except Exception as e:
            print(f"ATTACHMENT_VIEW_FAIL index={i} name={name} err={e}")
    return 0


def cmd_download(page) -> int:
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _set_download_path(page, DOWNLOAD_DIR)
    cards = list_cards(page)
    n = len(cards)
    if n == 0:
        print("ATTACHMENTS_NONE")
        return 0
    print(f"ATTACHMENTS_FOUND N={n}")
    print(f"DOWNLOAD_DIR {DOWNLOAD_DIR}")
    for i, card in enumerate(cards):
        name = _card_name(card)
        try:
            card.scroll_into_view_if_needed(timeout=3000)
            card.hover(timeout=3000)
            time.sleep(0.35)
            btn = card.locator(DL_BTN).first
            if not btn.count():
                btn = page.locator(DL_BTN).nth(i)
            with page.expect_download(timeout=60000) as dl_info:
                btn.click(timeout=5000)
            download = dl_info.value
            suggested = download.suggested_filename or name or f"attachment_{i}"
            dest = DOWNLOAD_DIR / suggested
            # avoid overwrite collisions
            if dest.exists():
                stem, suf = dest.stem, dest.suffix
                dest = DOWNLOAD_DIR / f"{stem}_{int(time.time())}{suf}"
            download.save_as(str(dest))
            print(f"ATTACHMENT_DOWNLOADED index={i} name={name} path={dest}")
        except Exception as e:
            print(f"ATTACHMENT_DOWNLOAD_FAIL index={i} name={name} err={e}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Sprinklr case attachments")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--list", action="store_true", help="List attachment cards")
    g.add_argument("--view", action="store_true", help="Hover + View Detail each card")
    g.add_argument("--download", action="store_true", help="Download all to yoummday temporaries")
    args = ap.parse_args()

    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
        except Exception as e:
            print(f"ERROR: CDP connect failed: {e}", file=sys.stderr)
            print("Start Chrome with --remote-debugging-port=9222 (login first).", file=sys.stderr)
            return 1
        page, _ctx = _sprinklr_page(browser)
        if page is None:
            print("ERROR: No Sprinklr page found", file=sys.stderr)
            return 1
        page.bring_to_front()
        if args.list:
            return cmd_list(page)
        if args.view:
            return cmd_view(page)
        if args.download:
            return cmd_download(page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
