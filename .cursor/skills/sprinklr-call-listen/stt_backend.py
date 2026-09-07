"""STT backends for call_listen: faster-whisper (preferred) or vosk (fallback).

Always biased to **German (de)** — including dialect, accent, and non-native / broken German.
Default acoustic model: German-tuned Whisper large-v3-turbo (CTranslate2 / faster-whisper).
"""
from __future__ import annotations

import json
import wave
from pathlib import Path
from typing import Any, Optional

_REPO = Path(__file__).resolve().parent.parent.parent.parent
_MODELS = _REPO / ".cursor" / "state" / "stt_models"

# Pre-converted faster-whisper CT2 (primeline turbo German lineage)
_DEFAULT_HF_GERMAN_CT2 = "GalaktischeGurke/primeline-whisper-large-v3-german-ct2"
_LOCAL_GERMAN_DIRNAME = "whisper-large-v3-turbo-german-ct2"  # local folder name (CT2 on disk)

# Bias Whisper toward o2 Care German + imperfect speech (accents, dialect, L2)
_DEFAULT_DE_PROMPT = (
    "o2 Kundengespräch auf Deutsch. "
    "Der Kunde spricht oft mit Akzent, Dialekt oder gebrochenem Deutsch — "
    "schreibe trotzdem Deutsch (nicht Englisch). "
    "Wenn der Kunde eine Kundennummer, Handynummer oder IBAN Ziffer für Ziffer nennt, "
    "transkribiere die Ziffern möglichst einzeln (null eins zwei …). "
    "Häufige Themen: Rechnung, Vertrag, Tarif, Handy, SIM-Karte, Internet, "
    "Rufnummer, Kündigung, Gutschrift, Erstattung, Zahlungsart, PIN, PUK, Mein o2, "
    "Zahlung, Lastschrift."
)


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


def _normalize_lang(language: str | None) -> str:
    lang = (language or "de").strip().lower()
    if lang in ("de", "de-de", "german", "deutsch", "ger"):
        return "de"
    if lang in ("auto", "", "detect"):
        return "de"
    return lang


def _looks_like_ct2_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    # CTranslate2 whisper dirs usually contain model.bin
    return (path / "model.bin").exists() or any(path.glob("*.bin"))


def ensure_german_ct2_model(
    hf_repo: str | None = None,
    local_dir: Path | None = None,
) -> Optional[Path]:
    """
    Ensure German turbo CT2 model is on disk (download once from Hugging Face).
    Returns local path or None on failure.
    """
    dest = local_dir or (_MODELS / _LOCAL_GERMAN_DIRNAME)
    if _looks_like_ct2_dir(dest):
        return dest
    repo = (hf_repo or _DEFAULT_HF_GERMAN_CT2).strip()
    try:
        from huggingface_hub import snapshot_download

        _MODELS.mkdir(parents=True, exist_ok=True)
        print(f"STT: downloading German CT2 model {repo} → {dest} …", flush=True)
        snapshot_download(repo_id=repo, local_dir=str(dest))
        if _looks_like_ct2_dir(dest):
            print(f"STT: German CT2 ready at {dest}", flush=True)
            return dest
        print(f"STT: download finished but model.bin missing under {dest}", flush=True)
    except Exception as e:
        print(f"STT: German CT2 download failed: {e}", flush=True)
    return None


def resolve_whisper_model_id(cfg: dict[str, Any] | None = None) -> str:
    """
    Pick acoustic model:
    1) explicit stt_model_path / existing local German CT2
    2) auto-download German turbo CT2 (if stt_prefer_german_finetune true)
    3) stt_model size name (small/medium/turbo/…)
    """
    cfg = cfg or {}
    explicit = (cfg.get("stt_model_path") or "").strip()
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = _REPO / p
        if _looks_like_ct2_dir(p):
            return str(p)

    local = _MODELS / _LOCAL_GERMAN_DIRNAME
    prefer = bool(cfg.get("stt_prefer_german_finetune", True))
    if prefer:
        if _looks_like_ct2_dir(local):
            return str(local)
        got = ensure_german_ct2_model(cfg.get("stt_hf_repo") or _DEFAULT_HF_GERMAN_CT2, local)
        if got:
            return str(got)

    return str(cfg.get("stt_model") or "turbo")


def transcribe_wav(
    wav_path: Path,
    language: str = "de",
    cfg: dict[str, Any] | None = None,
) -> Optional[str]:
    cfg = cfg or {}
    language = _normalize_lang(cfg.get("stt_language") or language)
    model_id = resolve_whisper_model_id(cfg)
    initial_prompt = (cfg.get("stt_initial_prompt") or _DEFAULT_DE_PROMPT).strip()
    vad_filter = bool(cfg.get("stt_vad_filter", False))
    beam_size = int(cfg.get("stt_beam_size") or 5)
    best_of = int(cfg.get("stt_best_of") or 5)
    temperature = float(cfg.get("stt_temperature") or 0.0)
    condition_prev = bool(cfg.get("stt_condition_on_previous_text", False))
    compute_type = str(cfg.get("stt_compute_type") or "int8")
    device = str(cfg.get("stt_device") or "cpu")

    if whisper_available():
        try:
            from faster_whisper import WhisperModel

            cache_key = f"_wmodel_{model_id}_{device}_{compute_type}"
            model = getattr(transcribe_wav, cache_key, None)
            if model is None:
                print(f"STT: loading WhisperModel({model_id!r}) device={device} {compute_type}", flush=True)
                model = WhisperModel(model_id, device=device, compute_type=compute_type)
                setattr(transcribe_wav, cache_key, model)

            kwargs: dict[str, Any] = {
                "language": language,
                "task": "transcribe",
                "vad_filter": vad_filter,
                "beam_size": beam_size,
                "best_of": best_of,
                "temperature": temperature,
                "condition_on_previous_text": condition_prev,
                "word_timestamps": False,
            }
            if initial_prompt:
                kwargs["initial_prompt"] = initial_prompt

            segments, info = model.transcribe(str(wav_path), **kwargs)
            try:
                det = getattr(info, "language", None)
                if det and str(det).lower() not in ("de", "german"):
                    print(f"STT warn: detected lang={det} but forced de", flush=True)
            except Exception:
                pass
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
