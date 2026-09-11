# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright

READ_JS = """
() => {
  const out = { tinymce: [], iframes: [], sectionText: '' };
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of window.tinymce.editors) {
        out.tinymce.push({
          id: ed.id || '',
          len: (ed.getContent({ format: 'text' }) || '').trim().length,
          preview: (ed.getContent({ format: 'text' }) || '').trim().slice(0, 80)
        });
      }
    }
  } catch (e) { out.tinymceError = String(e); }
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (section) {
    out.sectionText = (section.innerText || '').trim().slice(0, 120);
    const iframes = section.querySelectorAll('iframe');
    iframes.forEach((iframe, i) => {
      try {
        const t = (iframe.contentDocument && iframe.contentDocument.body)
          ? (iframe.contentDocument.body.innerText || '').trim()
          : '';
        out.iframes.push({ i, id: iframe.id || '', len: t.length, preview: t.slice(0, 80) });
      } catch (e) {
        out.iframes.push({ i, id: iframe.id || '', error: String(e) });
      }
    });
  }
  return out;
}
"""

CLEAR_JS = """
() => {
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of window.tinymce.editors) {
        try { ed.setContent(''); ed.fire('input'); ed.fire('change'); } catch (e) {}
      }
    }
  } catch (e) {}
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (section) {
    const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
    const iframe = base.querySelector('iframe[id$="_ifr"]') || base.querySelector('iframe')
      || section.querySelector('iframe[id$="_ifr"]') || section.querySelector('iframe');
    if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
      iframe.contentDocument.body.innerHTML = '';
      iframe.contentDocument.body.innerText = '';
    }
  }
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            url = pg.url or ""
            if "sprinklr.com" in url and "/console/" in url:
                page = pg
                break
        if page:
            break
    if not page:
        print("ERROR: no sprinklr page")
        raise SystemExit(1)
    page.bring_to_front()
    info = page.evaluate(READ_JS)
    print("DIAG:", info)
    page.evaluate(CLEAR_JS)
    after = page.evaluate(READ_JS)
    print("AFTER_CLEAR:", after)
