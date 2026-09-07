# sprinklr-call-listen

Local CALL auto-listen: capture Sprinklr call audio → **faster-whisper** STT → voice brief + **live teleprompter** for the agent.

## Status: PARKED (2026-09-07)

**Do not use in live Care until reactivated.**

| Switch | File | Value while parked |
|--------|------|--------------------|
| Master | `capture_path.json` → **`enabled`** | **`false`** |
| Teleprompter | `capture_path.json` → **`teleprompter_enabled`** | **`false`** |

`--arm` / `--prime` / `--foreground` print **`CALL_LISTEN_DISABLED`** and exit.  
CALL cases: typed **BRIEF** only (see `sprinklr-call-vs-email.mdc`).

### Reactivate later

1. Set `enabled=true` and `teleprompter_enabled=true` in `capture_path.json`
2. Optionally swap to a better STT model (`stt_model` / `stt_prefer_german_finetune`)
3. `uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm`
4. On CHANNEL: CALL → `--prime`

Debug override (not for agents): `--force`

### Kept base (good foundation)

- Capture: **windows_loopback** / HyperX Speakers (`soundcard`)
- Live STT default: stock **faster-whisper turbo** + `language=de` (German CT2 too slow on CPU)
- Volume gate `loopback_min_peak=0.0005`
- Field notes: `.cursor/knowledge/call-stt-field-notes.md`

---

**Honest limit:** The Cursor agent cannot hear audio in chat. This skill produces transcript + teleprompter files the agent/user reads.

## Commands (when enabled)

```powershell
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --arm
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --prime
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --status
uv run python .cursor/skills/sprinklr-call-listen/call_listen.py --stop
```

## Gate / STT config

See `capture_path.json`. German CT2 install helper: `install_german_stt.py`.

| Path | Purpose |
|------|---------|
| `.cursor/state/call_brief_{FALL}.txt` | `[Kunde]` transcript after prime |
| `.cursor/state/call_teleprompter_latest.txt` | LIVE STT + SAY THIS |
| `.cursor/state/call_listen.log` | Heartbeat / peaks / STT |
