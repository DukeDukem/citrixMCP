#!/usr/bin/env python3
"""RETIRED — all case-processing audio cues disabled (2026-09-18).

Prowler / book / Dexter must not play and must not gate or trigger RE/PR/LF.
Processing uses arm → extract_ready → extract_auto_continue_hook → re_auto_lf_hook only.
"""
from __future__ import annotations

import argparse
import sys


def play_mp3(*_a, **_k) -> bool:
    print("AUDIO_RETIRED — play skipped", flush=True)
    return False


def play_re_complete_sound() -> bool:
    print("AUDIO_RETIRED — Prowler skipped", flush=True)
    return False


def play_re_ready_sound() -> bool:
    print("AUDIO_RETIRED — book skipped", flush=True)
    return False


def play_pr_lf_done_sound() -> bool:
    print("AUDIO_RETIRED — Dexter skipped", flush=True)
    return False


play_closeout_done_sound = play_pr_lf_done_sound
play_lf_tr_done_sound = play_pr_lf_done_sound


def main() -> int:
    ap = argparse.ArgumentParser(description="Audio cues RETIRED — no-op")
    ap.add_argument("--play", action="store_true")
    ap.add_argument("--play-ready", action="store_true")
    ap.add_argument("--play-pr-lf-done", action="store_true")
    ap.add_argument("--play-closeout-done", action="store_true")
    ap.parse_args()
    print("AUDIO_RETIRED — all cues disabled; use arm/extract/AUTO_PIPELINE only", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
