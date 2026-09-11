from playwright.sync_api import sync_playwright
p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = None
for c in b.contexts:
    for pg in c.pages:
        if "sprinklr" in (pg.url or ""):
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
print("Kundennummer", field("Kundennummer"))
print("Quelle", field("Quelle"))
print("Ziel", field("Ziel"))
text = page.evaluate("() => document.body.innerText.slice(0,12000)")
print("ImGespräch", "Im Gespräch" in text)
import re
m = re.search(r"(\d+)\s+Anhang", text)
print("Anhang", m.group(0) if m else "none")
p.stop()
