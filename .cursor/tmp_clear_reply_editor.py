from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:9222')
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if 'sprinklr.com' in (pg.url or ''):
                page = pg
                break
        if page:
            break
    if not page:
        raise RuntimeError('No Sprinklr page found')
    page.bring_to_front()
    page.evaluate('''() => {
      if (window.tinymce && window.tinymce.editors) {
        for (const ed of window.tinymce.editors) {
          try { ed.setContent(''); } catch (e) {}
        }
      }
      const iframe = document.querySelector('section[aria-label="Nachricht verfassen"] iframe');
      if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
        iframe.contentDocument.body.innerHTML = '';
        iframe.contentDocument.body.textContent = '';
      }
    }''')
    browser.close()
