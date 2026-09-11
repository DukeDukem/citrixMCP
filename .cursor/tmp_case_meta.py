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

info = {
  "Fall": page.evaluate("""() => {
    const t = document.body.innerText || '';
    const m = t.match(/Fall\\s*#?\\s*(\\d{6,})/i);
    return m ? m[1] : '';
  }"""),
  "Kundennummer": field("Kundennummer"),
  "Quelle": field("Quelle"),
  "Ziel": field("Ziel"),
  "ImGespräch": "Im Gespräch" in (page.inner_text("body")[:5000] if False else page.evaluate("() => document.body.innerText.slice(0,8000)")),
  "Anhang": page.evaluate("""() => {
    const t = document.body.innerText || '';
    const m = t.match(/(\\d+)\\s+Anhang/);
    return m ? m[0] : (t.includes('Anhänge') ? 'Anhänge' : 'none');
  }"""),
}
# also search Quelle/Ziel loosely
text = page.evaluate("() => document.body.innerText")
for key in ["Quelle", "Ziel", "Care Widerruf", "CBC_", "CARE_ALLGEMEIN"]:
    if key.lower() in text.lower():
        pass
# extract Quelle/Ziel lines
import re
for label in ["Quelle", "Ziel"]:
    m = re.search(rf"{label}\\s*\\n\\s*([^\\n]+)", text)
    if m:
        info[label+"_loose"] = m.group(1).strip()[:120]
print(info)
# newest inbound snippet already have
p.stop()
