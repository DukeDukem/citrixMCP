"""
Always-on-top teleprompter window — tails call_teleprompter_latest.txt

Usage:
  uv run python .cursor/skills/sprinklr-call-listen/teleprompter_ui.py
"""
from __future__ import annotations

import tkinter as tk
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent.parent
_LATEST = _REPO / ".cursor" / "state" / "call_teleprompter_latest.txt"
_POLL_MS = 400


def main() -> int:
    root = tk.Tk()
    root.title("o2 CALL Teleprompter — say this")
    root.attributes("-topmost", True)
    root.geometry("720x320+40+40")
    root.configure(bg="#1a1028")

    header = tk.Label(
        root,
        text="TELEPROMPTER — read to customer",
        fg="#f5c542",
        bg="#1a1028",
        font=("Segoe UI", 12, "bold"),
        anchor="w",
    )
    header.pack(fill="x", padx=12, pady=(10, 4))

    meta = tk.Label(
        root,
        text="Waiting for customer speech…",
        fg="#c4b5d8",
        bg="#1a1028",
        font=("Segoe UI", 9),
        anchor="w",
    )
    meta.pack(fill="x", padx=12)

    text = tk.Text(
        root,
        wrap="word",
        font=("Segoe UI", 14),
        bg="#2a1840",
        fg="#f8f4ff",
        insertbackground="#f8f4ff",
        relief="flat",
        padx=14,
        pady=12,
    )
    text.pack(fill="both", expand=True, padx=12, pady=12)
    text.insert("1.0", "Armed. After your greeting, customer speech → lines appear here.")
    text.configure(state="disabled")

    state = {"mtime": None, "body": ""}

    def refresh() -> None:
        try:
            if _LATEST.exists():
                m = _LATEST.stat().st_mtime
                if m != state["mtime"]:
                    body = _LATEST.read_text(encoding="utf-8", errors="replace")
                    state["mtime"] = m
                    state["body"] = body
                    text.configure(state="normal")
                    text.delete("1.0", "end")
                    text.insert("1.0", body.strip() or "(empty)")
                    text.configure(state="disabled")
                    # flash header
                    header.configure(fg="#7CFFB2")
                    root.after(350, lambda: header.configure(fg="#f5c542"))
                    first = body.strip().splitlines()[0] if body.strip() else ""
                    meta.configure(text=first[:100] if first.startswith("[") else "Updated")
            else:
                meta.configure(text=f"Waiting for {_LATEST.name}")
        except Exception as e:
            meta.configure(text=f"UI error: {e}")
        root.after(_POLL_MS, refresh)

    root.after(_POLL_MS, refresh)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
