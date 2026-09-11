import asyncio
from playwright.async_api import async_playwright

JS = """
() => {
  const out = { url: location.href, caseId: '', subject: '', from: '', messages: [] };
  const caseEl = document.querySelector('[data-testid="caseId"], [data-entityid="CASE_ID"]');
  if (caseEl) out.caseId = (caseEl.innerText || '').trim();
  const nodes = document.querySelectorAll('[data-testid="html-message-content"], [data-element-type="email-message-container"]');
  nodes.forEach((n, i) => {
    const t = (n.innerText || n.textContent || '').trim();
    if (t) out.messages.push({ i, len: t.length, text: t.slice(0, 8000) });
  });
  const sidebar = document.querySelector('div[data-entityid="Kundennummer"][aria-label="Kundennummer"]');
  if (sidebar) out.kundennummer = (sidebar.innerText || '').trim();
  return out;
}
"""

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        for ctx in browser.contexts:
            for page in ctx.pages:
                if "sprinklr" in page.url and "console" in page.url:
                    data = await page.evaluate(JS)
                    import json
                    print(json.dumps(data, ensure_ascii=False, indent=2))
                    return
        print("NO_SPRINKLR_PAGE")

asyncio.run(main())
