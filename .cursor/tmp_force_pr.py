from pathlib import Path
from playwright.sync_api import sync_playwright
import html, time

reply = Path(".cursor/skills/sprinklr-write-reply/reply_57088161.txt").read_text(encoding="utf-8").strip()
# force neutral salutation like PR script
if reply.startswith("Guten Tag Vanessa Blunk,"):
    reply = "Guten Tag,\n" + reply.split("\n", 1)[1].lstrip("\n")

paras = []
for block in reply.split("\n\n"):
    lines = [html.escape(ln) for ln in block.split("\n") if True]
    paras.append("<p>" + "<br>".join(lines) + "</p>")
content = "".join(paras)

p = sync_playwright().start()
b = p.chromium.connect_over_cdp("http://127.0.0.1:9222")
page = None
for c in b.contexts:
    for pg in c.pages:
        if "sprinklr.com" in (pg.url or "") and "console" in (pg.url or ""):
            page = pg
            try:
                page.bring_to_front()
            except Exception:
                pass
            break
    if page:
        break

# click Nachricht verfassen / iframe
page.evaluate("""() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return;
  try { section.scrollIntoView({block:'center'}); } catch(e) {}
  const tox = section.querySelector('.tox-tinymce');
  if (tox && tox.style) tox.style.visibility = 'visible';
  const iframe = section.querySelector('iframe');
  if (iframe) try { iframe.click(); } catch(e) {}
}""")
time.sleep(0.5)

result = page.evaluate("""(content) => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return {ok:false, err:'no section'};
  const base = section.querySelector('[data-testid="baseEditorContainer"]') || section;
  const iframe = base.querySelector('iframe[id$="_ifr"]') || base.querySelector('iframe');
  if (!iframe) return {ok:false, err:'no iframe'};
  const id = (iframe.id || '').replace(/_ifr$/, '');
  let editor = null;
  try {
    if (window.tinymce) {
      editor = window.tinymce.get(id) || (window.tinymce.editors || []).find(e => e && e.id === id) || null;
      if (!editor && window.tinymce.editors) {
        for (const ed of window.tinymce.editors) {
          try {
            const el = ed.getElement && ed.getElement();
            if (el && section.contains(el)) { editor = ed; break; }
          } catch(e) {}
        }
      }
    }
  } catch(e) { return {ok:false, err:String(e)}; }
  if (!editor) {
    // fallback: write into iframe body
    const doc = iframe.contentDocument;
    if (!doc) return {ok:false, err:'no doc'};
    doc.body.innerHTML = content;
    return {ok:true, method:'iframe', len:(doc.body.innerText||'').trim().length, probe:(doc.body.innerText||'').trim().slice(0,80)};
  }
  try {
    editor.focus();
    editor.setContent('');
    editor.setContent(content);
    editor.fire('input');
    editor.fire('change');
    const text = (editor.getContent({format:'text'}) || '').trim();
    if (!text || text.includes('[Antwort]') || text.length < 100) return {ok:false, err:'did not stick', len:text.length, probe:text.slice(0,80)};
    return {ok:true, method:'tinymce', id:editor.id, len:text.length, probe:text.slice(0,80)};
  } catch(e) { return {ok:false, err:String(e)}; }
}""", content)
print("WRITE", result)
time.sleep(1.0)
text = page.evaluate("""() => {
  const section = document.querySelector('section[aria-label="Nachricht verfassen"]');
  if (!section) return 'NO_SECTION';
  const iframe = section.querySelector('iframe');
  if (iframe && iframe.contentDocument) return (iframe.contentDocument.body.innerText || '').trim();
  return 'NO_IFRAME';
}""")
print("LEN", len(text))
print("---OK---", "12,99" in text and "Quittung" in text and "[Antwort]" not in text)
print(text[:300])
# keep page; stop playwright connection carefully
p.stop()
