"""
Converts knowledgebase*.docx files from Downloads into a queryable
KnowledgeBase folder in the CitrixMCP project.

For each docx it produces:
  KnowledgeBase/<slug>.md        - full text as markdown
  KnowledgeBase/images/<slug>/   - extracted embedded images (PNG)

Also writes:
  KnowledgeBase/INDEX.md         - table of contents + section summaries
  KnowledgeBase/SEARCH_HINT.md  - instructions Cursor uses to query the KB
"""

import os
import re
import sys
import traceback
import zipfile
import shutil
from pathlib import Path
from io import BytesIO

try:
    import docx
    from PIL import Image
except ImportError:
    print("ERROR: Run  python -m pip install python-docx Pillow  first.")
    sys.exit(1)

# ── paths ────────────────────────────────────────────────────────────────────
DOWNLOADS = Path(os.environ["USERPROFILE"]) / "Downloads"
PROJECT   = Path(__file__).parent.parent
KB_DIR    = PROJECT / "KnowledgeBase"
IMG_DIR   = KB_DIR / "images"

DOCX_FILES = sorted(DOWNLOADS.glob("knowledgebase*.docx"))

if not DOCX_FILES:
    print("No knowledgebase*.docx files found in", DOWNLOADS)
    sys.exit(1)

print(f"Found {len(DOCX_FILES)} docx files:")
for f in DOCX_FILES:
    print("  ", f.name)

# ── helpers ──────────────────────────────────────────────────────────────────

def slug(path: Path) -> str:
    name = path.stem
    name = re.sub(r"\s*\(\d+\)\s*", "", name)
    return name.strip().replace(" ", "_")


def extract_images_from_docx(doc_path: Path, out_dir: Path) -> list[tuple[str, str]]:
    """
    A .docx is a ZIP file. We extract images from word/media/ directly.
    Returns list of (original_name, saved_path_relative_to_KB_DIR).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    with zipfile.ZipFile(str(doc_path), "r") as z:
        media_files = [n for n in z.namelist() if n.startswith("word/media/")]
        for i, mf in enumerate(media_files, 1):
            ext = Path(mf).suffix.lower()
            # Convert all to PNG for consistency
            raw = z.read(mf)
            try:
                img = Image.open(BytesIO(raw))
                fname = f"img_{i:03d}.png"
                out_path = out_dir / fname
                img.save(str(out_path), "PNG")
                rel = f"images/{out_dir.name}/{fname}"
                saved.append((Path(mf).name, rel))
                print(f"    image: {Path(mf).name} -> {fname}")
            except Exception as e:
                print(f"    WARN: could not convert {mf}: {e}")
    return saved


def table_to_md(tbl) -> str:
    rows = []
    for row in tbl.rows:
        cells = [c.text.replace("\n", " ").strip() for c in row.cells]
        rows.append(cells)
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    padded = [r + [""] * (width - len(r)) for r in rows]
    lines = []
    lines.append("| " + " | ".join(padded[0]) + " |")
    lines.append("| " + " | ".join(["---"] * width) + " |")
    for row in padded[1:]:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def convert_docx(doc_path: Path) -> tuple[str, int]:
    """Returns (markdown_text, image_count)."""
    sl = slug(doc_path)
    img_out_dir = IMG_DIR / sl

    print(f"  Extracting images...")
    saved_images = extract_images_from_docx(doc_path, img_out_dir)
    img_count = len(saved_images)

    print(f"  Parsing document text...")
    doc = docx.Document(str(doc_path))

    lines = [f"# {sl.replace('_', ' ').title()}\n"]
    lines.append(f"> Source: `{doc_path.name}`\n")

    # We'll insert image references after the document - since matching
    # inline images to paragraphs is complex, list them at end in an appendix
    if saved_images:
        lines.append("\n---\n")
        lines.append("## Embedded Images\n")
        for orig_name, rel_path in saved_images:
            lines.append(f"\n![{orig_name}]({rel_path})\n")
        lines.append("\n---\n")

    # Now extract all text: paragraphs + tables in document order
    body = doc.element.body
    for child in body:
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag

        if tag == "p":
            para = docx.text.paragraph.Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                continue
            style = para.style.name if para.style else ""
            if re.match(r"Heading\s+\d", style):
                level = int(re.search(r"\d", style).group())
                prefix = "#" * (level + 1)
                lines.append(f"\n{prefix} {text}\n")
            else:
                # Bold paragraphs often act as sub-headers
                all_bold = all(run.bold for run in para.runs if run.text.strip())
                if all_bold and len(text) < 120:
                    lines.append(f"\n**{text}**\n")
                else:
                    lines.append(f"{text}\n")

        elif tag == "tbl":
            tbl = docx.table.Table(child, doc)
            md_table = table_to_md(tbl)
            if md_table:
                lines.append(f"\n{md_table}\n")

    return "\n".join(lines), img_count


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    KB_DIR.mkdir(parents=True, exist_ok=True)
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    index_entries = []

    for doc_path in DOCX_FILES:
        sl = slug(doc_path)
        print(f"\n=== Converting {doc_path.name} -> {sl}.md ===")
        try:
            md_text, img_count = convert_docx(doc_path)
        except Exception as e:
            print(f"  ERROR: {e}")
            traceback.print_exc()
            continue

        out_path = KB_DIR / f"{sl}.md"
        out_path.write_text(md_text, encoding="utf-8")
        print(f"  Written: {out_path.name}  ({len(md_text):,} chars, {img_count} images)")

        # first substantive paragraph for index preview
        preview_lines = [
            l.strip() for l in md_text.splitlines()
            if l.strip()
            and not l.startswith("#")
            and not l.startswith(">")
            and not l.startswith("|")
            and not l.startswith("!")
            and not l.startswith("---")
            and not l.startswith("**")
        ]
        preview = preview_lines[0][:200] if preview_lines else "(no preview)"

        index_entries.append({
            "slug": sl,
            "source": doc_path.name,
            "chars": len(md_text),
            "images": img_count,
            "preview": preview,
        })

    # ── INDEX.md ─────────────────────────────────────────────────────────────
    print("\nWriting INDEX.md...")
    index_lines = [
        "# KnowledgeBase Index\n",
        "Searchable knowledge base for O2/Telefonica customer support (Backoffice E-Mail team).",
        "Source documents were Word files converted to Markdown.\n",
        "## Documents\n",
        "| File | Source | Chars | Images | Preview |",
        "| --- | --- | --- | --- | --- |",
    ]
    for e in index_entries:
        prev = e["preview"].replace("|", "/")[:80]
        index_lines.append(
            f"| [{e['slug']}.md]({e['slug']}.md) | `{e['source']}` | {e['chars']:,} | {e['images']} | {prev}... |"
        )

    index_lines += [
        "\n## How to Query\n",
        "- Read **SEARCH_HINT.md** for Cursor agent query instructions.",
        "- Grep across `KnowledgeBase/*.md` for any keyword.",
        "- Open individual `.md` files for full document content.",
        "- Images are in `KnowledgeBase/images/<doc>/`.\n",
    ]

    (KB_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")

    # ── SEARCH_HINT.md ────────────────────────────────────────────────────────
    print("Writing SEARCH_HINT.md...")
    doc_list = "\n".join(f"  {e['slug']}.md" for e in index_entries)
    search_hint = f"""\
