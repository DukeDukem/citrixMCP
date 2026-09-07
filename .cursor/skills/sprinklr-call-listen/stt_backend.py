"""STT backends for call_listen: faster-whisper (preferred) or vosk (fallback)."""
from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Optional

_REPO = Path(__file__).resolve().parent.parent.parent.parent
_MODELS = _REPO / ".cursor" / "state" / "stt_models"


def whisper_available() -> bool:
    try:
        import av  # noqa: F401
        import faster_whisper  # noqa: F401

        return True
    except Exception:
        return False


def vosk_available() -> bool:
    try:
        import vosk  # noqa: F401

        return True
    except Exception:
        return False


def backend_name() -> str:
    if whisper_available():
        return "faster-whisper"
    if vosk_available():
        return "vosk"
    return "none"


def _ensure_vosk_model(lang: str = "de") -> Optional[Path]:
    """Download small German model once into .cursor/state/stt_models/."""
    import urllib.request
    import zipfile

    _MODELS.mkdir(parents=True, exist_ok=True)
    # vosk-model-small-de-0.15
    name = "vosk-model-small-de-0.15"
    dest = _MODELS / name
    if dest.exists():
        return dest
    url = f"https://alphacephei.com/vosk/models/{name}.zip"
    zip_path = _MODELS / f"{name}.zip"
    try:
        print(f"STT: downloading vosk model {name}…", flush=True)
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(_MODELS)
        try:
            zip_path.unlink()
        except Exception:
            pass
        if dest.exists():
            return dest
    except Exception as e:
        print(f"STT: vosk model download failed: {e}", flush=True)
    return None


def transcribe_wav(wav_path: Path, language: str = "de") -> Optional[str]:
    if whisper_available():
        try:
            from faster_whisper import WhisperModel

            model = getattr(transcribe_wav, "_wmodel", None)
            if model is None:
                model = WhisperModel("small", device="cpu", compute_type="int8")
                setattr(transcribe_wav, "_wmodel", model)
            segments, _info = model.transcribe(str(wav_path), language=language, vad_filter=True)
            parts = [s.text.strip() for s in segments if s.text and s.text.strip()]
            return " ".join(parts).strip() or None
        except Exception as e:
            print(f"STT whisper failed: {e}", flush=True)

    if vosk_available():
        try:
            from vosk import KaldiRecognizer, Model, SetLogLevel

            SetLogLevel(-1)
            model_path = getattr(transcribe_wav, "_vmodel_path", None)
            if model_path is None:
                model_path = _ensure_vosk_model("de")
                setattr(transcribe_wav, "_vmodel_path", model_path)
            if not model_path:
                return None
            model = getattr(transcribe_wav, "_vmodel", None)
            if model is None:
                model = Model(str(model_path))
                setattr(transcribe_wav, "_vmodel", model)

            with wave.open(str(wav_path), "rb") as wf:
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2:
                    return None
                rec = KaldiRecognizer(model, wf.getframerate())
                rec.SetWords(False)
                parts: list[str] = []
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    if rec.AcceptWaveform(data):
                        j = json.loads(rec.Result())
                        t = (j.get("text") or "").strip()
                        if t:
                            parts.append(t)
                final = json.loads(rec.FinalResult())
                t = (final.get("text") or "").strip()
                if t:
                    parts.append(t)
                return " ".join(parts).strip() or None
        except Exception as e:
            print(f"STT vosk failed: {e}", flush=True)

    return None


def webm_to_wav_ffmpeg(webm: Path, wav: Path) -> bool:
    """Convert webm→wav via ffmpeg CLI if present (avoids blocked PyAV)."""
    import shutil
    import subprocess

    ff = shutil.which("ffmpeg")
    if not ff:
        return False
    try:
        r = subprocess.run(
            [
                ff,
                "-y",
                "-i",
                str(webm),
                "-ac",
                "1",
                "-ar",
                "16000",
                str(wav),
            ],
            capture_output=True,
            timeout=60,
        )
        return r.returncode == 0 and wav.exists()
    except Exception:
        return False
