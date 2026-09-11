from playwright.sync_api import sync_playwright

p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = None
for c in b.contexts:
    for pg in c.pages:
        if "sprinklr.com" in (pg.url or "") and "console" in (pg.url or ""):
            page = pg
            break
    if page:
        break
text = page.evaluate(
    """() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  const root = section || document;
  const iframe = root.querySelector('iframe.tox-edit-area__iframe') || root.querySelector('[data-testid="baseEditorContainer"] iframe') || root.querySelector('iframe');
  if (iframe && iframe.contentDocument) return (iframe.contentDocument.body.innerText || '').trim();
  return 'NO_IFRAME';
}"""
)
ok = (
    "REAL Solution" in text
    and "26/1218209-X" in text
    and "155 am Ende" in text
    and "[Antwort]" not in text
)
print("LEN", len(text))
print("---OK---", ok)
print(text[:300])
p.stop()
