import json, time
from pathlib import Path

base = Path(".cursor/skills/sprinklr-write-reply")
t = (base / "temp_reply_52889735.txt").read_text(encoding="utf-8")
(base / "latest_re_reply.txt").write_text(t, encoding="utf-8")
(base / "latest_re_reply.json").write_text(
    json.dumps(
        {"case_id": "#52889735", "response_text": t, "saved_at": time.time()},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
assert t.count("Guten Tag") == 1 and t.count("Freundliche Grüße") == 1
assert "6059874388" not in t
assert "mit 388 am Ende" in t
print("OK", len(t))
