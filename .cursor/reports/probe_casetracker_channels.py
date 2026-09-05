"""List Roberta Case Tracker channel radio IDs (Voice vs E-Mail Care)."""
from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

_JS = r"""
() => {
  const channels = [...document.querySelectorAll('[id^=channel], input[name="channel"], input[name*=channel i]')].map(el => ({
    id: el.id, name: el.name, value: el.value, type: el.type, checked: !!el.checked
  }));
  const labels = [...document.querySelectorAll('label')].filter(l =>
    /Voice|Tel|E-Mail|Kanal|Chat|Social|Care/i.test(l.innerText || '')
  ).map(l => ({
    for: l.htmlFor,
    text: (l.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 120)
  }));
  const html = document.documentElement.innerHTML;
  const ids = [...html.matchAll(/id=["'](channel_[^"']+)["']/g)].map(m => m[1]);
  return { channels, labels: labels.slice(0, 40), channelIds: [...new Set(ids)] };
}
"""


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = next(
            (
                pg
                for ctx in browser.contexts
                for pg in ctx.pages
                if "casetracker" in (pg.url or "").lower()
            ),
            None,
        )
        if not page:
            print("NO_TRACKER")
            return 1
        page.bring_to_front()
        info = page.evaluate(_JS)
        print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
