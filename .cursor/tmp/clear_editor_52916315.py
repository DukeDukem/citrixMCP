from playwright.sync_api import sync_playwright

CASE = "6a6d09826156a1e66da37e2d"
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
        print("TAB", page.url)
        if CASE in (page.url or ""):
            target = page
    if not target:
        for page in browser.contexts[0].pages:
            if "sprinklr.com/app/console" in (page.url or ""):
                target = page
                break
    if not target:
        raise SystemExit("no sprinklr tab")
    print("Clearing", target.url)
    target.bring_to_front()
    target.evaluate(CLEAR_JS)
    text = ""
    try:
        frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
        if frame:
            text = frame.locator("body#tinymce").inner_text(timeout=3000)
    except Exception as e:
        print("warn", e)
    print("after clear len", len((text or "").strip()), "antwort", "[Antwort]" in (text or ""))
