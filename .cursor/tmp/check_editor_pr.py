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
    if not page:
        raise SystemExit("no page")
    # read tinymce in Nachricht verfassen
    text = page.evaluate(
        """() => {
          const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
          if (!section) return {err: 'no section'};
          const iframe = section.querySelector('iframe');
          if (!iframe || !iframe.contentDocument) return {err: 'no iframe'};
          const body = iframe.contentDocument.body;
          const t = (body.innerText || body.textContent || '').trim();
          return {len: t.length, start: t.slice(0, 200), hasCongstar: t.toLowerCase().includes('congstar'), hasAntwort: t.includes('[Antwort]')};
        }"""
    )
    print(text)
