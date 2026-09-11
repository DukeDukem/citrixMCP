from playwright.sync_api import sync_playwright
import re
p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = None
for c in b.contexts:
    for pg in c.pages:
        if "sprinklr.com" in (pg.url or "") and "login" not in (pg.url or ""):
            page = pg
            break
    if page: break

def field(label):
    return page.evaluate("""(label) => {
      const el = document.querySelector(`div[data-entityid="${label}"][aria-label="${label}"]`);
      if (!el) return null;
      const ht = el.querySelector('[data-testid="htmlText"]');
      if (ht) return (ht.innerText || '').trim();
      const sp = el.querySelector('span.spr-text-03');
      return sp ? (sp.innerText || '').trim() : (el.innerText || '').trim();
    }""", label)
text = page.evaluate("() => document.body.innerText.slice(0,5000)")
m = re.search(r"(\d+)\s+Anhang", text)
print({"Kundennummer": field("Kundennummer"), "Quelle": field("Quelle"), "Ziel": field("Ziel"), "Anhang": m.group(0) if m else "none", "ImGespräch": "Im Gespräch" in text})
p.stop()
