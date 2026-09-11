import json, time
from pathlib import Path

base = Path(".cursor/skills/sprinklr-write-reply")
t = (base / "temp_reply_52702498.txt").read_text(encoding="utf-8")
(base / "latest_re_reply.txt").write_text(t, encoding="utf-8")
(base / "latest_re_reply.json").write_text(
    json.dumps(
        {"case_id": "#52702498", "response_text": t, "saved_at": time.time()},
        ensure_ascii=False,
        indent=2,
    ),
    encoding="utf-8",
)
assert t.count("Guten Tag") == 1 and t.count("Freundliche Grüße") == 1
assert "6028267392" not in t and "1429599729" not in t
print("OK", len(t))
