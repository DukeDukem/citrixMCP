"""
CALL listen watch: capture Sprinklr call audio → local faster-whisper → call_brief_{FALL}.txt

Usage:
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --foreground
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --stop
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --status

DISABLED BY DEFAULT (capture_path.json enabled=false) until a better STT model is ready.
Reactivate: set enabled=true (+ teleprompter_enabled=true) in capture_path.json, then --arm.
While disabled, CALL handling uses typed BRIEF only (no STT / teleprompter).
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import subprocess
import sys
import time
import wave
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_SKILL = Path(__file__).resolve().parent
_REPO = _SKILL.parent.parent.parent
_STATE = _REPO / ".cursor" / "state"
_CHUNKS = _STATE / "call_audio_chunks"
_LOG = _STATE / "call_listen.log"
_META = _STATE / "call_listen.json"
_STOP = _STATE / "call_listen_stop"
_PRIME = _STATE / "call_listen_prime"
_CAPTURE_PATH = _SKILL / "capture_path.json"
_TP_LATEST = _STATE / "call_teleprompter_latest.txt"
_TP_UI_META = _STATE / "call_teleprompter_ui.json"
_LIVE_DIR = _STATE  # call_live_{FALL}.txt written by TeleprompterDisplay


# Inject: hook PCs, tap remote audio via AudioContext → Int16 PCM chunks (no webm/ffmpeg).
_INJECT_CAPTURE_JS = """
() => {
  if (window.__callListenInjected) return { ok: true, already: true };
  window.__sprCallPcs = window.__sprCallPcs || [];
  window.__callListenChunks = [];
  window.__callListenStatus = { recording: false, tracks: 0, sampleRate: 16000, errors: [] };

  const Orig = window.RTCPeerConnection;
  if (Orig && !window.__sprCallPcHooked) {
    window.RTCPeerConnection = function (...args) {
      const pc = new Orig(...args);
      try { window.__sprCallPcs.push(pc); } catch (e) {}
      try {
        pc.addEventListener('track', (ev) => {
          if (ev.track && ev.track.kind === 'audio') {
            window.__callListenTryStart(ev.streams && ev.streams[0]
              ? ev.streams[0]
              : new MediaStream([ev.track]));
          }
        });
      } catch (e) {}
      return pc;
    };
    window.RTCPeerConnection.prototype = Orig.prototype;
    window.__sprCallPcHooked = true;
  }

  const downsampleTo16k = (input, inRate) => {
    if (inRate === 16000) return input;
    const ratio = inRate / 16000;
    const outLen = Math.floor(input.length / ratio);
    const out = new Float32Array(outLen);
    for (let i = 0; i < outLen; i++) {
      out[i] = input[Math.floor(i * ratio)] || 0;
    }
    return out;
  };

  const floatTo16BitPCM = (float32) => {
    const buf = new ArrayBuffer(float32.length * 2);
    const view = new DataView(buf);
    for (let i = 0; i < float32.length; i++) {
      let s = Math.max(-1, Math.min(1, float32[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    // base64
    const bytes = new Uint8Array(buf);
    let binary = '';
    const chunk = 0x8000;
    for (let i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
  };

  window.__callListenTryStart = (stream) => {
    try {
      if (window.__callListenAudioCtx) return;
      if (!stream) return;
      const tracks = stream.getAudioTracks ? stream.getAudioTracks() : [];
      if (!tracks.length) return;
      window.__callListenStatus.tracks = tracks.length;
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      const ctx = new AudioCtx();
      const source = ctx.createMediaStreamSource(stream);
      const proc = ctx.createScriptProcessor(4096, 1, 1);
      let pcmBuf = [];
      let samplesAccum = 0;
      const targetRate = 16000;
      const flushEverySec = 1.0;
      proc.onaudioprocess = (e) => {
        try {
          const input = e.inputBuffer.getChannelData(0);
          const down = downsampleTo16k(input, ctx.sampleRate);
          pcmBuf.push(down);
          samplesAccum += down.length;
          if (samplesAccum >= targetRate * flushEverySec) {
            let total = 0;
            for (const p of pcmBuf) total += p.length;
            const merged = new Float32Array(total);
            let off = 0;
            for (const p of pcmBuf) { merged.set(p, off); off += p.length; }
            pcmBuf = [];
            samplesAccum = 0;
            const b64 = floatTo16BitPCM(merged);
            window.__callListenChunks.push({
              at: Date.now(),
              b64: b64,
              format: 'pcm_s16le',
              sampleRate: 16000,
              samples: merged.length,
            });
            if (window.__callListenChunks.length > 40) {
              window.__callListenChunks.splice(0, window.__callListenChunks.length - 40);
            }
          }
        } catch (err) {
          window.__callListenStatus.errors.push(String(err));
        }
      };
      source.connect(proc);
      // Do not play captured audio back into speakers (avoid echo) — silent sink
      const mute = ctx.createGain();
      mute.gain.value = 0;
      proc.connect(mute);
      mute.connect(ctx.destination);
      window.__callListenAudioCtx = ctx;
      window.__callListenProcessor = proc;
      window.__callListenStatus.recording = true;
      window.__callListenStatus.sampleRate = 16000;
    } catch (e) {
      window.__callListenStatus.errors.push(String(e));
    }
  };

  try {
    for (const pc of window.__sprCallPcs) {
      const recvs = pc.getReceivers ? pc.getReceivers() : [];
      for (const r of recvs) {
        if (r.track && r.track.kind === 'audio') {
          window.__callListenTryStart(new MediaStream([r.track]));
        }
      }
    }
  } catch (e) {}

  try {
    document.querySelectorAll('audio').forEach((a) => {
      if (a.srcObject) window.__callListenTryStart(a.srcObject);
    });
  } catch (e) {}

  window.__callListenInjected = true;
  return { ok: true, already: false };
}
"""

_POLL_CHUNKS_JS = """
() => {
  const chunks = window.__callListenChunks || [];
  window.__callListenChunks = [];
  return {
    chunks: chunks,
    status: window.__callListenStatus || {},
  };
}
"""

_STOP_RECORDER_JS = """
() => {
  try {
    if (window.__callListenProcessor) {
      try { window.__callListenProcessor.disconnect(); } catch (e) {}
    }
    if (window.__callListenAudioCtx) {
      try { window.__callListenAudioCtx.close(); } catch (e) {}
    }
  } catch (e) {}
  window.__callListenAudioCtx = null;
  window.__callListenProcessor = null;
  window.__callListenStatus = window.__callListenStatus || {};
  window.__callListenStatus.recording = false;
  return true;
}
"""


def _log(msg: str) -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    line = f"[{datetime.now().strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    with _LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _load_capture_config() -> dict[str, Any]:
    if _CAPTURE_PATH.exists():
        try:
            return json.loads(_CAPTURE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "enabled": False,
        "capture_path": "webrtc_hook",
        "fallback": "windows_loopback",
        "stt_language": "de",
    }


def _feature_enabled(cfg: dict[str, Any] | None = None) -> bool:
    """Master switch: capture_path.json → enabled (default False while parked)."""
    c = cfg if cfg is not None else _load_capture_config()
    return bool(c.get("enabled", False))


def _refuse_if_disabled(*, force: bool = False) -> int | None:
    """Return exit code if listen/teleprompter must not start; else None."""
    if force or _feature_enabled():
        return None
    print("CALL_LISTEN_DISABLED")
    print(
        "Call speech detection + teleprompter are parked "
        "(capture_path.json enabled=false)."
    )
    print(
        "Reactivate later: set enabled=true and teleprompter_enabled=true, "
        "then run call_listen.py --arm."
    )
    print("CALL cases: use typed BRIEF only until then.")
    return 2


def _brief_path(fall: str) -> Path:
    return _STATE / f"call_brief_{fall}.txt"


def _write_meta(extra: dict[str, Any] | None = None) -> None:
    data = {
        "pid": os.getpid(),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "log": str(_LOG),
        "mode": "call_listen",
    }
    if extra:
        data.update(extra)
    _STATE.mkdir(parents=True, exist_ok=True)
    _META.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_brief(fall: str, text: str, tag: str = "") -> None:
    path = _brief_path(fall)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"{tag} " if tag else ""
    with path.open("a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {prefix}{text.strip()}\n")


def _pcm_b64_to_wav(b64: str, sample_rate: int = 16000) -> Path:
    _CHUNKS.mkdir(parents=True, exist_ok=True)
    pcm = base64.b64decode(b64)
    wav_path = _CHUNKS / f"pcm_{int(time.time() * 1000)}.wav"
    with wave.open(str(wav_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return wav_path


def _transcribe_chunk(ch: dict, language: str = "de", cfg: dict | None = None) -> Optional[str]:
    sys.path.insert(0, str(_SKILL))
    from stt_backend import backend_name, transcribe_wav, webm_to_wav_ffmpeg

    b64 = ch.get("b64")
    if not b64:
        return None
    fmt = (ch.get("format") or "").lower()
    if fmt == "pcm_s16le" or ch.get("sampleRate"):
        wav = _pcm_b64_to_wav(b64, int(ch.get("sampleRate") or 16000))
        return transcribe_wav(wav, language=language, cfg=cfg)

    # Legacy webm path
    _CHUNKS.mkdir(parents=True, exist_ok=True)
    webm = _CHUNKS / f"chunk_{int(time.time() * 1000)}.webm"
    webm.write_bytes(base64.b64decode(b64))
    wav = _CHUNKS / (webm.stem + ".wav")
    if webm_to_wav_ffmpeg(webm, wav):
        return transcribe_wav(wav, language=language, cfg=cfg)
    return transcribe_wav(webm, language=language, cfg=cfg)  # may fail without av


def _try_loopback_chunk(
    seconds: float = 2.0,
    min_peak: float = 0.0005,
    preferred_device: str | None = None,
) -> Optional[Path]:
    """
    Capture what speakers play (customer audio) via soundcard loopback.

    Tries preferred device first, then all speaker loopbacks; keeps the loudest clip.
    Returns wav path, or None if below volume threshold.
    """
    try:
        import numpy as np  # type: ignore
        import soundcard as sc  # type: ignore
    except ImportError:
        _log("loopback: install soundcard — uv pip install soundcard")
        return None

    _CHUNKS.mkdir(parents=True, exist_ok=True)
    fs = 16000
    frames = max(1, int(seconds * fs))

    def _record_one(mic) -> tuple[Optional[Any], float, str]:
        try:
            data = mic.record(numframes=frames, samplerate=fs)
            pcm = np.asarray(data, dtype=np.float32)
            if pcm.ndim > 1:
                pcm = pcm.mean(axis=1)
            pcm = np.clip(pcm.flatten(), -1.0, 1.0)
            peak = float(np.max(np.abs(pcm))) if pcm.size else 0.0
            return pcm, peak, getattr(mic, "name", "?")
        except Exception as e:
            return None, 0.0, f"fail:{e}"

    try:
        speakers = list(sc.all_speakers())

        def _rank(s) -> tuple:
            nl = (s.name or "").lower()
            prefer_l = (preferred_device or "").lower()
            if prefer_l and prefer_l in nl:
                return (0, nl)
            if "hyperx" in nl or "stinger" in nl or "headset" in nl:
                return (1, nl)
            return (2, nl)

        uniq = sorted(speakers, key=_rank)
        if not uniq:
            uniq = [sc.default_speaker()]

        best_pcm = None
        best_peak = -1.0
        best_name = ""
        for s in uniq:
            try:
                mic = sc.get_microphone(id=s.name, include_loopback=True)
            except Exception:
                continue
            pcm, peak, name = _record_one(mic)
            if pcm is None:
                continue
            if peak > best_peak:
                best_peak = peak
                best_pcm = pcm
                best_name = name
            # Fast path: preferred/headset already loud enough — skip other devices
            if best_peak >= float(min_peak) and (
                "hyperx" in (best_name or "").lower()
                or "stinger" in (best_name or "").lower()
                or (preferred_device and preferred_device.lower() in (best_name or "").lower())
            ):
                break

        if best_pcm is None:
            _log("loopback: no speaker device recorded")
            return None

        if best_peak < float(min_peak):
            # Throttle: full multi-device dump at most every ~8s
            now = time.time()
            last = getattr(_try_loopback_chunk, "_last_silent_log", 0.0)
            if now - last >= 8.0:
                _try_loopback_chunk._last_silent_log = now  # type: ignore[attr-defined]
                peaks = []
                for s in uniq:
                    try:
                        mic = sc.get_microphone(id=s.name, include_loopback=True)
                        _, p, n = _record_one(mic)
                        peaks.append(f"{n}={p:.5f}")
                    except Exception as e:
                        peaks.append(f"{s.name}=err:{e}")
                _log(
                    "loopback SILENT on all speakers (skip STT) — "
                    "Sprinklr VOIP must play through Windows Speakers "
                    f"(prefer HyperX). peaks: {'; '.join(peaks)}"
                )
            return None

        wav_path = _CHUNKS / f"loop_{int(time.time() * 1000)}.wav"
        with wave.open(str(wav_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(fs)
            w.writeframes((best_pcm * 32767).astype("int16").tobytes())
        _log(f"loopback ok peak={best_peak:.5f} device={best_name}")
        return wav_path
    except Exception as e:
        _log(f"loopback capture failed: {e}")
        return None


def _set_capture_path(path_mode: str) -> None:
    """Persist capture path override (e.g. auto-fallback to loopback)."""
    cfg = _load_capture_config()
    cfg["capture_path"] = path_mode
    cfg["notes"] = (
        cfg.get("notes") or ""
    ) + f" | auto-set capture_path={path_mode} at {datetime.now().isoformat()}"
    try:
        _CAPTURE_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        _log(f"could not persist capture_path: {e}")



def _teleprompter_paths(fall: str) -> Path:
    return _STATE / f"call_teleprompter_{fall}.txt"


def _write_teleprompter(fall: str, customer: str, talk: str, backend: str, display=None) -> None:
    _STATE.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%H:%M:%S")
    block = (
        f"[{stamp}] SAY THIS (backend={backend})\n"
        f"{talk.strip()}\n"
        f"---\n"
        f"[{stamp}] Customer said:\n{customer.strip()}\n"
        f"{'=' * 40}\n"
    )
    path = _teleprompter_paths(fall)
    with path.open("a", encoding="utf-8") as f:
        f.write(block)
    if display is not None:
        display.fall = fall
        display.set_say_this(talk, customer, backend)
    else:
        latest = (
            f"[{stamp}] SAY THIS\n\n"
            f"{talk.strip()}\n\n"
            f"— (customer) {customer.strip()[:240]}{'…' if len(customer.strip()) > 240 else ''}\n"
        )
        _TP_LATEST.write_text(latest, encoding="utf-8")
    print(f"TELEPROMPTER_UPDATE fall={fall} backend={backend}", flush=True)
    _log(f"TELEPROMPTER ({backend}): {talk[:100]}…")


class UtteranceBuffer:
    """Accumulate customer STT; fire teleprompter after short silence."""

    def __init__(self, silence_s: float = 1.4, min_chars: int = 18) -> None:
        self.silence_s = silence_s
        self.min_chars = min_chars
        self.parts: list[str] = []
        self.last_speech_at = 0.0
        self.last_fire_text = ""

    def push(self, text: str) -> None:
        text = (text or "").strip()
        if not text:
            return
        self.parts.append(text)
        self.last_speech_at = time.time()

    def pending(self) -> str:
        return " ".join(self.parts).strip()

    def ready_to_fire(self) -> bool:
        if not self.parts:
            return False
        if time.time() - self.last_speech_at < self.silence_s:
            return False
        pending = self.pending()
        if len(pending) < self.min_chars:
            return False
        if pending == self.last_fire_text:
            return False
        return True

    def consume(self) -> str:
        text = self.pending()
        self.parts.clear()
        self.last_fire_text = text
        return text


def _fire_teleprompter(fall: str, customer: str, cfg: dict, display=None) -> None:
    from teleprompter import generate_talk_track

    talk, backend = generate_talk_track(customer, capture_cfg=cfg)
    _write_teleprompter(fall, customer, talk, backend, display=display)


def _spawn_teleprompter_ui() -> None:
    """Visible always-on-top window (not CREATE_NO_WINDOW)."""
    try:
        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]
        proc = subprocess.Popen(
            [sys.executable, str(_SKILL / "teleprompter_ui.py")],
            cwd=str(_REPO),
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
        _STATE.mkdir(parents=True, exist_ok=True)
        _TP_UI_META.write_text(
            json.dumps({"pid": proc.pid, "started_at": datetime.now(timezone.utc).isoformat()}),
            encoding="utf-8",
        )
        print(f"TELEPROMPTER_UI_PID {proc.pid}", flush=True)
    except Exception as e:
        print(f"[WARN] teleprompter UI: {e}", flush=True)


def _write_primed_teleprompter(fall: str, reason: str, display=None) -> None:
    """Show READY so the user greets only after CALL prime."""
    if display is not None:
        display.reset(fall)
        display.set_status(
            f"PRIMED ({reason}) — LIVE lines appear as customer speaks (proves STT pickup)"
        )
    else:
        text = (
            f"LIVE CUSTOMER (STT) — Fall #{fall}\n"
            f"PRIMED ({reason}) — waiting for customer audio…\n"
            f"{'─' * 42}\n"
            f"(no customer speech transcribed yet)\n\n"
            f"{'═' * 42}\n"
            f"SAY THIS — read to customer\n"
            f"{'─' * 42}\n"
            f"Hold greeting until PRIMED. Then greet / unhold.\n"
            f"If LIVE stays empty during talk → audio not reaching STT.\n"
        )
        try:
            _TP_LATEST.write_text(text, encoding="utf-8")
        except Exception as e:
            _log(f"prime teleprompter write: {e}")
    print(f"TELEPROMPTER_PRIMED fall={fall} reason={reason}", flush=True)


def _consume_prime_flag() -> bool:
    if not _PRIME.exists():
        return False
    try:
        _PRIME.unlink()
        return True
    except Exception:
        return True


def _prime_gate(gate, fall: str, reason: str, display=None) -> bool:
    """Open customer phase; return True if newly opened."""
    evt = gate.open_call_case(reason=reason)
    if not evt:
        return False
    _log(evt)
    print(evt, flush=True)
    _write_meta(
        {
            "fall": fall,
            "gate_open": True,
            "gate_reason": reason,
            "session_keepalive": True,
        }
    )
    _write_primed_teleprompter(fall, reason, display=display)
    return True


def cmd_prime() -> int:
    """Agent: CHANNEL: CALL detected → prime customer STT / teleprompter."""
    _STATE.mkdir(parents=True, exist_ok=True)
    _PRIME.write_text(
        json.dumps(
            {
                "at": datetime.now(timezone.utc).isoformat(),
                "reason": "agent_channel_call",
            }
        ),
        encoding="utf-8",
    )
    # Also update UI immediately so user can greet without waiting for poll
    fall = "unknown"
    if _META.exists():
        try:
            fall = str(json.loads(_META.read_text(encoding="utf-8")).get("fall") or "unknown")
        except Exception:
            pass
    _write_primed_teleprompter(fall, "agent_channel_call")
    print("CALL_LISTEN_PRIME_REQUESTED")
    print("TELEPROMPTER PRIMED — hold greeting until then, then greet")
    return 0


def _spawn_detached(*, force: bool = False) -> int:
    """Idempotent arm: keep one listen + teleprompter for the whole session."""
    refused = _refuse_if_disabled(force=force)
    if refused is not None:
        return refused
    _STATE.mkdir(parents=True, exist_ok=True)

    live_pid = _living_meta_pid(_META)
    if live_pid:
        print("MODE: --listen-call (DETACHED)")
        print("CALL_LISTEN_ALREADY_ARMED")
        print(f"CALL_LISTEN_DETACHED pid={live_pid}")
        print(f"CALL_LISTEN_LOG {_LOG}")
        print("READY_FOR_CALL_AUDIO — transcript + live teleprompter (session keep-alive)", flush=True)
        print(f"TELEPROMPTER_FILE {_TP_LATEST}", flush=True)
        tp_pid = _living_meta_pid(_TP_UI_META)
        if tp_pid:
            print(f"TELEPROMPTER_UI_PID {tp_pid} (already running)", flush=True)
        else:
            _spawn_teleprompter_ui()
        return 0

    _LOG.write_text("", encoding="utf-8")
    if _STOP.exists():
        try:
            _STOP.unlink()
        except Exception:
            pass

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]

    log_f = open(_LOG, "a", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(_SKILL / "call_listen.py"), "--foreground"],
        cwd=str(_REPO),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=creationflags,
        close_fds=False if sys.platform == "win32" else True,
    )
    _write_meta({"pid": proc.pid, "detached": True, "session_keepalive": True})
    print("MODE: --listen-call (DETACHED)")
    print("CALL_LISTEN_ARMED")
    print(f"CALL_LISTEN_DETACHED pid={proc.pid}")
    print(f"CALL_LISTEN_LOG {_LOG}")
    print("READY_FOR_CALL_AUDIO — transcript + live teleprompter", flush=True)
    print(f"TELEPROMPTER_FILE {_TP_LATEST}", flush=True)
    _spawn_teleprompter_ui()
    return 0


def _pid_alive(pid: int) -> bool:
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            out = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return str(pid) in (out.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _living_meta_pid(meta_path: Path) -> int:
    if not meta_path.exists():
        return 0
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        pid = int(meta.get("pid") or 0)
        return pid if _pid_alive(pid) else 0
    except Exception:
        return 0


def _should_stop(_page, _markers: dict) -> bool:
    """Session keep-alive: only the stop file ends the listen process."""
    return _STOP.exists()


def run_foreground() -> int:
    sys.path.insert(0, str(_SKILL))
    from cdp_util import (
        call_markers,
        connect_browser,
        extract_fall_id,
        find_sprinklr_page,
        is_call_channel,
        load_cdp_endpoint,
    )

    cfg = _load_capture_config()
    path_mode = (cfg.get("capture_path") or "webrtc_hook").lower()
    language = cfg.get("stt_language") or "de"
    sys.path.insert(0, str(_SKILL))
    from stt_backend import backend_name, transcribe_wav

    stt_name = backend_name()
    whisper_ok = stt_name != "none"
    if not whisper_ok:
        _log(
            "WARN: No STT backend. Install vosk (preferred on locked PCs) or faster-whisper. "
            "uv pip install vosk"
        )
    else:
        _log(
            f"STT backend: {stt_name} language={language} "
            f"(German lock; dialect/accent/broken DE expected)"
        )
        try:
            from faster_whisper import WhisperModel
            from stt_backend import resolve_whisper_model_id, transcribe_wav as _tw

            mid = resolve_whisper_model_id(cfg)
            _log(f"STT acoustic model: {mid}")
            device = str(cfg.get("stt_device") or "cpu")
            ctype = str(cfg.get("stt_compute_type") or "int8")
            _log("STT: preloading acoustic model (may take ~1 min on CPU)…")
            model = WhisperModel(mid, device=device, compute_type=ctype)
            cache_key = f"_wmodel_{mid}_{device}_{ctype}"
            setattr(_tw, cache_key, model)
            _log("STT: preload OK")
        except Exception as e:
            _log(f"STT model resolve/preload warn: {e}")

    from greeting_gate import CustomerPhaseGate
    from teleprompter_display import TeleprompterDisplay

    gate = CustomerPhaseGate(cfg)
    trigger = getattr(gate, "trigger", "call_case")
    _log(
        f"Gate trigger={trigger} — "
        + (
            "opens on CHANNEL: CALL / call UI / --prime (not spoken greeting)."
            if trigger == "call_case"
            else (
                "opens after spoken o2 greeting (or timeout)."
                if trigger == "greeting"
                else "always open."
            )
        )
    )
    silence_s = float(cfg.get("utterance_silence_s", 1.4))
    min_utt = int(cfg.get("utterance_min_chars", 18))
    loopback_min_peak = float(cfg.get("loopback_min_peak", 0.0005))
    loopback_chunk_s = float(cfg.get("loopback_chunk_s", 2.0))
    loopback_device = (cfg.get("loopback_device") or "").strip() or None
    tp_enabled = bool(cfg.get("teleprompter_enabled", True))
    utt = UtteranceBuffer(silence_s=silence_s, min_chars=min_utt)
    display = TeleprompterDisplay(_TP_LATEST, _STATE)
    display.set_status("Session listen armed — waiting for CHANNEL: CALL")
    _log(
        f"Teleprompter {'ON' if tp_enabled else 'OFF'} "
        f"(silence={silence_s}s, min_chars={min_utt}, live_stt=ON)"
    )
    _log(
        f"Volume gate: loopback_min_peak={loopback_min_peak} "
        f"chunk={loopback_chunk_s}s (below = skip STT)"
    )

    _STATE.mkdir(parents=True, exist_ok=True)
    _CHUNKS.mkdir(parents=True, exist_ok=True)
    _write_meta({"foreground": True, "capture_path": path_mode})
    _log("CALL_LISTEN_START")
    print("CALL_LISTEN_FOREGROUND", flush=True)

    try:
        pw, browser, ep = connect_browser(load_cdp_endpoint())
    except Exception as e:
        _log(f"ERROR: CDP connect failed: {e}")
        print(f"ERROR: CDP connect failed: {e}", file=sys.stderr)
        return 2

    fall = "unknown"
    stt_missing_noted = False
    ended_reset_done = False
    last_status_log = 0.0
    no_audio_since = None
    try:
        while not _STOP.exists():
            page = find_sprinklr_page(browser)
            if not page:
                _log("Waiting for Sprinklr tab…")
                time.sleep(2)
                continue

            markers = call_markers(page)
            fid = extract_fall_id(page)
            if fid and fid != fall and fall != "unknown":
                fall = fid
                gate = CustomerPhaseGate(cfg)
                utt = UtteranceBuffer(silence_s=silence_s, min_chars=min_utt)
                display.reset(fall)
                ended_reset_done = False
                no_audio_since = None
                _write_meta({"fall": fall, "capture_path": path_mode, "gate_open": gate.open})
                _log(f"New Fall #{fall} — gate + utterance buffer reset")
            elif fid:
                fall = fid
                display.fall = fall
                _write_meta({"fall": fall, "capture_path": path_mode, "gate_open": gate.open})

            # Agent CHANNEL: CALL → --prime flag
            if _consume_prime_flag():
                _prime_gate(gate, fall, "agent_channel_call", display=display)

            if not is_call_channel(markers):
                _log("No CALL markers — waiting (EMAIL OK; session keep-alive)…")
                time.sleep(2)
                continue

            # CALL UI detected → prime customer STT / teleprompter (no spoken greeting needed)
            if not gate.open:
                reason = "im_gespraech" if markers.get("imGespraech") else "call_ui"
                _prime_gate(gate, fall, reason, display=display)

            if markers.get("imGespraech"):
                ended_reset_done = False

            # Call ended → reset gate for next call; do NOT exit (always-on session)
            if markers.get("anrufBeendet") and not markers.get("imGespraech"):
                if not ended_reset_done:
                    gate = CustomerPhaseGate(cfg)
                    utt = UtteranceBuffer(silence_s=silence_s, min_chars=min_utt)
                    ended_reset_done = True
                    no_audio_since = None
                    display.set_status("Anruf beendet — gate reset; waiting for next CALL")
                    _log("Anruf beendet — gate reset; listen stays armed")
                    _write_meta(
                        {
                            "fall": fall,
                            "capture_path": path_mode,
                            "gate_open": False,
                            "session_keepalive": True,
                        }
                    )
                time.sleep(1.0)
                continue

            if _should_stop(page, markers):
                _log("Stop condition (stop file)")
                break

            # Inject / poll WebRTC path
            if path_mode in ("webrtc_hook", "html_audio", "sprinklr_captions"):
                try:
                    page.evaluate(_INJECT_CAPTURE_JS)
                    polled = page.evaluate(_POLL_CHUNKS_JS) or {}
                    chunks = polled.get("chunks") or []
                    status = polled.get("status") or {}
                    tracks = int(status.get("tracks") or 0)
                    recording = bool(status.get("recording"))
                    now = time.time()
                    if recording and tracks > 0:
                        no_audio_since = None
                        if now - last_status_log >= 3.0:
                            _log(f"Recording… tracks={tracks} fall={fall} chunks={len(chunks)}")
                            last_status_log = now
                        display.set_status(
                            f"recording=yes tracks={tracks} chunks={len(chunks)} — LIVE updating…"
                        )
                    else:
                        if no_audio_since is None:
                            no_audio_since = now
                        wait_s = int(now - no_audio_since)
                        if now - last_status_log >= 3.0:
                            _log(
                                f"No remote audio yet fall={fall} "
                                f"recording={recording} tracks={tracks} waited={wait_s}s"
                            )
                            last_status_log = now
                        display.set_status(
                            f"recording={'yes' if recording else 'no'} tracks={tracks} "
                            f"— NO customer audio for {wait_s}s (WebRTC empty?)"
                        )
                        # Sprinklr often uses native VOIP (0 RTC tracks) — fall back to headset loopback
                        if wait_s >= 8:
                            _log(
                                "AUTO-FALLBACK capture_path=windows_loopback "
                                "(WebRTC tracks=0 — VOIP not in page)"
                            )
                            _set_capture_path("windows_loopback")
                            path_mode = "windows_loopback"
                            no_audio_since = None
                            display.set_status(
                                "FALLBACK: HyperX speaker loopback — listening to what you hear…"
                            )
                            continue
                    for ch in chunks:
                        b64 = ch.get("b64")
                        if not b64:
                            continue
                        try:
                            raw_path = _CHUNKS / f"{fall}_{ch.get('at', int(time.time()*1000))}.b64.txt"
                            raw_path.write_text(
                                b64[:80] + f"... len={len(b64)} fmt={ch.get('format')}",
                                encoding="utf-8",
                            )
                        except Exception:
                            pass
                        if whisper_ok:
                            text = _transcribe_chunk(ch, language=language, cfg=cfg)
                            if text:
                                # Always show raw STT in LIVE pane (parallel to speech)
                                if tp_enabled:
                                    display.append_live(text, tag="STT")
                                keep, evt = gate.filter(text)
                                if evt:
                                    _log(evt)
                                    if evt.startswith("CUSTOMER_PHASE_OPEN"):
                                        print("CUSTOMER_PHASE_OPEN", flush=True)
                                        _write_meta(
                                            {
                                                "fall": fall,
                                                "capture_path": path_mode,
                                                "gate_open": True,
                                                "gate_reason": gate.opened_reason,
                                            }
                                        )
                                if keep:
                                    from agent_fillers import filter_customer_speech

                                    keep2, skip_evt = filter_customer_speech(keep, cfg)
                                    if skip_evt:
                                        _log(skip_evt)
                                        if tp_enabled:
                                            display.append_live(keep, tag="filtered")
                                    keep = keep2
                                if keep:
                                    _append_brief(fall, keep, tag="[Kunde]")
                                    _log(f"STT[Kunde]: {keep[:120]}{'…' if len(keep) > 120 else ''}")
                                    print(f"CALL_BRIEF_UPDATE fall={fall}", flush=True)
                                    if tp_enabled and gate.open:
                                        display.append_live(keep, tag="Kunde")
                                        utt.push(keep)
                        elif not stt_missing_noted:
                            _append_brief(
                                fall,
                                "[STT unavailable — install vosk or faster-whisper; audio capture still armed]",
                            )
                            display.set_status("STT unavailable — install vosk or faster-whisper")
                            stt_missing_noted = True
                except Exception as e:
                    _log(f"webrtc poll error: {e}")
                    display.set_status(f"webrtc poll error: {e}")

            # Loopback: capture headset output (customer voice you hear)
            if path_mode == "windows_loopback":
                wav = _try_loopback_chunk(
                    loopback_chunk_s,
                    min_peak=loopback_min_peak,
                    preferred_device=loopback_device,
                )
                if wav and whisper_ok:
                    text = transcribe_wav(wav, language=language, cfg=cfg)
                    if text:
                        no_audio_since = None
                        display.set_status("loopback HyperX — LIVE STT updating…")
                        if tp_enabled:
                            display.append_live(text, tag="STT")
                        keep, evt = gate.filter(text)
                        if evt:
                            _log(evt)
                            if evt.startswith("CUSTOMER_PHASE_OPEN"):
                                print("CUSTOMER_PHASE_OPEN", flush=True)
                        if keep:
                            from agent_fillers import filter_customer_speech

                            keep2, skip_evt = filter_customer_speech(keep, cfg)
                            if skip_evt:
                                _log(skip_evt)
                                if tp_enabled:
                                    display.append_live(keep, tag="filtered")
                            keep = keep2
                        if keep:
                            _append_brief(fall, keep, tag="[Kunde]")
                            _log(f"STT(loop)[Kunde]: {keep[:120]}")
                            print(f"CALL_BRIEF_UPDATE fall={fall}", flush=True)
                            if tp_enabled and gate.open:
                                display.append_live(keep, tag="Kunde")
                                utt.push(keep)
                    else:
                        display.set_status("loopback active — waiting for speech in headset…")
                elif not wav:
                    display.set_status(
                        "SILENT loopback (HyperX+ASUS peak=0) — "
                        "play Sprinklr on HyperX Speakers, unmute, disable exclusive mode"
                    )
                # Fire SAY THIS on pause (loopback path skips the shared sleep below)
                if tp_enabled and gate.open and utt.ready_to_fire():
                    customer_utt = utt.consume()
                    try:
                        _fire_teleprompter(fall, customer_utt, cfg, display=display)
                    except Exception as e:
                        _log(f"teleprompter error: {e}")
                continue

            # Fire teleprompter ASAP after short customer pause
            if tp_enabled and gate.open and utt.ready_to_fire():
                customer_utt = utt.consume()
                try:
                    _fire_teleprompter(fall, customer_utt, cfg, display=display)
                except Exception as e:
                    _log(f"teleprompter error: {e}")

            time.sleep(0.35)

        try:
            page = find_sprinklr_page(browser)
            if page:
                page.evaluate(_STOP_RECORDER_JS)
        except Exception:
            pass
        _log("CALL_LISTEN_STOPPED")
        print("CALL_LISTEN_STOPPED", flush=True)
        return 0
    finally:
        try:
            pw.stop()
        except Exception:
            pass


def cmd_stop() -> int:
    _STATE.mkdir(parents=True, exist_ok=True)
    _STOP.write_text("stop", encoding="utf-8")
    print("CALL_LISTEN_STOP_REQUESTED")
    # Kill listen + teleprompter UI
    for meta_path, label in ((_META, "listen"), (_TP_UI_META, "teleprompter_ui")):
        if not meta_path.exists():
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            pid = int(meta.get("pid") or 0)
            if pid and sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                print(f"STOPPED {label} pid={pid}")
        except Exception as e:
            print(f"[WARN] stop {label}: {e}")
    return 0


def cmd_status() -> int:
    if _META.exists():
        print(_META.read_text(encoding="utf-8"))
    else:
        print("NO_CALL_LISTEN_META")
    brief_files = sorted(_STATE.glob("call_brief_*.txt"))
    for b in brief_files[-5:]:
        print(f"BRIEF {b.name} bytes={b.stat().st_size}")
    if _TP_LATEST.exists():
        print("TELEPROMPTER_LATEST:")
        print(_TP_LATEST.read_text(encoding="utf-8", errors="replace")[:500])
    if _LOG.exists():
        lines = _LOG.read_text(encoding="utf-8", errors="replace").splitlines()
        print("LOG_TAIL:")
        for line in lines[-15:]:
            print(line)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="store_true", help="Detach listen watch")
    ap.add_argument("--foreground", action="store_true", help="Run listen loop in this process")
    ap.add_argument("--stop", action="store_true", help="Stop listen watch")
    ap.add_argument("--status", action="store_true", help="Show listen status / brief files")
    ap.add_argument(
        "--prime",
        action="store_true",
        help="CHANNEL: CALL — open customer STT / teleprompter (no spoken greeting needed)",
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Bypass enabled=false (debug only; do not use from agent while parked)",
    )
    args = ap.parse_args()

    if args.stop:
        return cmd_stop()
    if args.status:
        return cmd_status()
    if args.prime:
        refused = _refuse_if_disabled(force=args.force)
        if refused is not None:
            return refused
        return cmd_prime()
    if args.arm:
        return _spawn_detached(force=args.force)
    if args.foreground:
        refused = _refuse_if_disabled(force=args.force)
        if refused is not None:
            return refused
        return run_foreground()

    # default: arm detached
    return _spawn_detached(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())
