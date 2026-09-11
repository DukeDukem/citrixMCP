import asyncio
import json
from playwright.async_api import async_playwright

JS = """
() => {
  const info = {
    url: location.href,
    htmlMessageCount: document.querySelectorAll('[data-testid="html-message-content"]').length,
    inboundCount: document.querySelectorAll('[data-testid="inboundChatConversationItem"]').length,
    outboundCount: document.querySelectorAll('[data-testid="outboundChatConversationItemBrandMessage"], [data-testid="outboundChatConversationItem"]').length,
    samples: [],
  };
  document.querySelectorAll('[data-testid="html-message-content"]').forEach((el, i) => {
    info.samples.push({
      i,
      innerTextLen: (el.innerText || '').length,
      textContentLen: (el.textContent || '').length,
      innerHTMLLen: (el.innerHTML || '').length,
      preview: (el.innerText || el.textContent || '').trim().slice(0, 500),
    });
  });
  const collapsed = document.querySelectorAll('[data-testid="collapsed-case-item"], .collapsed-case-item');
  info.collapsedCases = Array.from(collapsed).slice(0, 5).map(el => el.getAttribute('aria-label') || el.innerText.slice(0, 80));
  return info;
}
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        for ctx in browser.contexts:
            for page in ctx.pages:
                if "sprinklr" in page.url and "console" in page.url:
                    # scroll conversation panel
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)
                    data = await page.evaluate(JS)
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    return
        print("NO_SPRINKLR_PAGE")

asyncio.run(main())
