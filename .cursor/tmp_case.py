from playwright.sync_api import sync_playwright
p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = None
for c in b.contexts:
    for pg in c.pages:
        if "sprinklr.com" in (pg.url or "") and "console" in (pg.url or ""):
            page = pg
            break
    if page: break
info = page.evaluate("""() => {
  const text = document.body.innerText || '';
  const get = (label) => {
    const el = document.querySelector(`div[data-entityid="${label}"][aria-label="${label}"]`);
    if (!el) return null;
    const ht = el.querySelector('[data-testid="htmlText"]');
    if (ht) return (ht.innerText || '').trim();
    const sp = el.querySelector('span.spr-text-03');
    return sp ? (sp.innerText || '').trim() : null;
  };
  const fall = (text.match(/Fall\\s*#?\\s*(\\d{6,})/) || [])[1];
  return {
    imGespraech: text.includes('Im Gespräch'),
    disposition: /o2 Disposition|Disposition Codes/.test(text),
    anruf: /Eingehender Anruf|Anruf beendet/.test(text),
    htmlMsg: document.querySelectorAll('[data-testid="html-message-content"]').length,
    kundennummer: get('Kundennummer'),
    quelle: get('Quelle'),
    ziel: get('Ziel'),
    fall,
  };
}""")
print("CHANNEL_HINT", info)
p.stop()
