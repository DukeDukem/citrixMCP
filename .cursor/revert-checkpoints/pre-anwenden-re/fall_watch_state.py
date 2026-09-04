"""
Shared state: LF / PR LF primes Fall # watch; sidebar click triggers detection.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_STATE_DIR = Path(__file__).resolve().parent.parent.parent / "state"
_STATE_FILE = _STATE_DIR / "fall_watch_primed.json"


def _read_state() -> dict[str, Any]:
    if not _STATE_FILE.exists():
        return {}
    try:
        data = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state(data: dict[str, Any]) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def prime_fall_watch(case_id: str | None = None, source: str = "lf") -> None:
    """Mark watch as primed — next sidebar click may trigger Fall # detection."""
    digits = ""
    if case_id:
        digits = "".join(c for c in case_id if c.isdigit())
    _write_state(
        {
            "primed": True,
            "case_id": f"#{digits}" if digits else "",
            "source": source,
            "primed_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def is_fall_watch_primed() -> bool:
    return bool(_read_state().get("primed"))


def get_primed_info() -> dict[str, Any]:
    return _read_state()


def clear_fall_watch_prime() -> None:
    if _STATE_FILE.exists():
        try:
            _STATE_FILE.unlink()
        except Exception:
            _write_state({"primed": False})


def consume_fall_watch_prime() -> bool:
    """Return True if was primed; clears prime (one-shot per LF/PR LF)."""
    state = _read_state()
    if not state.get("primed"):
        return False
    clear_fall_watch_prime()
    return True


if __name__ == "__main__":
    import argparse
    import sys

    ap = argparse.ArgumentParser(description="Fall # watch prime state")
    ap.add_argument("--prime", action="store_true", help="Set primed")
    ap.add_argument("--case-id", default="", help="Fall # that was logged")
    ap.add_argument("--source", default="lf", help="lf | pr-lf | session-start")
    ap.add_argument("--clear", action="store_true", help="Clear primed state")
    ap.add_argument("--status", action="store_true", help="Print primed status")
    args = ap.parse_args()

    if args.clear:
        clear_fall_watch_prime()
        print("FALL_WATCH_PRIME_CLEARED")
        sys.exit(0)
    if args.status:
        info = get_primed_info()
        if info.get("primed"):
            print(f"FALL_WATCH_PRIMED case={info.get('case_id', '')} source={info.get('source', '')}")
        else:
            print("FALL_WATCH_NOT_PRIMED")
        sys.exit(0)
    if args.prime:
        prime_fall_watch(args.case_id or None, source=args.source)
        print(f"FALL_WATCH_PRIMED case={args.case_id or '(none)'} source={args.source}")
        sys.exit(0)
    ap.print_help()
    sys.exit(1)
