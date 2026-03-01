"""Convert knowledgebase7.docx with corrupt-image skipping."""
import os
import zipfile
import re
from pathlib import Path
from io import BytesIO
import docx
from PIL import Image

DOWNLOADS = Path(os.environ["USERPROFILE"]) / "Downloads"
KB_DIR = Path(__file__).parent.parent / "KnowledgeBase"
IMG_DIR = KB_DIR / "images"

doc_path = DOWNLOADS / "knowledgebase7.docx"
sl = "knowledgebase7"
img_out_dir = IMG_DIR / sl
img_out_dir.mkdir(parents=True, exist_ok=True)

print("Extracting images (skipping corrupt)...")
saved = []
try:
    with zipfile.ZipFile(str(doc_path), "r") as z:
        media = [n for n in z.namelist() if n.startswith("word/media/")]
        print(f"  Found {len(media)} media files")
        for i, mf in enumerate(media, 1):
            try:
                raw = z.read(mf)
                img = Image.open(BytesIO(raw))
                fname = f"img_{i:03d}.png"
                img.save(str(img_out_dir / fname), "PNG")
                saved.append((Path(mf).name, f"images/{sl}/{fname}"))
                if i % 50 == 0:
                    print(f"  ... {i}/{len(media)} images done")
            except Exception as e:
                print(f"  SKIP {mf}: {e}")
except Exception as e:
    print(f"ZIP error: {e}")

print(f"  Saved {len(saved)} images")

print("Parsing document text...")
doc = docx.Document(str(doc_path))

lines = ["# Knowledgebase7\n", "> Source: knowledgebase7.docx\n"]

if saved:
    lines.append("\n---\n")
    lines.append("## Embedded Images\n")
    for orig, rel in saved:
        lines.append(f"\n![{orig}]({rel})\n")
    lines.append("\n---\n")

for child in doc.element.body:
    tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
    if tag == "p":
        para = docx.text.paragraph.Paragraph(child, doc)
        text = para.text.strip()
        if not text:
            continue
        style = para.style.name if para.style else ""
        if re.match(r"Heading\s+\d", style):
            lvl = int(re.search(r"\d", style).group())
            lines.append(f"\n{'#' * (lvl + 1)} {text}\n")
        else:
            lines.append(f"{text}\n")
    elif tag == "tbl":
        tbl = docx.table.Table(child, doc)
        rows = [[c.text.replace("\n", " ").strip() for c in r.cells] for r in tbl.rows]
        if rows:
            w = max(len(r) for r in rows)
            rows = [r + [""] * (w - len(r)) for r in rows]
            md_rows = ["| " + " | ".join(rows[0]) + " |"]
            md_rows.append("| " + " | ".join(["---"] * w) + " |")
            for r in rows[1:]:
                md_rows.append("| " + " | ".join(r) + " |")
            lines.append("\n" + "\n".join(md_rows) + "\n")

md = "\n".join(lines)
out = KB_DIR / "knowledgebase7.md"
out.write_text(md, encoding="utf-8")
print(f"Written {out.name}  ({len(md):,} chars)")
