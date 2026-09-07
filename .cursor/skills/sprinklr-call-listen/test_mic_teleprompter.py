"""
Mic → STT → greeting gate → teleprompter smoke test (no Sprinklr call required).

Usage:
  uv run python .cursor/skills/sprinklr-call-listen/test_mic_teleprompter.py
  uv run python .cursor/skills/sprinklr-call-listen/test_mic_teleprompter.py --seconds 10
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_SKILL = Path(__file__).resolve().parent
_REPO = _SKILL.parent.parent.parent
_STATE = _REPO / ".cursor" / "state"
_CHUNKS = _STATE / "call_audio_chunks"
_TP_LATEST = _STATE / "call_teleprompter_latest.txt"
_TP_UI_META = _STATE / "call_teleprompter_ui.json"
_BRIEF = _STATE / "call_brief_MIC_TEST.txt"
_CAPTURE = _SKILL / "capture_path.json"


def _spawn_ui() -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    if _TP_UI_META.exists():
        try:
            meta = json.loads(_TP_UI_META.read_text(encoding="utf-8"))
            pid = int(meta.get("pid") or 0)
            if pid and sys.platform == "win32":
                out = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                if str(pid) in (out.stdout or ""):
                    print(f"TELEPROMPTER_UI_PID {pid} (already running)", flush=True)
                    return
        except Exception:
            pass
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
    proc = subprocess.Popen(
        [sys.executable, str(_SKILL / "teleprompter_ui.py")],
        cwd=str(_REPO),
        creationflags=creationflags,
    )
    _TP_UI_META.write_text(
        json.dumps({"pid": proc.pid, "started_at": datetime.now(timezone.utc).isoformat()}),
        encoding="utf-8",
    )
    print(f"TELEPROMPTER_UI_PID {proc.pid}", flush=True)


def _load_cfg() -> dict:
    try:
        return json.loads(_CAPTURE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, default=8.0)
    ap.add_argument("--device", type=int, default=None, help="sounddevice input index")
    ap.add_argument("--list-devices", action="store_true")
    args = ap.parse_args()

    try:
        import sounddevice as sd
    except ImportError:
        print("ERROR: sounddevice missing — uv pip install sounddevice", file=sys.stderr)
        return 2

    if args.list_devices:
        print("default", sd.default.device)
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                print(f"{i}: in={d['max_input_channels']} sr={d.get('default_samplerate')} {d.get('name')}")
        return 0

    sys.path.insert(0, str(_SKILL))
    from greeting_gate import CustomerPhaseGate
    from stt_backend import backend_name, transcribe_wav
    from teleprompter import generate_talk_track

    cfg = _load_cfg()
    stt = backend_name()
    print(f"STT_BACKEND {stt}", flush=True)
    if stt == "none":
        print("ERROR: no STT backend", file=sys.stderr)
        return 2

    _spawn_ui()
    _STATE.mkdir(parents=True, exist_ok=True)
    _CHUNKS.mkdir(parents=True, exist_ok=True)

    device = args.device
    if device is None:
        try:
            device = int(sd.default.device[0])
        except Exception:
            device = None
    try:
        info = sd.query_devices(device)
        native_fs = int(float(info.get("default_samplerate") or 44100))
        name = info.get("name")
    except Exception:
        native_fs = 44100
        name = str(device)

    target_fs = 16000
    secs = max(3.0, float(args.seconds))
    print("", flush=True)
    print("=" * 60, flush=True)
    print(f"MIC TEST — device={device} ({name}) @ {native_fs} Hz for {secs:.0f}s", flush=True)
    print('Speak clearly: "Willkommen bei o2, Lukas ist mein Name, was kann ich für Sie tun?"', flush=True)
    print("=" * 60, flush=True)
    time.sleep(0.8)

    try:
        recording = sd.rec(
            int(secs * native_fs),
            samplerate=native_fs,
            channels=1,
            dtype="float32",
            device=device,
        )
        sd.wait()
    except Exception as e:
        print(f"ERROR: record failed: {e}", file=sys.stderr)
        return 2

    pcm = np.clip(recording.flatten(), -1, 1)
    peak = float(np.max(np.abs(pcm))) if pcm.size else 0.0
    print(f"AUDIO_PEAK {peak:.4f} (near 0 = silence / muted / wrong device)", flush=True)

    # Downsample to 16 kHz for whisper
    if native_fs != target_fs and pcm.size:
        ratio = native_fs / target_fs
        out_len = int(pcm.size / ratio)
        idx = (np.arange(out_len) * ratio).astype(np.int64)
        pcm = pcm[np.clip(idx, 0, pcm.size - 1)]

    wav_path = _CHUNKS / f"mic_test_{int(time.time() * 1000)}.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(target_fs)
        w.writeframes((pcm * 32767).astype("int16").tobytes())
    print(f"WAV {wav_path}", flush=True)

    print("Transcribing…", flush=True)
    text = (transcribe_wav(wav_path, language=cfg.get("stt_language") or "de") or "").strip()
    print(f"STT_RAW: {text or '(empty)'}", flush=True)

    gate = CustomerPhaseGate(cfg)
    keep, evt = gate.filter(text)
    if evt:
        print(evt, flush=True)
    print(f"GATE_OPEN {gate.open} reason={gate.opened_reason}", flush=True)
    print(f"KEEP_AS_CUSTOMER: {keep or '(none)'}", flush=True)

    stamp = datetime.now().strftime("%H:%M:%S")
    with _BRIEF.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] STT_RAW: {text}\n")
        if evt:
            f.write(f"[{stamp}] {evt}\n")
        if keep:
            f.write(f"[{stamp}] [Kunde] {keep}\n")

    customer_for_tp = keep
    if gate.open and not customer_for_tp:
        customer_for_tp = (
            "Hallo, ich habe eine Frage zu meiner Rechnung und brauche bitte kurz Hilfe."
        )
        print("TELEPROMPTER_DEMO using sample customer line (gate open, no customer text)", flush=True)

    if customer_for_tp:
        talk, backend = generate_talk_track(customer_for_tp, capture_cfg=cfg)
        latest = (
            f"SAY THIS ({backend}):\n\n{talk.strip()}\n\n"
            f"— (customer) {customer_for_tp[:240]}\n"
        )
        _TP_LATEST.write_text(latest, encoding="utf-8")
        print("TELEPROMPTER_UPDATE", flush=True)
        print(latest, flush=True)
    else:
        _TP_LATEST.write_text(
            "SAY THIS:\n\n(no speech / gate still closed — try louder greeting)\n",
            encoding="utf-8",
        )
        print("TELEPROMPTER: gate closed or empty STT — check mic / speak greeting again", flush=True)

    print(f"BRIEF_FILE {_BRIEF}", flush=True)
    print("Look at the on-top teleprompter window.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
