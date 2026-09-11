from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import re

reply = Path("temp_reply.txt").read_text(encoding="utf-8-sig").strip()
# Neutral salutation to match write-reply behavior
if reply.startswith("Guten Tag ") and "," in reply.split("\n", 1)[0]:
    reply = "Guten Tag,\n" + reply.split("\n", 1)[1].lstrip("\n")

paras = []
for block in re.split(r"\n\s*\n", reply):
    html = "<br>".join(block.split("\n"))
    paras.append(f"<p>{html}</p>")
html_body = "".join(paras)

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
        raise SystemExit("no sprinklr page")

    result = page.evaluate(
        """(html) => {
          const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
          if (!section) return { ok: false, err: 'no section' };
          const iframe = section.querySelector('iframe');
          if (!iframe || !iframe.contentDocument) return { ok: false, err: 'no iframe' };
          const body = iframe.contentDocument.body;
          body.innerHTML = '';
          body.focus();
          body.innerHTML = html;
          body.dispatchEvent(new Event('input', { bubbles: true }));
          body.dispatchEvent(new Event('change', { bubbles: true }));
          const t = (body.innerText || '').trim();
          return {
            ok: true,
            len: t.length,
            hasFaltin: t.includes('Faltin'),
            hasDurch: t.includes('durchgeführt'),
            hasAntwort: t.includes('[Antwort]')
          };
        }""",
        html_body,
    )
    print(json.dumps(result, ensure_ascii=False))
    if not result.get("ok") or result.get("hasAntwort") or not result.get("hasFaltin"):
        raise SystemExit("force write failed")
