"""
Temporary script: convert Word (.docx) files from a source folder to Markdown in KnowledgeBase.
Usage: uv run --with mammoth --with html2text scratchspace/convert_docx_to_markdown.py
Or: pip install mammoth html2text && python scratchspace/convert_docx_to_markdown.py
"""
import os
import re
import sys

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SOURCE_DIR = r"C:\Users\PC ENTER\Desktop\YOUMMDAY IMPORTANT SHIT\KNOWLEDGE BASE"
OUT_DIR = os.path.join(REPO_ROOT, "KnowledgeBase")


def safe_filename(name: str) -> str:
    """Make a safe markdown filename from docx name."""
    base = os.path.splitext(name)[0]
    base = re.sub(r"[^\w\s\-]", "", base)
    base = re.sub(r"\s+", "_", base).strip("_") or "document"
    return base + ".md"


def main():
    try:
        import mammoth
        import html2text
    except ImportError as e:
        print("Install: pip install mammoth html2text", file=sys.stderr)
        raise SystemExit(1) from e

    if not os.path.isdir(SOURCE_DIR):
        print(f"Source directory not found: {SOURCE_DIR}", file=sys.stderr)
        sys.exit(1)

    os.makedirs(OUT_DIR, exist_ok=True)
    h2t = html2text.HTML2Text()
    h2t.ignore_links = False
    h2t.ignore_images = False
    h2t.body_width = 0

    docx_files = [f for f in os.listdir(SOURCE_DIR) if f.lower().endswith(".docx")]
    if not docx_files:
        print("No .docx files found in", SOURCE_DIR)
        return

    for name in sorted(docx_files):
        src_path = os.path.join(SOURCE_DIR, name)
        if not os.path.isfile(src_path):
            continue
        out_name = safe_filename(name)
        out_path = os.path.join(OUT_DIR, out_name)
        try:
            with open(src_path, "rb") as f:
                result = mammoth.convert_to_html(f)
            html = result.value
            if result.messages:
                for msg in result.messages:
                    print(f"  [{name}] {msg}", file=sys.stderr)
            md = h2t.handle(html)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(md)
            print(f"OK: {name} -> KnowledgeBase/{out_name}")
        except Exception as e:
            print(f"FAIL: {name} - {e}", file=sys.stderr)

    print(f"Done. Markdown files in {OUT_DIR}")


if __name__ == "__main__":
    main()
