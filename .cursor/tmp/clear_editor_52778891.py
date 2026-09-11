from playwright.sync_api import sync_playwright

CASE_HINT = "6a6b706d6156a1e66dc45ee2"
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
        if CASE_HINT in (page.url or ""):
            target = page
            break
    if not target:
        print("ERROR: case tab not found")
        raise SystemExit(1)
    print("Clearing:", target.url)
    target.bring_to_front()
    target.evaluate(CLEAR_JS)
    frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
    text = ""
    try:
        if frame:
            text = frame.locator("body#tinymce").inner_text(timeout=3000)
    except Exception as e:
        print("readback warn:", e)
    print("len after clear:", len((text or "").strip()), "has [Antwort]:", "[Antwort]" in (text or ""))
    print("OK" if not (text or "").strip() else "NOT EMPTY")
