import asyncio
from playwright.async_api import async_playwright


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = None
        for context in browser.contexts:
            for pg in context.pages:
                url = (pg.url or "").lower()
                if "telefonica-germany.sprinklr.com/app/console" in url:
                    page = pg
                    break
            if page:
                break
        if page is None and browser.contexts and browser.contexts[0].pages:
            page = browser.contexts[0].pages[0]
        if page is None:
            raise RuntimeError("No browser page found")

        await page.bring_to_front()
        await page.evaluate(
            """
() => {
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of window.tinymce.editors) {
        try {
          ed.setContent('');
          ed.fire('input');
          ed.fire('change');
        } catch (e) {}
      }
    }
    const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
    if (section) {
      const iframe = section.querySelector('iframe.tox-edit-area__iframe, iframe');
      if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
        iframe.contentDocument.body.innerHTML = '';
        iframe.contentDocument.body.textContent = '';
      }
    }
  } catch (e) {}
}
"""
        )
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
