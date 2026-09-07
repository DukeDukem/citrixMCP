"""
CALL listen watch: capture Sprinklr call audio → local faster-whisper → call_brief_{FALL}.txt

Usage:
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --foreground
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --stop
  uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --status

Agent: after CHANNEL: CALL, run --arm (detached). Read .cursor/state/call_brief_{FALL}.txt
as voice brief (or when user types BRIEF). STOP LISTEN / LF / DONE stops the watch.
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
_CAPTURE_PATH = _SKILL / "capture_path.json"

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
      const flushEverySec = 2.5;
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
        "capture_path": "webrtc_hook",
        "fallback": "windows_loopback",
        "stt_language": "de",
    }


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


def _transcribe_chunk(ch: dict, language: str = "de") -> Optional[str]:
    sys.path.insert(0, str(_SKILL))
    from stt_backend import backend_name, transcribe_wav, webm_to_wav_ffmpeg

    b64 = ch.get("b64")
    if not b64:
        return None
    fmt = (ch.get("format") or "").lower()
    if fmt == "pcm_s16le" or ch.get("sampleRate"):
        wav = _pcm_b64_to_wav(b64, int(ch.get("sampleRate") or 16000))
        return transcribe_wav(wav, language=language)

    # Legacy webm path
    _CHUNKS.mkdir(parents=True, exist_ok=True)
    webm = _CHUNKS / f"chunk_{int(time.time() * 1000)}.webm"
    webm.write_bytes(base64.b64decode(b64))
    wav = _CHUNKS / (webm.stem + ".wav")
    if webm_to_wav_ffmpeg(webm, wav):
        return transcribe_wav(wav, language=language)
    return transcribe_wav(webm, language=language)  # may fail without av


def _try_loopback_chunk(seconds: float = 3.0) -> Optional[Path]:
    """Optional WASAPI loopback via sounddevice; returns wav path or None."""
    try:
        import numpy as np  # type: ignore
        import sounddevice as sd  # type: ignore
    except ImportError:
        return None

    _CHUNKS.mkdir(parents=True, exist_ok=True)
    fs = 16000
    try:
        # loopback device: hostapi WASAPI often exposed as specialized devices
        devices = sd.query_devices()
        loop_idx = None
        for i, d in enumerate(devices):
            name = (d.get("name") or "").lower()
            if "loopback" in name or "stereo mix" in name or "what u hear" in name:
                loop_idx = i
                break
        if loop_idx is None:
            # Try Wasapi loopback default
            try:
                loop_idx = sd.default.device[0]
            except Exception:
                return None
        recording = sd.rec(
            int(seconds * fs),
            samplerate=fs,
            channels=1,
            dtype="float32",
            device=loop_idx,
        )
        sd.wait()
        pcm = np.clip(recording.flatten(), -1, 1)
        wav_path = _CHUNKS / f"loop_{int(time.time() * 1000)}.wav"
        with wave.open(str(wav_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(fs)
            w.writeframes((pcm * 32767).astype("int16").tobytes())
        return wav_path
    except Exception as e:
        _log(f"loopback capture failed: {e}")
        return None


def _spawn_detached() -> int:
    _STATE.mkdir(parents=True, exist_ok=True)
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
    _write_meta({"pid": proc.pid, "detached": True})
    print("MODE: --listen-call (DETACHED)")
    print(f"CALL_LISTEN_ARMED")
    print(f"CALL_LISTEN_DETACHED pid={proc.pid}")
    print(f"CALL_LISTEN_LOG {_LOG}")
    print("READY_FOR_CALL_AUDIO — transcript builds in .cursor/state/call_brief_{FALL}.txt", flush=True)
    return 0


def _should_stop(page, markers: dict) -> bool:
    if _STOP.exists():
        return True
    # Stop when call clearly ended and no longer in conversation
    if markers.get("anrufBeendet") and not markers.get("imGespraech"):
        # disposition may still be open — keep listening while disposition visible? Plan: stop on Anruf beendet
        return True
    return False


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
        _log(f"STT backend: {stt_name}")

    from greeting_gate import CustomerPhaseGate

    gate = CustomerPhaseGate(cfg)
    _log(
        "Post-greeting gate ON — brief keeps customer speech after "
        "'Willkommen bei o2, Lukas ist mein Name…' (or gate timeout)."
        if gate.enabled
        else "Post-greeting gate OFF — keeping all STT."
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
    try:
        while not _STOP.exists():
            page = find_sprinklr_page(browser)
            if not page:
                _log("Waiting for Sprinklr tab…")
                time.sleep(2)
                continue

            markers = call_markers(page)
            fid = extract_fall_id(page)
            if fid and fid != fall:
                fall = fid
                gate = CustomerPhaseGate(cfg)  # new case → wait for greeting again
                _write_meta({"fall": fall, "capture_path": path_mode, "gate_open": gate.open})
                _log(f"New Fall #{fall} — greeting gate reset")
            elif fid:
                fall = fid
                _write_meta({"fall": fall, "capture_path": path_mode, "gate_open": gate.open})

            if not is_call_channel(markers):
                _log("No CALL markers yet — waiting (EMAIL cases ignored)…")
                time.sleep(2)
                continue

            if _should_stop(page, markers):
                _log("Stop condition (Anruf beendet or stop file)")
                break

            # Inject / poll WebRTC path
            if path_mode in ("webrtc_hook", "html_audio", "sprinklr_captions"):
                try:
                    page.evaluate(_INJECT_CAPTURE_JS)
                    polled = page.evaluate(_POLL_CHUNKS_JS) or {}
                    chunks = polled.get("chunks") or []
                    status = polled.get("status") or {}
                    if status.get("recording"):
                        _log(f"Recording… tracks={status.get('tracks')} fall={fall}")
                    for ch in chunks:
                        b64 = ch.get("b64")
                        if not b64:
                            continue
                        # Persist raw chunk meta
                        try:
                            raw_path = _CHUNKS / f"{fall}_{ch.get('at', int(time.time()*1000))}.b64.txt"
                            raw_path.write_text(b64[:80] + f"... len={len(b64)} fmt={ch.get('format')}", encoding="utf-8")
                        except Exception:
                            pass
                        if whisper_ok:
                            text = _transcribe_chunk(ch, language=language)
                            if text:
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
                                    _append_brief(fall, keep, tag="[Kunde]")
                                    _log(f"STT[Kunde]: {keep[:120]}{'…' if len(keep) > 120 else ''}")
                                    print(f"CALL_BRIEF_UPDATE fall={fall}", flush=True)
                        elif not stt_missing_noted:
                            _append_brief(
                                fall,
                                "[STT unavailable — install vosk or faster-whisper; audio capture still armed]",
                            )
                            stt_missing_noted = True
                except Exception as e:
                    _log(f"webrtc poll error: {e}")

            # Loopback fallback mode or webrtc producing nothing for a while
            if path_mode == "windows_loopback":
                wav = _try_loopback_chunk(3.0)
                if wav and whisper_ok:
                    text = transcribe_wav(wav, language=language)
                    if text:
                        keep, evt = gate.filter(text)
                        if evt:
                            _log(evt)
                            if evt.startswith("CUSTOMER_PHASE_OPEN"):
                                print("CUSTOMER_PHASE_OPEN", flush=True)
                        if keep:
                            _append_brief(fall, keep, tag="[Kunde]")
                            _log(f"STT(loop)[Kunde]: {keep[:120]}")
                            print(f"CALL_BRIEF_UPDATE fall={fall}", flush=True)

            time.sleep(1.0)

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
    # Also try kill via meta pid
    if _META.exists():
        try:
            meta = json.loads(_META.read_text(encoding="utf-8"))
            pid = int(meta.get("pid") or 0)
            if pid and sys.platform == "win32":
                subprocess.run(
                    ["taskkill", "/PID", str(pid), "/T", "/F"],
                    capture_output=True,
                    timeout=15,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                print(f"STOPPED pid={pid}")
        except Exception as e:
            print(f"[WARN] stop kill: {e}")
    return 0


def cmd_status() -> int:
    if _META.exists():
        print(_META.read_text(encoding="utf-8"))
    else:
        print("NO_CALL_LISTEN_META")
    brief_files = sorted(_STATE.glob("call_brief_*.txt"))
    for b in brief_files[-5:]:
        print(f"BRIEF {b.name} bytes={b.stat().st_size}")
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
    args = ap.parse_args()

    if args.stop:
        return cmd_stop()
    if args.status:
        return cmd_status()
    if args.arm:
        return _spawn_detached()
    if args.foreground:
        return run_foreground()

    # default: arm detached
    return _spawn_detached()


if __name__ == "__main__":
    raise SystemExit(main())
