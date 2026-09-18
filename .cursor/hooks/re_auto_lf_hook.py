#!/usr/bin/env python3
"""Text/transcript hook: after full 7-step RE → spawn auto_lf_after_re once.

Cursor stop payloads often have text_len=0 but include transcript_path.
afterAgentResponse usually has text — use both. Never audio.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_STATE = _REPO / ".cursor" / "state"
_LOG = _STATE / "re_auto_lf_hook.log"
_DEBOUNCE = _STATE / "re_auto_lf_debounce.json"
_LATEST_RE = _STATE / "latest_re_visible.md"
_SESSION = _STATE / "email_session_active.json"
_DONE = _STATE / "auto_lf_done.json"
_EXTRACT_READY = _STATE / "extract_ready.json"
_PAYLOAD_DUMP = _STATE / "re_auto_lf_last_payload.json"
_DEBOUNCE_SECONDS = 15.0

_SECTION7 = (
    re.compile(r"(?mi)7\.\s*Summary of response"),
    re.compile(r"(?mi)Summary of response\s*\(EN\)"),
)
_DONE_MARK = (
    re.compile(r"(?mi)7-step\s+complete"),
    re.compile(r"(?mi)Auto-LF\s+starts\s+after\s+this\s+message"),
)
_SECTION1 = (re.compile(r"(?mi)1\.\s*Customer(?:\s+case)?\s+summary"),)
_SECTION6 = (re.compile(r"(?mi)6\.\s*Your response to customer"),)
_CASE_RE = re.compile(r"Fall\s*#\s*(\d{5,})", re.I)


def _log(msg: str) -> None:
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with _LOG.open("a", encoding="utf-8") as f:
            f.write(f"{ts} {msg}\n")
    except Exception:
        pass


def _ok() -> int:
    try:
        sys.stdout.write("{}\n")
        sys.stdout.flush()
    except Exception:
        pass
    return 0


def _any(text: str, pats: tuple[re.Pattern, ...]) -> bool:
    return bool(text) and any(p.search(text) for p in pats)


def _session_active() -> bool:
    if not _SESSION.exists():
        return False
    try:
        return bool(json.loads(_SESSION.read_text(encoding="utf-8")).get("active"))
    except Exception:
        return False


def _digits(case_id: str) -> str:
    return re.sub(r"\D", "", case_id or "")


def _case_from_text(text: str) -> str:
    m = _CASE_RE.search(text or "")
    return f"#{m.group(1)}" if m else ""


def _already_filed(case_id: str) -> bool:
    dig = _digits(case_id)
    if not dig:
        return False
    if _DONE.exists():
        try:
            done = json.loads(_DONE.read_text(encoding="utf-8"))
            if _digits(str(done.get("case_id") or "")) == dig:
                if time.time() - _DONE.stat().st_mtime < 3600:
                    return True
        except Exception:
            pass
    speichern = _STATE / "lf_speichern_pending.json"
    if speichern.exists():
        try:
            data = json.loads(speichern.read_text(encoding="utf-8"))
            if _digits(str(data.get("case_id") or "")) == dig:
                return True
        except Exception:
            pass
    return False


def _pending_case_needing_lf() -> str:
    if not _EXTRACT_READY.exists():
        return ""
    try:
        data = json.loads(_EXTRACT_READY.read_text(encoding="utf-8"))
    except Exception:
        return ""
    case_id = str(data.get("case_id") or "")
    if not case_id:
        return ""
    if str(data.get("channel") or "").upper() == "CALL":
        return ""
    if _already_filed(case_id):
        return ""
    return case_id if case_id.startswith("#") else f"#{_digits(case_id)}"


def _is_full_re(text: str) -> bool:
    if not text:
        return False
    if _any(text, _DONE_MARK):
        return True
    if _any(text, _SECTION7) and (_any(text, _SECTION1) or _any(text, _SECTION6)):
        return True
    return False


def _walk_strings(obj: object, out: list[str], depth: int = 0) -> None:
    if depth > 12:
        return
    if isinstance(obj, str):
        if len(obj.strip()) >= 40:
            out.append(obj)
        return
    if isinstance(obj, dict):
        for v in obj.values():
            _walk_strings(v, out, depth + 1)
        return
    if isinstance(obj, list):
        for item in obj:
            _walk_strings(item, out, depth + 1)


def _extract_text(payload: dict) -> str:
    for key in (
        "text",
        "response",
        "message",
        "final_text",
        "assistant_message",
        "content",
        "output",
        "agent_response",
        "completion",
        "reply",
    ):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val
        if isinstance(val, list):
            parts: list[str] = []
            for item in val:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    t = item.get("text") or item.get("content") or ""
                    if isinstance(t, str):
                        parts.append(t)
            joined = "\n".join(parts).strip()
            if joined:
                return joined
    for nest in ("data", "result", "payload", "body"):
        sub = payload.get(nest)
        if isinstance(sub, dict):
            got = _extract_text(sub)
            if got:
                return got
    candidates: list[str] = []
    _walk_strings(payload, candidates)
    best = ""
    for s in candidates:
        if _is_full_re(s) and len(s) > len(best):
            best = s
    return best


def _debounce(case_id: str = "") -> bool:
    now = time.time()
    try:
        _STATE.mkdir(parents=True, exist_ok=True)
        if _DEBOUNCE.exists():
            data = json.loads(_DEBOUNCE.read_text(encoding="utf-8"))
            same = (
                _digits(str(data.get("case_id") or "")) == _digits(case_id)
                if case_id
                else True
            )
            if same and now - float(data.get("at", 0)) < _DEBOUNCE_SECONDS:
                return False
        _DEBOUNCE.write_text(
            json.dumps({"at": now, "case_id": case_id or ""}, indent=2),
            encoding="utf-8",
        )
        return True
    except Exception:
        return True


def _resolve_transcript_file(transcript_path: str) -> Path | None:
    """Cursor may pass a .jsonl file OR a conversation directory containing it."""
    if not transcript_path:
        return None
    p = Path(transcript_path)
    if p.is_file() and p.suffix.lower() == ".jsonl":
        return p
    if p.is_dir():
        # Prefer <dirname>/<dirname>.jsonl
        candidate = p / f"{p.name}.jsonl"
        if candidate.is_file():
            return candidate
        jsonls = sorted(p.glob("*.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
        if jsonls:
            return jsonls[0]
    # Truncated path from dump — try adding .jsonl
    if not p.suffix:
        as_file = Path(str(p) + ".jsonl")
        if as_file.is_file():
            return as_file
        if p.is_dir() or Path(str(p)).exists():
            pass
    return None


def _assistant_texts_from_jsonl(path: Path, max_lines: int = 80) -> list[str]:
    """Newest-first assistant text chunks from a transcript jsonl."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        _log(f"transcript_read_fail path={path} err={e!r}")
        return []
    out: list[str] = []
    for line in reversed(lines[-400:]):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        role = (obj.get("role") or "").lower()
        msg = obj.get("message") if isinstance(obj.get("message"), dict) else obj
        if role and role not in ("assistant", "model"):
            # Some formats nest role inside message
            if isinstance(msg, dict):
                role2 = (msg.get("role") or "").lower()
                if role2 and role2 not in ("assistant", "model"):
                    continue
            elif role not in ("assistant", "model"):
                continue
        content = None
        if isinstance(msg, dict):
            content = msg.get("content")
        if content is None:
            content = obj.get("content")
        chunks: list[str] = []
        if isinstance(content, str):
            chunks.append(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, str):
                    chunks.append(part)
                elif isinstance(part, dict):
                    if part.get("type") in ("tool_use", "tool_result"):
                        continue
                    t = part.get("text") or ""
                    if isinstance(t, str) and t.strip():
                        chunks.append(t)
        text = "\n".join(chunks).strip()
        if text:
            out.append(text)
        if len(out) >= max_lines:
            break
    return out


