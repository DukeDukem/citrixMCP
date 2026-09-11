"""One-shot CDP extract of visible Sprinklr case text."""
from __future__ import annotations

import json
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const out = {};
  const kn = document.querySelector('div[data-entityid="Kundennummer"][aria-label="Kundennummer"]');
  out.kundennummer = kn ? kn.innerText.slice(0, 120) : '';
  const ziel = document.querySelector('div[data-entityid="Ziel"]');
  out.ziel = ziel ? ziel.innerText.slice(0, 200) : '';
  const quelle = document.querySelector('div[data-entityid="Quelle"]');
  out.quelle = quelle ? quelle.innerText.slice(0, 200) : '';
  const fall = document.querySelector('div[data-entityid="Fallnummer"]');
  out.fallnummer = fall ? fall.innerText.slice(0, 120) : '';
  out.bodies = [...document.querySelectorAll('[data-testid="html-message-content"]')]
    .map(el => (el.innerText || '').trim().slice(0, 5000))
    .filter(Boolean)
    .slice(0, 8);
  const allText = document.body.innerText || '';
  const m = allText.match(/Fall\s*#?\d{5,}/);
  out.fallMatch = m ? m[0] : '';
  const idx = allText.indexOf('Kundennummer');
  out.aroundKN = idx >= 0 ? allText.slice(Math.max(0, idx - 80), idx + 500) : '';
  const idx2 = allText.search(/Betreff|Subject/i);
  out.aroundBetreff = idx2 >= 0 ? allText.slice(Math.max(0, idx2 - 40), idx2 + 600) : '';
  const idx3 = allText.search(/\bVon\b|From:/i);
  out.aroundFrom = idx3 >= 0 ? allText.slice(idx3, idx3 + 500) : '';
  // Care webform style fields often appear as label:value
  for (const key of ['Name', 'Vorname', 'Nachname', 'Geburtsdatum', 'Rufnummer', 'E-Mail', 'Email', 'Adresse', 'Vertragsnummer', 'MSISDN']) {
    const re = new RegExp(key + '\\s*[:\\n]\\s*([^\\n]{1,120})', 'i');
    const mm = allText.match(re);
    if (mm) out['field_' + key] = mm[1].trim();
  }
  out.textLen = allText.length;
  out.textSample = allText.slice(0, 8000);
  return out;
}
"""


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "sprinklr" in (pg.url or ""):
                    # prefer console with case open
                    if "/console/" in (pg.url or ""):
                        page = pg
                        break
                    if page is None:
                        page = pg
            if page and "/console/" in (page.url or ""):
                break
        if not page:
            print("NO_SPRINKLR_PAGE")
            raise SystemExit(1)
        print("URL:", page.url)
        data = page.evaluate(JS)
        print(json.dumps(data, ensure_ascii=False, indent=2)[:20000])


if __name__ == "__main__":
    main()
