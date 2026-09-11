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
print({"Fall": field("Fall") or "?", "Kundennummer": field("Kundennummer"), "Quelle": field("Quelle"), "Ziel": field("Ziel"),
 "ImGespräch": "Im Gespräch" in page.evaluate("() => document.body.innerText.slice(0,5000)"),
 "Anhang": page.evaluate("() => { const t=document.body.innerText||''; const m=t.match(/(\\d+)\\s+Anhang/); return m and m[0] or 'none'; }")})
# dump thread briefly via page text for inbound count
p.stop()