def _scan_transcript_file(path: Path, need_case: str = "") -> str:
    need_dig = _digits(need_case)
    for text in _assistant_texts_from_jsonl(path):
        if not _is_full_re(text):
            continue
        if need_dig and _digits(_case_from_text(text)) != need_dig:
            continue
        return text
    return ""


def _scan_any_transcript(need_case: str = "", transcript_path: str = "") -> str:
    # 1) Explicit path from Cursor payload (authoritative)
    if transcript_path:
        tf = _resolve_transcript_file(transcript_path)
        if tf:
            hit = _scan_transcript_file(tf, need_case)
            if hit:
                _log(f"transcript_path_hit file={tf.name} case={need_case or _case_from_text(hit)}")
                return hit
            _log(f"transcript_path_miss file={tf}")

    # 2) Fallback: newest jsonl under agent-transcripts
    roots = [
        Path.home()
        / ".cursor"
        / "projects"
        / "c-Users-PC-ENTER-Desktop-Citrix"
        / "agent-transcripts",
    ]
    proj = Path.home() / ".cursor" / "projects"
    if proj.is_dir():
        for p in proj.glob("*/agent-transcripts"):
            if p not in roots:
                roots.append(p)
    files: list[Path] = []
    for root in roots:
        if not root.is_dir():
            continue
        try:
            files.extend(root.rglob("*.jsonl"))
        except Exception:
            continue
    files = sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)[:6]
    for path in files:
        if "subagents" in path.parts:
            continue
        if time.time() - path.stat().st_mtime > 7200:
            continue
        hit = _scan_transcript_file(path, need_case)
        if hit:
            _log(f"transcript_glob_hit file={path.name}")
            return hit
    return ""


