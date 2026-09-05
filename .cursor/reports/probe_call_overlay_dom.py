"""Probe Sprinklr CDP DOM for call vs email markers (one-shot)."""
from __future__ import annotations

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

_OUT = Path(".cursor/reports/sprinklr-call-overlay-dom-2026-09-05.json")

_JS = r"""
() => {
  const text = (el) => (el && (el.innerText || el.textContent) || '').replace(/\s+/g,' ').trim();
  const pick = (sel) => Array.from(document.querySelectorAll(sel)).slice(0, 20).map(el => ({
    tag: el.tagName,
    testid: el.getAttribute('data-testid'),
    entity: el.getAttribute('data-entityid'),
    aria: el.getAttribute('aria-label'),
    className: (el.className || '').toString().slice(0, 100),
    text: text(el).slice(0, 200)
  }));
  const bodySample = text(document.body).slice(0, 4000);
  const has = (s) => bodySample.toLowerCase().includes(String(s).toLowerCase());
  const overlayHits = Array.from(document.querySelectorAll('div,section,aside,article'))
    .filter(el => /Im Gespräch|Disposition|VOIP|Anruf beendet|Medienauslagerung|o2 Disposition/i.test(text(el)))
    .slice(0, 12)
    .map(el => ({
      tag: el.tagName,
      testid: el.getAttribute('data-testid'),
      entity: el.getAttribute('data-entityid'),
      className: (el.className || '').toString().slice(0, 120),
      text: text(el).slice(0, 240)
    }));
  return {
    url: location.href,
    title: document.title,
    fallHeader: text(document.querySelector('h2, h1')),
    markers: {
      ImGespraech: has('Im Gespräch') || has('Im Gesprach'),
      Anruf: /\bAnruf\b/i.test(bodySample),
      AnrufBeendet: has('Anruf beendet'),
      Aufzeichnung: has('Aufzeichnung'),
      Disposition: has('Disposition'),
      VOIP: has('VOIP') || has('Nailed Up'),
      Mikrofon: has('Mikrofon'),
      QuelleAura: has('Aura Care'),
      NachrichtVerfassen: !!document.querySelector('section[aria-label="Nachricht verfassen"]'),
      TinyMCE: !!document.querySelector('iframe.tox-edit-area__iframe, body#tinymce'),
    },
    quelleZiel: pick('[data-entityid="Quelle"], [data-entityid="Ziel"], [aria-label="Quelle"], [aria-label="Ziel"]'),
    audioLike: pick('[data-testid*="audio" i], audio, [aria-label*="Anruf" i], [data-testid*="recording" i]'),
    overlays: overlayHits
  };
}
"""


def main() -> int:
    with sync_playwright() as p:
        try:
            browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        except Exception as e:
            print(f"NO_CDP: {e}")
            return 1
        pages = [pg for ctx in browser.contexts for pg in ctx.pages]
        print(f"PAGES {len(pages)}")
        hit = False
        for i, page in enumerate(pages):
            u = (page.url or "").lower()
            t = (page.title() or "").lower()
            print(f"--- {i} title={(page.title() or '')[:80]!r} url={(page.url or '')[:120]!r}")
            if "sprinklr" not in u and "sprinklr" not in t:
                continue
            info = page.evaluate(_JS)
            _OUT.parent.mkdir(parents=True, exist_ok=True)
            _OUT.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"WROTE {_OUT}")
            print(json.dumps(info.get("markers"), ensure_ascii=False, indent=2))
            print("fallHeader:", info.get("fallHeader"))
            for o in (info.get("overlays") or [])[:8]:
                print("overlay:", o.get("testid"), o.get("text", "")[:120])
            hit = True
            break
        if not hit:
            print("NO_SPRINKLR_PAGE")
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
