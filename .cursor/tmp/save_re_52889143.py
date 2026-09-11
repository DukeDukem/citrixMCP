import json, time
from pathlib import Path

p = Path(".cursor/skills/sprinklr-write-reply/temp_reply_52889143.txt")
t = p.read_text(encoding="utf-8")
t = t.replace('unter "Rechnung"', "unter \u201eRechnung\u201c")
p.write_text(t, encoding="utf-8")
base = Path(".cursor/skills/sprinklr-write-reply")
(base / "latest_re_reply.txt").write_text(t, encoding="utf-8")
(base / "latest_re_reply.json").write_text(
    json.dumps(
        {"case_id": "#52889143", "response_text": t, "saved_at": time.time()},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
assert t.count("Guten Tag") == 1
assert t.count("Freundliche Grüße") == 1
print("OK", len(t))
