import json, time
from pathlib import Path

reply = Path(".cursor/skills/sprinklr-write-reply/reply_55546630.txt").read_text(encoding="utf-8").strip().replace("\r\n", "\n")
assert reply.count("Guten Tag") == 1
assert "o2online.de/goto/wechsel" in reply
assert "Vertragsinhaberwechsel" in reply
assert "Fall #" not in reply
assert "Authentifizierungsmatrix" not in reply

payload = {
    "case_id": "#55546630",
    "response_text": reply,
    "saved_at": int(time.time()),
    "source": "user_directed",
}
base = Path(".cursor/skills/sprinklr-write-reply")
for name in ("latest_re_reply.json", "latest_user_directed_reply.json", "latest_re_reply.txt"):
    path = base / name
    if name.endswith(".txt"):
        path.write_text(reply + "\n", encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print("synced", len(reply), "case #55546630")
