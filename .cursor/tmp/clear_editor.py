import asyncio
from playwright.async_api import async_playwright

CLEAR_JS = """() => {
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of window.tinymce.editors) {
        try { ed.setContent(''); ed.fire('change'); } catch (e) {}
      }
    }
  } catch (e) {}
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (section) {
    const iframe = section.querySelector('iframe[id$="_ifr"]') || section.querySelector('iframe');
    if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
      iframe.contentDocument.body.innerHTML = '';
      iframe.contentDocument.body.innerText = '';
    }
  }
}"""

READ_JS = """() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  const iframe = section && (section.querySelector('iframe[id$="_ifr"]') || section.querySelector('iframe'));
  if (!iframe || !iframe.contentDocument) return 'NO_IFRAME';
  return (iframe.contentDocument.body.innerText || '').trim();
}"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                u = pg.url or ""
                if "sprinklr.com" in u and "console" in u:
                    page = pg
                    break
            if page:
                break
        if not page:
            print("NO_PAGE")
            return
        await page.evaluate(CLEAR_JS)
        text = await page.evaluate(READ_JS)
        print("CLEARED_LEN", len(text), "PROBE", repr(text[:40]))

asyncio.run(main())
