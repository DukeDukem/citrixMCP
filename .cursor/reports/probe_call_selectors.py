"""Deeper Sprinklr call-channel selectors for Fall #57114650 snapshot."""
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

_OUT = Path(".cursor/reports/sprinklr-call-vs-email-selectors-2026-09-05.json")

_JS = r"""
() => {
  const text = (el) => (el && (el.innerText || el.textContent) || '').replace(/\s+/g,' ').trim();
  const out = {};

  // Case info fields
  const fields = {};
  for (const id of ['Quelle', 'Ziel', 'Sprache', 'Fallnummer', 'Kundennummer']) {
    const box = document.querySelector(`div[data-entityid="${id}"][aria-label="${id}"], div[data-entityid="${id}"], [aria-label="${id}"]`);
    if (box) {
      fields[id] = {
        text: text(box).slice(0, 200),
        htmlText: text(box.querySelector('[data-testid="htmlText"]')),
        sprText: text(box.querySelector('span.spr-text-03'))
      };
    }
  }
  out.fields = fields;

  // Timeline / conversation items mentioning Anruf
  const anrufNodes = Array.from(document.querySelectorAll('[data-testid], button, div, span'))
    .filter(el => /\b(Anruf|Eingehender Anruf|Im Gespräch|Aufzeichnung)\b/i.test(text(el)))
    .slice(0, 40)
    .map(el => ({
      testid: el.getAttribute('data-testid'),
      entity: el.getAttribute('data-entityid'),
      aria: el.getAttribute('aria-label'),
      role: el.getAttribute('role'),
      text: text(el).slice(0, 160)
    }));
  out.anrufNodes = anrufNodes;

  // Distinct testids that look call-related
  const testids = new Set();
  document.querySelectorAll('[data-testid]').forEach(el => {
    const id = el.getAttribute('data-testid') || '';
    if (/call|audio|voip|disposition|recording|phone|anruf|media/i.test(id)) testids.add(id);
  });
  out.callishTestids = Array.from(testids).sort();

  // Visible floating widgets (short text that is specifically the overlays)
  const shortWidgets = Array.from(document.querySelectorAll('div'))
    .map(el => text(el))
    .filter(t => t.length > 10 && t.length < 280)
    .filter(t => /Im Gespräch|Disposition Codes|o2 Disposition|Mikrofon|VOIP|Medienauslagerung|Kein Disposition/i.test(t))
    .slice(0, 20);
  out.shortWidgets = [...new Set(shortWidgets)];

  // Email composer presence
  out.composer = {
    nachrichtVerfassen: !!document.querySelector('section[aria-label="Nachricht verfassen"]'),
    baseEditor: !!document.querySelector('[data-testid="baseEditorContainer"]'),
  };

  // Conversation item types
  out.conversationItems = {
    fan: document.querySelectorAll('[data-testid="inboundChatConversationItemFanMessage"]').length,
    brand: document.querySelectorAll('[data-testid="inboundChatConversationItemBrandMessage"]').length,
    htmlMessage: document.querySelectorAll('[data-testid="html-message-content"]').length,
  };

  out.bodyHas = {
    EingehenderAnruf: /Eingehender Anruf/i.test(document.body.innerText || ''),
    AnrufBeendet: /Anruf beendet/i.test(document.body.innerText || ''),
    ImGespraech: /Im Gespräch/i.test(document.body.innerText || ''),
  };

  return out;
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
                if "sprinklr" in (pg.url or "").lower() or "sprinklr" in (pg.title() or "").lower()
            ),
            None,
        )
        if not page:
            print("NO_SPRINKLR")
            return 2
        info = page.evaluate(_JS)
        _OUT.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"WROTE {_OUT}")
        print("fields:", json.dumps(info.get("fields"), ensure_ascii=False, indent=2))
        print("callishTestids:", info.get("callishTestids"))
        print("conversationItems:", info.get("conversationItems"))
        print("bodyHas:", info.get("bodyHas"))
        print("shortWidgets:")
        for w in info.get("shortWidgets") or []:
            print(" -", w[:180])
        print("anrufNodes sample:")
        for n in (info.get("anrufNodes") or [])[:12]:
            if n.get("testid") or n.get("aria") or re.search(r"Eingehend|Im Gespräch|Anruf beendet", n.get("text") or ""):
                print(" -", n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
