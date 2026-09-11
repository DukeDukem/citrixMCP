"""Track armed extract completion so the agent can pick up RE/LF after Prowler."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parents[2] / "state"
_READY_FILE = _STATE_DIR / "extract_ready.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _case_id_from_segment(segment: str) -> str:
    for pat in (
        r"Case ID:\s*(Fall\s*#\d+)",
        r"Fall\s*#(\d{5,})",
        r"#(\d{5,})",
    ):
        m = re.search(pat, segment, re.I)
        if m:
            raw = m.group(1) if m.lastindex else m.group(0)
            digits = re.sub(r"\D", "", raw)
            if digits:
                return f"#{digits}"
    return ""


def write_extract_ready(
    segment: str,
    *,
    marker: str = "",
    source: str = "arm_watch",
) -> None:
    """Mark extract ready for agent pickup (Prowler / EXTRACT_DONE)."""
    if "CHANNEL: CALL" in segment or "CALL_LF_GATE" in segment:
        channel = "CALL"
        gate = "CALL_LF_GATE"
    else:
        channel = "EMAIL"
        gate = "RE_TEXT_ONLY_GATE"

    payload = {
        "ready": True,
        "consumed": False,
        "at": _now_iso(),
        "marker": marker,
        "source": source,
        "case_id": _case_id_from_segment(segment),
        "channel": channel,
        "gate": gate,
        "extract_file": str(_STATE_DIR / "latest_extract.md"),
        "arm_log": str(_STATE_DIR / "arm_watch.log"),
    }
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _READY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _dispatched = _STATE_DIR / "auto_continue_dispatched.json"
        if _dispatched.exists():
            _dispatched.unlink(missing_ok=True)
        print(f"EXTRACT_READY_WRITTEN {_READY_FILE}", flush=True)
    except Exception as e:
        print(f"[WARN] extract_ready write failed: {e}", flush=True)


def read_extract_ready() -> dict | None:
    if not _READY_FILE.exists():
        return None
    try:
        data = json.loads(_READY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def mark_consumed() -> None:
    data = read_extract_ready()
    if not data:
        return
    data["consumed"] = True
    data["consumed_at"] = _now_iso()
    try:
        _READY_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception:
        pass


def is_pending_pickup() -> bool:
    data = read_extract_ready()
    return bool(data and data.get("ready") and not data.get("consumed"))


def write_extract_ready_simple(
    *,
    case_id: str = "",
    marker: str = "",
    channel: str = "EMAIL",
    source: str = "arm_watch",
) -> None:
    """Minimal ready flag when full log segment is not available yet."""
    gate = "CALL_LF_GATE" if channel.upper() == "CALL" else "RE_TEXT_ONLY_GATE"
    payload = {
        "ready": True,
        "consumed": False,
        "at": _now_iso(),
        "marker": marker,
        "source": source,
        "case_id": case_id if case_id.startswith("#") else (f"#{case_id}" if case_id else ""),
        "channel": channel.upper(),
        "gate": gate,
        "extract_file": str(_STATE_DIR / "latest_extract.md"),
        "arm_log": str(_STATE_DIR / "arm_watch.log"),
    }
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _READY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _dispatched = _STATE_DIR / "auto_continue_dispatched.json"
        if _dispatched.exists():
            _dispatched.unlink(missing_ok=True)
        print(f"EXTRACT_READY_WRITTEN {_READY_FILE}", flush=True)
    except Exception as e:
        print(f"[WARN] extract_ready simple write failed: {e}", flush=True)
