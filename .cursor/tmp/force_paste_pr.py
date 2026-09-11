import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

reply = Path("temp_reply.txt").read_text(encoding="utf-8").strip()


def to_html(text: str) -> str:
    parts = []
    for para in text.split("\n\n"):
        lines = "<br>".join(p.strip() for p in para.split("\n"))
        parts.append(f"<p>{lines}</p>")
    return "".join(parts)


html = to_html(reply)


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        pages = []
        for ctx in browser.contexts:
            pages.extend(ctx.pages)
        page = None
        for pg in pages:
            if "sprinklr.com" not in (pg.url or ""):
                continue
            try:
                st = await pg.evaluate(
                    """() => ({
                  hasEditor: !!document.querySelector('[data-testid="baseEditorContainer"]'),
                  hasSection: !!document.querySelector('section[aria-label="Nachricht verfassen"]'),
                  hasMsg: !!document.querySelector('[data-testid="html-message-content"]')
                })"""
                )
                if st.get("hasEditor") or st.get("hasSection") or st.get("hasMsg"):
                    page = pg
                    if st.get("hasEditor") or st.get("hasSection"):
                        break
            except Exception:
                pass
        if not page:
            raise SystemExit("no sprinklr page")
        await page.bring_to_front()
        await page.wait_for_timeout(300)

        before = await page.evaluate(
            """() => {
          try {
            if (window.tinymce && window.tinymce.activeEditor) {
              const t = window.tinymce.activeEditor.getContent({format:'text'}) || '';
              return {
                len:t.length,
                stub:t.includes('[Antwort]'),
                hasDritte:t.includes('Dritte'),
                hasIBAN:t.includes('IBAN'),
                hasName:t.includes('Christian') || t.includes('Schramm')
              };
            }
          } catch(e) {}
          return {err:'no tinymce'};
        }"""
        )
        print("BEFORE", before)

        result = await page.evaluate(
            """(html) => {
          function ok(t) {
            return {
              len:(t||'').length,
              hasDritte:(t||'').includes('Dritte'),
              hasIBAN:(t||'').includes('IBAN'),
              hasStub:(t||'').includes('[Antwort]'),
              hasName:(t||'').includes('Christian') || (t||'').includes('Schramm'),
              hasSurvey:(t||'').includes('Zur Verbesserung'),
              hasSig:(t||'').includes('Freundliche')
            };
          }
          if (window.tinymce) {
            const eds=[];
            if (window.tinymce.editors) {
              for (const k of Object.keys(window.tinymce.editors)) eds.push(window.tinymce.editors[k]);
            }
            const ed=window.tinymce.activeEditor || eds.find(e=>e) || null;
            if (ed) {
              ed.focus();
              ed.setContent(html);
              ed.fire('change');
              ed.fire('input');
              return {via:'tinymce', ok:true, ...ok(ed.getContent({format:'text'})||'')};
            }
          }
          return {ok:false, err:'no editor'};
        }""",
            html,
        )
        print("AFTER", result)
        if (
            not result.get("ok")
            or result.get("hasStub")
            or result.get("hasName")
            or not result.get("hasDritte")
            or not result.get("hasIBAN")
            or result.get("len", 0) < 1800
        ):
            raise SystemExit("FORCE PASTE FAILED")


asyncio.run(main())
