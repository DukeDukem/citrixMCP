"""Quick Sprinklr page snapshot for recovery."""
from playwright.sync_api import sync_playwright
import json

JS = r"""
() => {
  const t = document.body.innerText || '';
  const fall = (t.match(/Fall\s*#?\s*(\d{5,})/) || [])[1] || '';
  const header = document.querySelector('h2, [data-testid="caseNumber"]');
  return {
    url: location.href,
    fall,
    header: header ? header.innerText.slice(0, 80) : '',
    call: /Im Gespräch|Eingehender Anruf|Disposition Plan|Anruf beendet/.test(t),
    consoleList: /collapsed-case-item/.test(document.documentElement.innerHTML) || !!document.querySelector('[data-testid="collapsed-case-item"]'),
    sample: t.slice(0, 600)
  };
}
"""

with sync_playwright() as p:
    b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    pages = [pg for ctx in b.contexts for pg in ctx.pages if "sprinklr" in (pg.url or "")]
    for pg in pages:
        try:
            d = pg.evaluate(JS)
            print(json.dumps(d, ensure_ascii=False, indent=2))
        except Exception as e:
            print("ERR", pg.url, e)