# KnowledgeBase Search Instructions

This file explains how Cursor should query the O2/Telefonica knowledge base.

## Purpose

You are an AI advisor for the O2/Telefonica Backoffice E-Mail customer support team.
This knowledge base contains:
- Handling procedures for customer requests (Tarif, Vertrag, Rechnung, SIM, eSIM, Geraet)
- Ticket IDs and workflows for SalCus, Marquez, Viagint
- Transfer Matrix (Sabio Transfermatrix) for routing to other divisions
- Authentication rules and verification steps
- Response templates and escalation paths

## Files in this Knowledge Base

```
KnowledgeBase/
  INDEX.md
  SEARCH_HINT.md
{doc_list}
  images/           <- extracted images and diagrams
```

## Query Strategy for Cursor Agent

### Step 1 - Identify relevant document
Read `KnowledgeBase/INDEX.md` to see previews of each document.

### Step 2 - Keyword search
Use Grep with path="KnowledgeBase/" to find relevant sections:
- Ticket/program search: "SalCus", "Marquez", "Viagint", "Ticket"
- Topic search: "Tarif", "Kuendigung", "Rechnung", "SIM", "eSIM", "Sperrung"
- Transfer: "Transfermatrix", "Weiterleitung", "Sabio"
- Verification: "Authentifizierung", "Verifizierung", "Kundendaten"

### Step 3 - Read relevant sections
Use Read tool on the matching .md file to get the full procedure.

### Step 4 - Images
If a procedure includes a diagram referenced as `![...]`, read the PNG from
`KnowledgeBase/images/<doc>/img_NNN.png` to inspect it visually.

## Key German System Terms (always use exact German labels)
- "GERAETE & SIM-KARTEN" - device and SIM management section
- "ESIM-PROFILE" - eSIM management
- "RECHNUNGSHISTORIE" - billing history
- "KUNDENDATEN" - customer data
- "VERTRAGSDETAILS" - contract details

## Output Rules
- Communicate in English for all explanations
- Use original German labels for system fields, buttons, tabs
- Always include: Ticket ID, Program name, specific tray/location, step-by-step actions
- If transferable: cite Transfer Matrix destination
"""
    (KB_DIR / "SEARCH_HINT.md").write_text(search_hint, encoding="utf-8")

    print(f"\nDone. KnowledgeBase at: {KB_DIR}")
    print(f"Total documents: {len(index_entries)}")


if __name__ == "__main__":
    main()
