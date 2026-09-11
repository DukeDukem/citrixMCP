from playwright.sync_api import sync_playwright

CLEAR_JS = """
() => {
  try {
    if (window.tinymce && window.tinymce.editors) {
      for (const ed of window.tinymce.editors) {
        try { ed.setContent(''); ed.fire('input'); ed.fire('change'); } catch (e) {}
      }
    }
  } catch (e) {}
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (section) {
    const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
    const iframe = base.querySelector('iframe[id$="_ifr"]') || base.querySelector('iframe');
    if (iframe && iframe.contentDocument && iframe.contentDocument.body) {
      iframe.contentDocument.body.innerHTML = '';
      iframe.contentDocument.body.innerText = '';
    }
  }
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
    page = None
    for pg in browser.contexts[0].pages:
        if "sprinklr" in (pg.url or "").lower():
            page = pg
            break
    if not page:
        print("NO_SPRINKLR")
        raise SystemExit(1)
    page.bring_to_front()
    page.evaluate(CLEAR_JS)
    text = ""
    try:
        frame = page.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
        if frame:
            text = frame.locator("body#tinymce").inner_text(timeout=3000)
    except Exception as e:
        print("read_err", e)
    print("CLEARED len=", len((text or "").strip()))
