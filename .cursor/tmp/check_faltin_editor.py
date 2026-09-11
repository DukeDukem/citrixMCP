from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if "sprinklr" in (pg.url or ""):
                page = pg
                break
        if page:
            break
    r = page.evaluate(
        """() => {
          const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
          if (!section) return {err: 'no section'};
          const iframe = section.querySelector('iframe');
          const body = iframe && iframe.contentDocument && iframe.contentDocument.body;
          const t = (body && (body.innerText || body.textContent) || '').trim();
          return {
            len: t.length,
            hasFaltin: t.includes('Faltin'),
            hasDurch: t.includes('durchgeführt'),
            hasAntwort: t.includes('[Antwort]'),
            start: t.slice(0, 120)
          };
        }"""
    )
    print(r)
