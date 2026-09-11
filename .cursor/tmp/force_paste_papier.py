from pathlib import Path
from playwright.sync_api import sync_playwright
import json
import re

reply = Path("temp_reply.txt").read_text(encoding="utf-8-sig").strip()
# Match what write-reply does: force neutral salutation if needed
if reply.startswith("Guten Tag ") and "," in reply.split("\n", 1)[0]:
    first, rest = reply.split("\n", 1)
    reply = "Guten Tag,\n" + rest.lstrip("\n")

# Build simple HTML paragraphs
paras = []
for block in re.split(r"\n\s*\n", reply):
    lines = [l.strip() for l in block.split("\n") if l.strip() or True]
    # keep line breaks as <br>
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
        """({ html, plain }) => {
          const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
          if (!section) return { ok: false, err: 'no section' };
          const iframe = section.querySelector('iframe');
          if (!iframe || !iframe.contentDocument) return { ok: false, err: 'no iframe' };
          const doc = iframe.contentDocument;
          const body = doc.body;
          // clear
          body.innerHTML = '';
          body.focus();
          body.innerHTML = html;
          // fire input events
          body.dispatchEvent(new Event('input', { bubbles: true }));
          body.dispatchEvent(new Event('change', { bubbles: true }));
          const t = (body.innerText || '').trim();
          return {
            ok: true,
            len: t.length,
            hasPapier: t.includes('Papierrechnung'),
            hasAntwort: t.includes('[Antwort]'),
            start: t.slice(0, 100)
          };
        }""",
        {"html": html_body, "plain": reply},
    )
    print(json.dumps(result, ensure_ascii=False))
    if not result.get("ok") or result.get("hasAntwort") or not result.get("hasPapier"):
        raise SystemExit("force write failed")
