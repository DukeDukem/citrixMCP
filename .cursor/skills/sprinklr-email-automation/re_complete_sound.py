"""Play audio cue when RE processing is fully complete (after agent section 7)."""
from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent.parent
_DEFAULT_ASSET = (
    _REPO_ROOT
    / ".cursor"
    / "skills"
    / "sprinklr-read-answer-email"
    / "assets"
    / "re-complete.mp3"
)
_DOWNLOADS_FALLBACK = Path(
    r"c:\Users\PC ENTER\Downloads\Prowler Sound Effect (From Spider-Man_ Into The Spider-Verse).mp3"
)


def _resolve_sound_path() -> Path | None:
    cfg_path = _REPO_ROOT / "config.json"
    if cfg_path.exists():
        try:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            custom = (cfg.get("re_complete_sound_path") or "").strip()
            if custom:
                p = Path(custom)
                if p.is_file():
                    return p
        except Exception as e:
            logger.debug("Could not read re_complete_sound_path from config: %s", e)
    for candidate in (_DEFAULT_ASSET, _DOWNLOADS_FALLBACK):
        if candidate.is_file():
            return candidate
    return None


def play_re_complete_sound() -> bool:
    """Non-blocking MP3 cue when full RE output (section 7) is done. Returns True if playback started."""
    sound = _resolve_sound_path()
    if sound is None:
        logger.warning("RE complete sound file not found")
        print("[WARN] RE complete sound not found — skipping audio cue.")
        return False

    if sys.platform != "win32":
        logger.info("RE complete sound skipped (non-Windows)")
        return False

    uri = sound.resolve().as_uri()
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        f"$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([uri]'{uri}'); "
        "$p.Play(); "
        "Start-Sleep -Milliseconds 2800"
    )
    try:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=creationflags,
        )
        print("RE_COMPLETE_SOUND")
        return True
    except Exception as e:
        logger.warning("Could not play RE complete sound: %s", e)
        print(f"[WARN] Could not play RE complete sound: {e}")
        return False


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="RE complete audio cue")
    ap.add_argument("--play", action="store_true", help="Play RE complete sound (after agent section 7)")
    args = ap.parse_args()
    if args.play:
        raise SystemExit(0 if play_re_complete_sound() else 1)
    ap.print_help()
    raise SystemExit(1)
