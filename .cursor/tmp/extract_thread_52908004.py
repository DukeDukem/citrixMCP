import asyncio
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
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
            print("NO PAGE")
            return

        print("URL", page.url)
        texts = await page.evaluate(
            """() => {
              const sels = [
                '[data-testid="html-message-content"]',
                '[data-testid="message-content"]',
                '[class*="MessageContent"]',
              ];
              const out = [];
              for (const sel of sels) {
                for (const n of document.querySelectorAll(sel)) {
                  const t = (n.innerText || '').trim();
                  if (t && t.length > 40) out.push(t.slice(0, 4000));
                }
              }
              return out.slice(0, 15);
            }"""
        )
        for i, t in enumerate(texts):
            print(f"===== BLOCK {i} len={len(t)} =====")
            print(t)
            print()


asyncio.run(main())