def _dump_payload(payload: dict, text: str) -> None:
    try:
        slim = {
            "keys": sorted(payload.keys()),
            "hook_event_name": payload.get("hook_event_name") or payload.get("event"),
            "text_len": len(text or ""),
            "transcript_path": str(payload.get("transcript_path") or ""),
            "conversation_id": str(payload.get("conversation_id") or "")[:36],
            "status": payload.get("status"),
            "loop_count": payload.get("loop_count"),
        }
        _PAYLOAD_DUMP.write_text(json.dumps(slim, indent=2), encoding="utf-8")
    except Exception:
        pass


def _spawn(text: str, source: str) -> None:
    worker = Path(__file__).resolve().parent / "auto_lf_after_re.py"
    if not worker.exists():
        _log("auto_lf_after_re.py missing")
        return
    _STATE.mkdir(parents=True, exist_ok=True)
    text_path = _STATE / "auto_lf_after_re_input.txt"
    payload = (text or "").strip()
    if not payload:
        _log(f"spawn aborted — no RE text source={source}")
        return
    case_id = _case_from_text(payload) or _pending_case_needing_lf()
    if case_id and _already_filed(case_id):
        _log(f"spawn skip already_filed {case_id} source={source}")
        return
    if not _debounce(case_id):
        _log(f"debounced case={case_id}")
        return
    text_path.write_text(payload, encoding="utf-8")
    try:
        _LATEST_RE.write_text(payload.strip() + "\n", encoding="utf-8")
    except Exception:
        pass
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x08000000 | 0x00000200
    err_log = _STATE / "auto_lf_after_re_spawn.err"
    with err_log.open("a", encoding="utf-8") as err_f:
        err_f.write(
            f"\n--- re_auto_lf_hook {datetime.now(timezone.utc).isoformat()} source={source} ---\n"
        )
        err_f.flush()
        proc = subprocess.Popen(
            [sys.executable, str(worker), "--run", "--text-file", str(text_path)],
            cwd=str(_REPO),
            stdin=subprocess.DEVNULL,
            stdout=err_f,
            stderr=err_f,
            creationflags=creationflags,
            close_fds=False if sys.platform == "win32" else True,
        )
    _log(f"spawned pid={proc.pid} text_len={len(payload)} case={case_id} source={source}")


def main() -> int:
    try:
        raw = sys.stdin.buffer.read()
        payload = json.loads(raw.decode("utf-8-sig", errors="replace")) if raw.strip() else {}
    except Exception as e:
        _log(f"json_error={e!r}")
        return _ok()

    if not isinstance(payload, dict):
        return _ok()
    if not _session_active():
        _log("skip session_inactive")
        return _ok()

    event = str(payload.get("hook_event_name") or payload.get("event") or "")
    transcript_path = str(payload.get("transcript_path") or "")
    text = _extract_text(payload)
    _dump_payload(payload, text)
    _log(
        f"event={event!r} text_len={len(text)} "
        f"transcript_path={'yes' if transcript_path else 'no'} "
        f"keys={sorted(payload.keys())[:14]}"
    )

    need = _pending_case_needing_lf()

    # 1) Payload text is a full RE
    if text and _is_full_re(text):
        _spawn(text, source=f"payload:{event or 'unknown'}")
        return _ok()

    # 2) Always try transcript_path / scan for pending Fall #
    scanned = _scan_any_transcript(need_case=need, transcript_path=transcript_path)
    if scanned and _is_full_re(scanned):
        cid = _case_from_text(scanned) or need
        if cid and _already_filed(cid):
            _log(f"scan skip already_filed {cid}")
            return _ok()
        # If we have a pending case, require match; else accept any fresh full RE
        if need and _digits(_case_from_text(scanned)) not in ("", _digits(need)):
            if _digits(_case_from_text(scanned)) != _digits(need):
                _log(f"scan case mismatch need={need} got={_case_from_text(scanned)}")
                # Still try need-specific scan only
                scanned2 = _scan_any_transcript(need_case=need, transcript_path=transcript_path)
                if not scanned2:
                    return _ok()
                scanned = scanned2
        _spawn(scanned, source=f"transcript:{event or 'unknown'}")
        return _ok()

    if need:
        _log(f"no_re_found need={need} event={event!r} text_len={len(text)}")

    # 3) Fresh latest_re fallback
    if _LATEST_RE.exists():
        try:
            age = time.time() - _LATEST_RE.stat().st_mtime
            if age < 180:
                saved = _LATEST_RE.read_text(encoding="utf-8", errors="replace")
                cid = _case_from_text(saved)
                if _is_full_re(saved) and cid and not _already_filed(cid):
                    _log(f"latest_re_hit age={age:.1f}s case={cid}")
                    _spawn(saved, source="latest_re")
                    return _ok()
        except Exception as e:
            _log(f"latest_re_fail={e!r}")

    return _ok()


if __name__ == "__main__":
    raise SystemExit(main())
