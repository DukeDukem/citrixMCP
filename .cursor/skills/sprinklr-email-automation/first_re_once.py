"""Post-login first RE must extract the open case (--once), not arm Anwenden."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_DIR = Path(__file__).resolve().parent.parent.parent / "state"
_STATE_FILE = _STATE_DIR / "first_re_once.json"


def _read() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write(data: dict[str, Any]) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_first_re_once(source: str = "login") -> None:
    """Call after successful login — next default RE runs --once."""
    _write(
        {
            "pending": True,
            "source": source,
            "set_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def is_first_re_once_pending() -> bool:
    return bool(_read().get("pending"))


def clear_first_re_once() -> None:
    if _STATE_FILE.exists():
        try:
            _STATE_FILE.unlink()
        except Exception:
            _write({"pending": False})


def consume_first_re_once() -> bool:
    """Return True if first-RE-once was pending; clear it (one-shot)."""
    if not is_first_re_once_pending():
        return False
    clear_first_re_once()
    return True


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="First RE after login = --once gate")
    ap.add_argument("--set", action="store_true", help="Mark next RE as --once")
    ap.add_argument("--clear", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--consume", action="store_true")
    args = ap.parse_args()
    if args.set:
        set_first_re_once()
        print("FIRST_RE_ONCE_PENDING")
        sys.exit(0)
    if args.clear:
        clear_first_re_once()
        print("FIRST_RE_ONCE_CLEARED")
        sys.exit(0)
    if args.consume:
        print("FIRST_RE_ONCE_CONSUMED" if consume_first_re_once() else "FIRST_RE_ONCE_NOT_PENDING")
        sys.exit(0)
    if args.status:
        print("FIRST_RE_ONCE_PENDING" if is_first_re_once_pending() else "FIRST_RE_ONCE_NOT_PENDING")
        sys.exit(0)
    ap.print_help()
    sys.exit(1)
