from playwright.sync_api import sync_playwright
import json
import urllib.request

ws = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version"))[
    "webSocketDebuggerUrl"
]
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws)
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            u = pg.url or ""
            if "sprinklr" in u.lower() and "/console/" in u:
                page = pg
                break
        if page:
            break
    text = page.evaluate(
        """() => {
      const ifr = document.querySelector('[data-testid=\"baseEditorContainer\"] iframe')
        || document.querySelector('iframe.tox-edit-area__iframe');
      if (ifr && ifr.contentDocument) return ifr.contentDocument.body.innerText || '';
      return '';
    }"""
    )
    print("LEN", len(text))
    print("ANTWORT", "[Antwort]" in text)
    print("DATENSCHUTZ", "Datenschutz" in text)
    print("PII_MAREIKE", "Mareike" in text or "Heyde" in text)
    print("FIRST", text.splitlines()[0] if text else "")
