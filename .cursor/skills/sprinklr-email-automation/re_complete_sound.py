"""Play audio cues: Prowler (extract start), book (RE ready), Dexter (PR LF done)."""
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
_DEFAULT_PR_LF_DONE = Path(
    r"c:\Users\PC ENTER\Downloads\Dexter Meme Sound Effect.mp3"
)
_DEFAULT_RE_READY = Path(
    r"c:\Users\PC ENTER\Downloads\(With sound sfx) Book opening with turning pages Fairy Tale - No Watermark Free iStock Footage Video.mp3"
)
_DEFAULT_VOLUME = 0.75  # MediaPlayer 0.0–1.0


def _clamp_volume(raw) -> float:
    try:
        v = float(raw)
    except (TypeError, ValueError):
        return _DEFAULT_VOLUME
    if v > 1.0:
        v = v / 100.0
    return max(0.0, min(1.0, v))


def _read_cfg() -> dict:
    cfg_path = _REPO_ROOT / "config.json"
    if not cfg_path.exists():
        return {}
    try:
        return json.loads(cfg_path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("Could not read config.json: %s", e)
        return {}


def _volume_from_cfg(cfg: dict, *keys: str) -> float:
    for key in keys:
        if key in cfg and cfg[key] is not None:
            return _clamp_volume(cfg[key])
    return _DEFAULT_VOLUME


def _path_from_cfg(cfg: dict, key: str, *fallbacks: Path) -> Path | None:
    custom = (cfg.get(key) or "").strip()
    if custom:
        p = Path(custom)
        if p.is_file():
            return p
    for candidate in fallbacks:
        if candidate.is_file():
            return candidate
    return None


def _load_re_complete_config() -> tuple[Path | None, float]:
    """Prowler / armed extract start: (path, volume)."""
    cfg = _read_cfg()
    path = _path_from_cfg(
        cfg, "re_complete_sound_path", _DEFAULT_ASSET, _DOWNLOADS_FALLBACK
    )
    volume = _volume_from_cfg(cfg, "re_complete_sound_volume")
    return path, volume


def _load_re_ready_config() -> tuple[Path | None, float]:
    """Book opening / RE 7-step ready: (path, volume)."""
    cfg = _read_cfg()
    path = _path_from_cfg(cfg, "re_ready_sound_path", _DEFAULT_RE_READY)
    volume = _volume_from_cfg(
        cfg, "re_ready_sound_volume", "re_complete_sound_volume"
    )
    return path, volume


def _load_pr_lf_done_config() -> tuple[Path | None, float]:
    """Dexter / PR LF done: (path, volume)."""
    cfg = _read_cfg()
    path = _path_from_cfg(cfg, "pr_lf_done_sound_path", _DEFAULT_PR_LF_DONE)
    volume = _volume_from_cfg(
        cfg, "pr_lf_done_sound_volume", "re_complete_sound_volume"
    )
    return path, volume


def _load_sound_config() -> tuple[Path | None, float]:
    """Back-compat alias for Prowler."""
    return _load_re_complete_config()


def play_mp3(
    sound: Path,
    volume: float,
    *,
    label: str = "SOUND",
    hold_ms: int = 3500,
) -> bool:
    """Non-blocking Windows MediaPlayer playback. Returns True if started."""
    if sys.platform != "win32":
        logger.info("%s skipped (non-Windows)", label)
        return False
    if not sound.is_file():
        logger.warning("%s file not found: %s", label, sound)
        print(f"[WARN] {label} file not found — skipping audio cue.")
        return False

    uri = sound.resolve().as_uri()
    vol = max(0.0, min(1.0, float(volume)))
    hold = max(500, int(hold_ms))
    ps = (
        "Add-Type -AssemblyName presentationCore; "
        f"$p = New-Object System.Windows.Media.MediaPlayer; "
        f"$p.Open([uri]'{uri}'); "
        f"$p.Volume = {vol:.4f}; "
        "$p.Play(); "
        f"Start-Sleep -Milliseconds {hold}"
    )
    try:
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            creationflags=creationflags,
        )
        print(f"{label} volume={vol:.2f}")
        return True
    except Exception as e:
        logger.warning("Could not play %s: %s", label, e)
        print(f"[WARN] Could not play {label}: {e}")
        return False


def play_re_complete_sound() -> bool:
    """Prowler cue (armed RE extract start)."""
    sound, volume = _load_re_complete_config()
    if sound is None:
        logger.warning("RE complete (Prowler) sound file not found")
        print("[WARN] RE complete sound not found — skipping audio cue.")
        return False
    return play_mp3(sound, volume, label="RE_COMPLETE_SOUND", hold_ms=2800)


def play_re_ready_sound() -> bool:
    """Book-opening cue when agent finishes full 7-step RE (ready to read)."""
    sound, volume = _load_re_ready_config()
    if sound is None:
        logger.warning("RE ready sound file not found")
        print("[WARN] RE ready sound not found — skipping audio cue.")
        return False
    return play_mp3(sound, volume, label="RE_READY_SOUND", hold_ms=5500)


def play_pr_lf_done_sound() -> bool:
    """Dexter cue when agent finishes PR LF close-out."""
    sound, volume = _load_pr_lf_done_config()
    if sound is None:
        logger.warning("PR LF done sound file not found")
        print("[WARN] PR LF done sound not found — skipping audio cue.")
        return False
    return play_mp3(sound, volume, label="PR_LF_DONE_SOUND", hold_ms=4500)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="RE / PR LF audio cues")
    ap.add_argument("--play", action="store_true", help="Play Prowler (extract start)")
    ap.add_argument(
        "--play-ready",
        action="store_true",
        help="Play book opening (RE 7-step ready)",
    )
    ap.add_argument(
        "--play-pr-lf",
        action="store_true",
        help="Play Dexter (PR LF done)",
    )
    ap.add_argument(
        "--volume",
        type=float,
        default=None,
        help="Override volume for this play (0.0–1.0 or 0–100)",
    )
    args = ap.parse_args()
    modes = sum(bool(x) for x in (args.play, args.play_ready, args.play_pr_lf))
    if modes == 1:
        vol_override = _clamp_volume(args.volume) if args.volume is not None else None

        if args.play_pr_lf:
            sound, volume = _load_pr_lf_done_config()
            label, hold = "PR_LF_DONE_SOUND", 4500
        elif args.play_ready:
            sound, volume = _load_re_ready_config()
            label, hold = "RE_READY_SOUND", 5500
        else:
            sound, volume = _load_re_complete_config()
            label, hold = "RE_COMPLETE_SOUND", 2800

        if vol_override is not None:
            volume = vol_override
        if sound is None:
            raise SystemExit(1)
        raise SystemExit(0 if play_mp3(sound, volume, label=label, hold_ms=hold) else 1)

    ap.print_help()
    raise SystemExit(1)
