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
text = page.evaluate("""() => {
  const iframe = document.querySelector('iframe.tox-edit-area__iframe') || document.querySelector('[data-testid="baseEditorContainer"] iframe');
  if (iframe && iframe.contentDocument) return (iframe.contentDocument.body.innerText || '').trim();
  return 'NO_IFRAME';
}""")
ok = "12,99" in text and "Quittung" in text and "Guten Tag" in text and text.count("Freundliche") >= 1 and "[Antwort]" not in text
print("LEN", len(text), "OK", ok)
print(text[200:500] if len(text)>200 else text)
p.stop()
