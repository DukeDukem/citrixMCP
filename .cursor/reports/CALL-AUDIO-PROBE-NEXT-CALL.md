# Live CALL audio probe — run on next real call

## Why

Capture path is pre-locked to **`webrtc_hook`** in  
[`.cursor/skills/sprinklr-call-listen/capture_path.json`](../skills/sprinklr-call-listen/capture_path.json).  
Confirm remote audio tracks during a live **Im Gespräch** session.

## On next CALL (while customer is speaking)

```powershell
Set-Location "c:\Users\PC ENTER\Desktop\Citrix"
uv run python .cursor/skills/sprinklr-call-listen/probe_call_audio.py --lock
```

Expect:
- `PROBE_OK fall=…`
- `PROBE_REPORT .cursor/reports/call-audio-probe-{FALL}.json`
- `RECOMMENDED_CAPTURE_PATH …`
- `CAPTURE_PATH_LOCKED`

### Interpret

| Probe field | Action |
|-------------|--------|
| `remoteAudioTracks` > 0 | Keep / lock **`webrtc_hook`** |
| `audioElements` with `hasSrcObject` | **`html_audio`** OK (same inject) |
| `captionHints` non-empty | Consider **`sprinklr_captions`** later |
| Live call but tracks = 0 | Re-lock with path **`windows_loopback`** (install `sounddevice`) |

Also ensure listen is armed:

```powershell
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm
```

Install STT once (vosk preferred — PyAV/faster-whisper often blocked by AppLocker):

```powershell
uv pip install vosk
```

## Offline / partial probe

A probe may run while **Disposition** is open but **not** Im Gespräch (`remoteAudioTracks=0`).  
Keep `webrtc_hook`; re-run `--lock` during live speech to confirm tracks. If still 0, set `capture_path` to `windows_loopback`.
