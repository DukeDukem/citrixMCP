"""Shared CDP helpers for call-listen probe / watch."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from playwright.sync_api import Browser, Page, sync_playwright

_REPO = Path(__file__).resolve().parent.parent.parent.parent
_DEFAULT_CDP = "http://127.0.0.1:9222"


def load_cdp_endpoint() -> str:
    cfg = _REPO / "config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            ep = data.get("cdp_endpoint") or data.get("CDP_ENDPOINT")
            if ep:
                return str(ep).replace("localhost", "127.0.0.1")
        except Exception:
            pass
    import os

    return (
        os.environ.get("SPRINKLR_CDP_ENDPOINT")
        or os.environ.get("CDP_ENDPOINT")
        or _DEFAULT_CDP
    ).replace("localhost", "127.0.0.1")


def find_sprinklr_page(browser: Browser) -> Optional[Page]:
    sprinklr_hosts = (
        "telefonica-germany.sprinklr.com",
        "telefonica-germany-app.sprinklr.com",
        "sprinklr.com",
    )
    pages: list[Page] = []
    for ctx in browser.contexts:
        try:
            pages.extend(ctx.pages or [])
        except Exception:
            continue
    for p in pages:
        try:
            u = (p.url or "").lower()
            if u.startswith("devtools://"):
                continue
            if any(h in u for h in sprinklr_hosts):
                return p
        except Exception:
            continue
    return None


def extract_fall_id(page: Page) -> Optional[str]:
    try:
        text = page.locator("body").inner_text(timeout=3000)
    except Exception:
        text = ""
    m = re.search(r"Fall\s*#?\s*(\d{6,})", text, re.I)
    if m:
        return m.group(1)
    try:
        aria = page.locator("[aria-label*='Fall']").first.get_attribute("aria-label") or ""
        m2 = re.search(r"(\d{6,})", aria)
        if m2:
            return m2.group(1)
    except Exception:
        pass
    return None


def call_markers(page: Page) -> dict[str, Any]:
    js = """
() => {
  const t = (document.body && document.body.innerText) || '';
  const has = (s) => t.indexOf(s) !== -1;
  const q = (sel) => document.querySelectorAll(sel).length;
  return {
    imGespraech: has('Im Gespräch'),
    eingehenderAnruf: has('Eingehender Anruf'),
    anrufBeendet: has('Anruf beendet'),
    disposition: has('Disposition'),
    audioPres: q('[data-testid="audio_pres"]'),
    omniMedia: q('[data-testid="omniMedia"], [data-testid*="omniMedia"]'),
    callButton: q('[data-testid="call-button"]'),
    htmlMessage: q('[data-testid="html-message-content"]'),
  };
}
"""
    try:
        return page.evaluate(js) or {}
    except Exception as e:
        return {"error": str(e)}


def is_call_channel(markers: dict[str, Any]) -> bool:
    if markers.get("imGespraech") or markers.get("disposition"):
        return True
    if markers.get("eingehenderAnruf"):
        return True
    if (markers.get("audioPres") or 0) > 0 and (markers.get("htmlMessage") or 0) == 0:
        return True
    return False


def connect_browser(endpoint: str | None = None):
    """Context manager-ish: returns (playwright, browser). Caller must stop playwright."""
    ep = endpoint or load_cdp_endpoint()
    pw = sync_playwright().start()
    browser = pw.chromium.connect_over_cdp(ep)
    return pw, browser, ep
