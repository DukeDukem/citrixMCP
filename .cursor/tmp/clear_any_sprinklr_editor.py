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
    pages = list(browser.contexts[0].pages) if browser.contexts else []
    for i, page in enumerate(pages):
        print(i, page.url)
    target = None
    for page in pages:
        if "sprinklr.com/app/console" in (page.url or ""):
            target = page
    if not target:
        print("No Sprinklr console tab")
        raise SystemExit(1)
    print("Clearing", target.url)
    target.bring_to_front()
    # read before
    text_before = ""
    try:
        frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
        if frame:
            text_before = frame.locator("body#tinymce").inner_text(timeout=3000)
    except Exception as e:
        print("before warn", e)
    print("BEFORE len", len((text_before or "").strip()), "antwort", "[Antwort]" in (text_before or ""))
    target.evaluate(CLEAR_JS)
    text = ""
    try:
        frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
        if frame:
            text = frame.locator("body#tinymce").inner_text(timeout=3000)
    except Exception as e:
        print("after warn", e)
    print("AFTER len", len((text or "").strip()))
