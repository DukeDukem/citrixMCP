from pathlib import Path
import json, time
text = Path(".cursor/state/temp_reply.txt").read_text(encoding="utf-8").strip()
payload = {
    "case_id": "#56096439",
    "response_text": text,
    "saved_at": int(time.time()),
    "source": "user_directed",
}
base = Path(".cursor/skills/sprinklr-write-reply")
(base / "latest_re_reply.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(base / "latest_user_directed_reply.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(base / "latest_re_reply.txt").write_text(text + "\n", encoding="utf-8")
lock = Path(".cursor/tmp/last_pr_write_lock.json")
if lock.exists():
    lock.unlink()
print("RE_LOCK_OK", "#56096439", len(text))
