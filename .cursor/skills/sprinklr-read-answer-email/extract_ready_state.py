"""Track armed extract completion so the agent can pick up RE/LF via AUTO_PIPELINE."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parents[2] / "state"
_READY_FILE = _STATE_DIR / "extract_ready.json"
_MONITORING_FILE = _STATE_DIR / "monitoring_armed.json"


# ---------------------------------------------------------------------------
# Monitoring-armed gate
# Active window: arm fires → mark_consumed() called (extract processed)
# Outside that window the stop hook must be silent.
# ---------------------------------------------------------------------------

def set_monitoring_armed(armed: bool) -> None:
    """Set/clear the monitoring armed flag."""
    try:
        _STATE_DIR.mkdir(parents=True, exist_ok=True)
        _MONITORING_FILE.write_text(
            json.dumps({"armed": armed, "at": _now_iso()}, indent=2),
            encoding="utf-8",
        )
        print(f"MONITORING_ARMED={armed}", flush=True)
    except Exception as e:
        print(f"[WARN] monitoring_armed write failed: {e}", flush=True)


def is_monitoring_armed() -> bool:
    """True only during the arm window (arm start → extract consumed)."""
    if not _MONITORING_FILE.exists():
        return False
    try:
        data = json.loads(_MONITORING_FILE.read_text(encoding="utf-8"))
        return bool(data.get("armed"))
    except Exception:
        return False


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
    """Mark extract ready for agent pickup (arm/await — not audio)."""
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
        prev = read_extract_ready() or {}
        new_case = payload["case_id"]
        prev_case = str(prev.get("case_id") or "")
        new_d = re.sub(r"\D", "", new_case or "")
        prev_d = re.sub(r"\D", "", prev_case)

        _dispatched = _STATE_DIR / "auto_continue_dispatched.json"
        d = {}
        if _dispatched.exists():
            try:
                d = json.loads(_dispatched.read_text(encoding="utf-8"))
            except Exception:
                d = {}
        d_case = re.sub(r"\D", "", str(d.get("case_id") or ""))

        # Same Fall # already dispatched/consumed → do not reopen (stops PR re-fire)
        if new_d and (d_case == new_d or (prev.get("consumed") and prev_d == new_d)):
            payload["consumed"] = True
            payload["ready"] = True
            payload["note"] = "same_case_not_reopened"
            payload["at"] = prev.get("at") or payload["at"]
            _READY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"EXTRACT_READY_SKIP_REOPEN {new_case}", flush=True)
            return

        _READY_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        # Clear dispatched only when Fall # changes
        if _dispatched.exists() and d_case and d_case != new_d:
            _dispatched.unlink(missing_ok=True)
        set_monitoring_armed(True)
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
    # Disarm monitoring: window is arm → consumed. No hook fires after this.
    set_monitoring_armed(False)


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
    cid = case_id if case_id.startswith("#") else (f"#{case_id}" if case_id else "")
    # Reuse full writer path for same-case guards
    write_extract_ready(
        f"Case ID: Fall {cid}\nCHANNEL: {channel.upper()}\n",
        marker=marker or "SIMPLE",
        source=source,
    )
