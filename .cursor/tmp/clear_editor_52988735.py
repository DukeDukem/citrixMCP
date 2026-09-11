from playwright.sync_api import sync_playwright

JS_CLEAR = r"""
() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return {ok: false, err: 'no section'};
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of Object.values(tinymce.editors)) {
        try { ed.setContent(''); ed.fire('input'); ed.fire('change'); } catch (e) {}
      }
    }
  } catch (e) {}
  const iframe = section.querySelector('iframe');
  if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
    iframe.contentDocument.body.innerHTML = '';
    iframe.contentDocument.body.innerText = '';
  }
  return {ok: true};
}
"""

JS_READ = r"""
() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return {len: 0, start: ''};
  const iframe = section.querySelector('iframe');
  let t = '';
  if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
    t = (iframe.contentDocument.body.innerText || '').trim();
  }
  return {len: t.length, start: t.slice(0, 80)};
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            url = pg.url or ""
            if "sprinklr.com" in url and "console" in url:
                page = pg
                break
        if page:
            break
    if not page:
        print("NO_PAGE")
        raise SystemExit(1)
    print("clear", page.evaluate(JS_CLEAR))
    print("after", page.evaluate(JS_READ))
