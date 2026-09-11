import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "sprinklr-email-automation"))

from playwright.async_api import async_playwright

CASE = "57936309"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        page = None
        for ctx in browser.contexts:
            for pg in ctx.pages:
                if "sprinklr" in pg.url and "console" in pg.url:
                    page = pg
                    break
        if not page:
            print("NO_SPRINKLR_PAGE")
            return

        # Click collapsed case if present
        sel = f'[aria-label*="Fall Nr. {CASE}"], [aria-label*="#{CASE}"]'
        loc = page.locator(sel).first
        if await loc.count():
            await loc.click()
            await page.wait_for_timeout(3000)

        data = await page.evaluate(
            """() => {
              const out = { messages: [] };
              document.querySelectorAll('[data-testid="html-message-content"]').forEach((el, i) => {
                const t = (el.innerText || el.textContent || '').trim();
                if (t) out.messages.push({ i, text: t.slice(0, 10000) });
              });
              out.count = out.messages.length;
              out.caseLabel = document.querySelector('[aria-label*="57936309"]')?.getAttribute('aria-label') || '';
              return out;
            }"""
        )
        print(json.dumps(data, ensure_ascii=False, indent=2))

asyncio.run(main())
