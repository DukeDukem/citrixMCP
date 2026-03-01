"""Regenerate INDEX.md after all 6 KB files are present."""
import re
from pathlib import Path

KB_DIR = Path(__file__).parent.parent / "KnowledgeBase"

md_files = sorted(KB_DIR.glob("knowledgebase*.md"))
print(f"Found {len(md_files)} KB markdown files")

index_entries = []
for f in md_files:
    text = f.read_text(encoding="utf-8")
    img_count = text.count("![")
    preview_lines = [
        l.strip() for l in text.splitlines()
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
        "slug": f.stem,
        "file": f.name,
        "chars": len(text),
        "images": img_count,
        "preview": preview,
    })
    print(f"  {f.name}: {len(text):,} chars, {img_count} images")

index_lines = [
    "# KnowledgeBase Index\n",
    "Searchable knowledge base for O2/Telefonica customer support (Backoffice E-Mail team).",
    "Source documents were Word files (knowledgebase*.docx) converted to Markdown.\n",
    "## Documents\n",
    "| File | Characters | Images | Preview |",
    "| --- | --- | --- | --- |",
]
for e in index_entries:
    prev = e["preview"].replace("|", "/")[:100]
    index_lines.append(
        f"| [{e['file']}]({e['file']}) | {e['chars']:,} | {e['images']} | {prev}... |"
    )

index_lines += [
    "\n## How to Query\n",
    "- Read **SEARCH_HINT.md** for Cursor agent query instructions.",
    "- Use Grep across `KnowledgeBase/*.md` for any German or English keyword.",
    "- Open individual `.md` files for full document content.",
    "- Images are in `KnowledgeBase/images/<docname>/`.\n",
    "## Total Coverage\n",
    f"- {len(index_entries)} documents",
    f"- {sum(e['chars'] for e in index_entries):,} total characters",
    f"- {sum(e['images'] for e in index_entries):,} total images\n",
]

(KB_DIR / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")
print("INDEX.md regenerated.")
