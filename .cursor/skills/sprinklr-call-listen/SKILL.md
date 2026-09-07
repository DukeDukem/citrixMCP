# sprinklr-call-listen

Local CALL auto-listen: capture Sprinklr call audio → **faster-whisper** STT → voice brief text for the agent.

The Cursor agent cannot hear audio in chat. This skill produces a transcript file the agent reads as the voice brief.

## Commands

```powershell
# During / after CHANNEL: CALL — start detached listen
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm

# Probe audio sources (run once on a live CALL, then --lock)
uv run python .cursor/skills/sprinklr-call-listen/probe_call_audio.py
uv run python .cursor/skills/sprinklr-call-listen/probe_call_audio.py --lock

# Status / stop
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --status
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --stop
```

## Outputs

| Path | Purpose |
|------|---------|
| `.cursor/state/call_brief_{FALL}.txt` | Rolling German transcript (voice brief) |
| `.cursor/state/call_audio_chunks/` | Raw webm/wav chunks (local only) |
| `.cursor/state/call_listen.log` | Heartbeat / STT lines |
| `.cursor/state/call_listen.json` | Detached watch meta (pid) |
| `.cursor/reports/call-audio-probe-{FALL}.json` | Probe report |
| `capture_path.json` | Locked capture mode (`webrtc_hook` default) |

## Capture path

Default: **`webrtc_hook`** (RTCPeerConnection remote tracks + `<audio srcObject>`).  
Fallback (after failed live probe): **`windows_loopback`** (needs `sounddevice`).

## STT install

Primary: **faster-whisper** (after Windows Reputation protection allows PyAV). Fallback: **vosk**.

```powershell
uv pip install faster-whisper vosk
```

Optional loopback fallback:

```powershell
uv pip install sounddevice numpy
```

## Agent flow

1. `CHANNEL: CALL` → run `call_listen.py --arm`
2. Say: Listening — transcript building in `call_brief_{FALL}.txt`
3. On user `BRIEF` / enough transcript / Disposition: read brief → CALL handling pack
4. Manual paste still overrides
5. On LF / `STOP LISTEN` / DONE: `call_listen.py --stop` (DONE also kills via done_for_today)

## Post-greeting capture (customer rant)

Calls typically start with your line:

> Willkommen bei o2, Lukas ist mein Name, was kann ich für Sie tun?

Listen **discards** STT until that greeting is recognized (or **25s** timeout if your mic is not in the captured stream). After that, lines are tagged `[Kunde]` in `call_brief_{FALL}.txt`.

Config: `capture_path.json` → `post_greeting_only`, `agent_greeting_fragments`, `gate_timeout_s`.
