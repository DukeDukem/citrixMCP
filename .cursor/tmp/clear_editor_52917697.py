from playwright.sync_api import sync_playwright

CASE = "6a6d2db7fc7ca77679147d8c"
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
    target = None
    for page in browser.contexts[0].pages:
        if CASE in (page.url or ""):
            target = page
            break
    if not target:
        raise SystemExit("case tab not found")
    target.bring_to_front()
    frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    before = frame.locator("body#tinymce").inner_text(timeout=3000) if frame else ""
    print("BEFORE", len(before.strip()), "[Antwort]" in before)
    target.evaluate(CLEAR_JS)
    frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    after = frame.locator("body#tinymce").inner_text(timeout=3000) if frame else ""
    print("AFTER", len(after.strip()), repr(after[:80]))
