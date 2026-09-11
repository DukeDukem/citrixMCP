import json, time
from pathlib import Path

base = Path(".cursor/skills/sprinklr-write-reply")
t = (base / "temp_reply_52889320.txt").read_text(encoding="utf-8")
(base / "latest_re_reply.txt").write_text(t, encoding="utf-8")
(base / "latest_re_reply.json").write_text(
    json.dumps(
        {"case_id": "#52889320", "response_text": t, "saved_at": time.time()},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
assert t.count("Guten Tag") == 1
assert t.count("Freundliche Grüße") == 1
assert "089 78 79 79 400" in t
print("OK", len(t))
