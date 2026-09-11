from pathlib import Path

p = Path(r".cursor/skills/sprinklr-email-automation/email_automation.py")
t = p.read_text(encoding="utf-8")
old = (
    "        for block in blocks:\n"
    '            lines = [ln.rstrip() for ln in block.split("\\n") if ln.strip() != "" or False]\n'
    '            lines = [ln for ln in block.split("\\n")]\n'
    "            # Drop purely empty lines inside a block (soft-wrap blocks shouldn't have them)\n"
    '            compact = [ln for ln in lines if ln.strip() != ""]\n'
)
new = (
    "        for block in blocks:\n"
    '            compact = [ln for ln in block.split("\\n") if ln.strip() != ""]\n'
)
if old not in t:
    raise SystemExit("OLD_NOT_FOUND")
p.write_text(t.replace(old, new, 1), encoding="utf-8")
print("CLEANED")
