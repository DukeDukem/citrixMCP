"""
Download / verify the German Whisper CT2 model used by call_listen.

  uv run python .cursor/skills/sprinklr-call-listen/install_german_stt.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_SKILL = Path(__file__).resolve().parent
sys.path.insert(0, str(_SKILL))

from stt_backend import (  # noqa: E402
    _DEFAULT_HF_GERMAN_CT2,
    ensure_german_ct2_model,
    resolve_whisper_model_id,
)


def main() -> int:
    print(f"Preferred HF repo: {_DEFAULT_HF_GERMAN_CT2}")
    path = ensure_german_ct2_model()
    if not path:
        print("ERROR: download failed — falling back to stock 'turbo' at runtime")
        return 1
    print(f"OK: {path}")
    # Resolve as call_listen would
    mid = resolve_whisper_model_id({"stt_prefer_german_finetune": True})
    print(f"resolve_whisper_model_id → {mid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
