from playwright.sync_api import sync_playwright

CDP_ENDPOINT = "http://127.0.0.1:9222"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_ENDPOINT)
    pages = browser.contexts[0].pages if browser.contexts else []
    page = next((pg for pg in pages if "sprinklr" in (pg.url or "").lower()), None)
    if not page:
        raise RuntimeError("No Sprinklr tab found")

    page.wait_for_selector("section[aria-label='Nachricht verfassen']", timeout=10000)
    cleared = page.evaluate(
        """
        () => {
          if (window.tinymce && window.tinymce.editors && window.tinymce.editors.length > 0) {
            for (const ed of window.tinymce.editors) {
              try {
                ed.setContent('');
                ed.fire('input');
                ed.fire('change');
              } catch (e) {}
            }
            return true;
          }
          const ifr = document.querySelector("[data-testid='baseEditorContainer'] iframe");
          if (ifr && ifr.contentDocument) {
            const body = ifr.contentDocument.querySelector("body#tinymce") || ifr.contentDocument.body;
            if (body) {
              body.innerHTML = '';
              return true;
            }
          }
          return false;
        }
        """
    )
    print("CLEARED" if cleared else "NOT_CLEARED")
