"""Clear Sprinklr reply editor after failed PR verification."""
from playwright.sync_api import sync_playwright

CASE_HINT = "6a70d428fc7ca77679553cd0"
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


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        pages = list(browser.contexts[0].pages) if browser.contexts else []
        target = None
        for page in pages:
            url = page.url or ""
            if CASE_HINT in url:
                target = page
                break
        if not target:
            for page in pages:
                if "sprinklr.com/app/console" in (page.url or ""):
                    target = page
                    break
        if not target:
            print("ERROR: no Sprinklr console page found")
            return 1
        print("Clearing editor on:", target.url)
        target.bring_to_front()
        target.evaluate(CLEAR_JS)
        text = ""
        try:
            frame = target.locator("[data-testid='baseEditorContainer'] iframe").first.content_frame
            if frame:
                text = frame.locator("body#tinymce").inner_text(timeout=3000)
        except Exception as e:
            print("readback warn:", e)
        cleaned = (text or "").strip()
        print("Editor text after clear len=", len(cleaned), "repr=", repr(cleaned[:80]))
        if cleaned:
            print("WARNING: editor not fully empty")
            return 1
        print("OK: editor empty")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
