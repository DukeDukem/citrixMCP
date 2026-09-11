from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return {error: 'no section'};
  const iframe = section.querySelector('iframe');
  let iframeText = '';
  if (iframe && iframe.contentDocument) {
    iframeText = (iframe.contentDocument.body && iframe.contentDocument.body.innerText) || '';
  }
  const eds = (window.tinymce && tinymce.editors) ? Object.values(tinymce.editors) : [];
  const list = eds.map(e => {
    let inSection = false;
    try {
      const el = e.getElement && e.getElement();
      inSection = !!(el && section.contains(el));
    } catch (err) {}
    return {
      id: e.id,
      inSection,
      len: ((e.getContent({format:'text'}) || '').trim()).length,
      start: ((e.getContent({format:'text'}) || '').trim()).slice(0, 120)
    };
  });
  return {iframeLen: iframeText.trim().length, iframeStart: iframeText.trim().slice(0, 200), editors: list};
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            url = pg.url or ""
            if "sprinklr.com" in url and "console" in url:
                page = pg
                break
        if page:
            break
    if not page:
        print("NO PAGE")
        raise SystemExit(1)
    import json
    data = page.evaluate(JS)
    print(json.dumps(data, ensure_ascii=False, indent=2))
