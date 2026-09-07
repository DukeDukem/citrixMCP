"""
Compose teleprompter display: live customer STT (rolling) + SAY THIS lines.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional


class TeleprompterDisplay:
    """Writes call_teleprompter_latest.txt with LIVE + SAY THIS sections."""

    def __init__(self, latest_path: Path, history_dir: Path) -> None:
        self.latest_path = latest_path
        self.history_dir = history_dir
        self.fall = "unknown"
        self.status = "Waiting…"
        self.live_lines: list[str] = []
        self.say_block = "(waiting for customer pause → SAY THIS)"
        self._max_live_lines = 40

    def reset(self, fall: str) -> None:
        self.fall = fall or "unknown"
        self.live_lines.clear()
        self.say_block = "(waiting for customer pause → SAY THIS)"
        self.status = "PRIMED — listening for customer audio…"
        self.flush()

    def set_status(self, status: str) -> None:
        self.status = status
        self.flush()

    def append_live(self, text: str, tag: str = "Kunde") -> None:
        text = (text or "").strip()
        if not text:
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self.live_lines.append(f"[{stamp}] [{tag}] {text}")
        if len(self.live_lines) > self._max_live_lines:
            self.live_lines = self.live_lines[-self._max_live_lines :]
        self.flush()
        # Persist rolling live file for this fall
        try:
            live_path = self.history_dir / f"call_live_{self.fall}.txt"
            with live_path.open("a", encoding="utf-8") as f:
                f.write(f"[{stamp}] [{tag}] {text}\n")
        except Exception:
            pass

    def set_say_this(self, talk: str, customer: str, backend: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.say_block = (
            f"[{stamp}] SAY THIS ({backend})\n\n"
            f"{(talk or '').strip()}\n\n"
            f"— (customer) {(customer or '').strip()[:280]}"
        )
        self.flush()

    def compose(self) -> str:
        live = "\n".join(self.live_lines) if self.live_lines else "(no customer speech transcribed yet)"
        return (
            f"LIVE CUSTOMER (STT) — Fall #{self.fall}\n"
            f"{self.status}\n"
            f"{'─' * 42}\n"
            f"{live}\n"
            f"\n"
            f"{'═' * 42}\n"
            f"SAY THIS — read to customer\n"
            f"{'─' * 42}\n"
            f"{self.say_block}\n"
        )

    def flush(self) -> None:
        self.latest_path.parent.mkdir(parents=True, exist_ok=True)
        self.latest_path.write_text(self.compose(), encoding="utf-8")
