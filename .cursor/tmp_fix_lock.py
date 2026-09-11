from pathlib import Path
import json
import time

text = Path(".cursor/skills/sprinklr-write-reply/reply_55613978.txt").read_text(encoding="utf-8").strip()
payload = {
    "case_id": "#55613978",
    "response_text": text,
    "saved_at": int(time.time()),
    "source": "user_directed",
}
Path(".cursor/skills/sprinklr-write-reply/latest_re_reply.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
Path(".cursor/skills/sprinklr-write-reply/latest_user_directed_reply.json").write_text(
    json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
Path(".cursor/skills/sprinklr-write-reply/latest_re_reply.txt").write_text(text + "\n", encoding="utf-8")
print("RE_LOCK_OK", len(text))
