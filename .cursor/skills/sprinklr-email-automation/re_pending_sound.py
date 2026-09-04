"""Set when RE extract finished; cleared after section-7 sound plays."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

_STATE_DIR = Path(__file__).resolve().parent.parent / "state"
_PENDING_FILE = _STATE_DIR / "re_pending_sound.json"


def set_re_pending_sound(case_id: str | None = None) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _PENDING_FILE.write_text(
        json.dumps(
            {
                "pending": True,
                "case_id": case_id or "",
                "set_at": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def clear_re_pending_sound() -> None:
    if _PENDING_FILE.exists():
        try:
            _PENDING_FILE.unlink()
        except Exception:
            pass


def is_re_pending_sound() -> bool:
    if not _PENDING_FILE.exists():
        return False
    try:
        data = json.loads(_PENDING_FILE.read_text(encoding="utf-8"))
        return bool(data.get("pending"))
    except Exception:
        return False
