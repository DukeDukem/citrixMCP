"""
Customer-phase gate for CALL listen / teleprompter.

Default trigger (gate_trigger=call_case): open when Sprinklr CALL UI is detected
(or agent --prime). Do NOT wait for the spoken o2 greeting.

Legacy (gate_trigger=greeting): open after hearing the agent welcome line (or timeout).

Agent greeting / fillers are still stripped from STT so they do not fire SAY THIS.
"""
from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Optional


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    repl = (
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("ß", "ss"),
        ("fuer", "fur"),
        ("willkomen", "willkommen"),
        ("willkommen", "willkommen"),
        ("telefónica", "telefonica"),
        ("o 2", "o2"),
        ("o-2", "o2"),
    )
    for a, b in repl:
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


_DEFAULT_FRAGMENTS = (
    "willkommen bei o2",
    "willkommen beim o2",
    "lukas ist mein name",
    "mein name ist lukas",
    "wie kann ich weiterhelfen",
    "wie kann ich ihnen weiterhelfen",
    "was kann ich fur sie tun",
    "was kann ich fuer sie tun",
    "was kann ich tun",
)

_GREETING_STRIP = re.compile(
    r"(?i)willkommen\s+bei(?:m)?\s+o2[^.]{0,80}?"
    r"(?:lukas\s+ist\s+mein\s+name|mein\s+name\s+ist\s+lukas)?[^.]{0,60}?"
    r"(?:wie\s+kann\s+ich\s+(?:ihnen\s+)?weiterhelfen|"
    r"was\s+kann\s+ich\s+f(?:u|ue)r\s+sie\s+tun)?[.?!]?\s*"
)


class CustomerPhaseGate:
    """Control when STT counts as customer speech for brief + teleprompter."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        cfg = cfg or {}
        # Backward compat: post_greeting_only false → always open (trigger none)
        if "gate_trigger" in cfg:
            self.trigger = str(cfg.get("gate_trigger") or "call_case").lower()
        elif cfg.get("post_greeting_only") is False:
            self.trigger = "none"
        else:
            # New default: CALL case / UI primes the gate (not spoken greeting)
            self.trigger = "call_case"

        self.timeout_s = float(cfg.get("gate_timeout_s", 25))
        self.min_chars = int(cfg.get("min_customer_chars", 8))
        self.match_min = int(cfg.get("greeting_match_min", 2))
        frags = cfg.get("agent_greeting_fragments") or list(_DEFAULT_FRAGMENTS)
        self.fragments = [_norm(f) for f in frags if f]
        self.open = self.trigger in ("none", "off", "disabled")
        self.t0 = time.time()
        self._heard: set[str] = set()
        self.opened_reason: Optional[str] = "always" if self.open else None
        # Legacy flag used by call_listen logs
        self.enabled = self.trigger not in ("none", "off", "disabled")

    def open_call_case(self, reason: str = "call_case") -> Optional[str]:
        """Prime for customer STT when CHANNEL: CALL / live call UI is seen."""
        if self.open:
            return None
        self.open = True
        self.opened_reason = reason
        return f"CUSTOMER_PHASE_OPEN reason={reason}"

    def reset(self) -> None:
        was_always = self.trigger in ("none", "off", "disabled")
        self.open = was_always
        self.t0 = time.time()
        self._heard.clear()
        self.opened_reason = "always" if was_always else None

    def _greeting_hit(self, normed: str) -> bool:
        hits_now = 0
        for frag in self.fragments:
            if frag and frag in normed:
                self._heard.add(frag)
                hits_now += 1
        if hits_now >= self.match_min:
            return True
        if len(self._heard) >= self.match_min and hits_now >= 1:
            return True
        if "willkommen" in normed and "lukas" in normed and (
            "weiterhelfen" in normed or "was kann ich" in normed or "o2" in normed
        ):
            return True
        return False

    def _is_mostly_greeting(self, normed: str) -> bool:
        if not normed:
            return True
        hits = sum(1 for frag in self.fragments if frag and frag in normed)
        if hits >= 2 and len(normed) < 120:
            return True
        if "willkommen" in normed and "lukas" in normed and len(normed) < 120:
            return True
        return False

    def _strip_greeting(self, text: str) -> str:
        t = _GREETING_STRIP.sub("", text).strip()
        n = _norm(t)
        if self._is_mostly_greeting(n):
            return ""
        m = re.search(
            r"(?i)(?:willkommen|lukas\s+ist\s+mein\s+name|"
            r"wie\s+kann\s+ich\s+(?:ihnen\s+)?weiterhelfen|"
            r"was\s+kann\s+ich\s+f(?:u|ue)r\s+sie\s+tun)[^.?!]*[.?!]\s*",
            t,
        )
        if m and m.end() < len(t):
            t = t[m.end() :].strip()
        return t

    def filter(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Returns (text_to_append_or_None, log_event_or_None).
        """
        text = (text or "").strip()
        if not text:
            return None, None

        if not self.enabled:
            cleaned = self._strip_greeting(text)
            if not cleaned or len(cleaned) < self.min_chars:
                return None, None
            if self._is_mostly_greeting(_norm(cleaned)):
                return None, None
            return cleaned, None

        # call_case: stay closed until open_call_case() — discard STT meanwhile
        if self.trigger == "call_case" and not self.open:
            return None, f"GATE_SKIP (awaiting CALL prime): {text[:80]}"

        # greeting trigger: open on welcome line or timeout
        if self.trigger == "greeting" and not self.open:
            if (time.time() - self.t0) >= self.timeout_s:
                self.open = True
                self.opened_reason = "timeout"
                return (
                    text if len(text) >= self.min_chars else None,
                    "CUSTOMER_PHASE_OPEN reason=timeout (greeting not heard — likely remote-only audio)",
                )
            normed = _norm(text)
            if self._greeting_hit(normed):
                self.open = True
                self.opened_reason = "greeting"
                rest = self._strip_greeting(text)
                if rest and len(rest) >= self.min_chars and not self._is_mostly_greeting(_norm(rest)):
                    return rest, "CUSTOMER_PHASE_OPEN reason=greeting"
                return None, "CUSTOMER_PHASE_OPEN reason=greeting (waiting for customer speech)"
            return None, f"GATE_SKIP (pre-greeting): {text[:80]}"

        # Open phase — drop pure agent greeting echoes
        cleaned = self._strip_greeting(text)
        if not cleaned or len(cleaned) < self.min_chars:
            return None, None
        if self._is_mostly_greeting(_norm(cleaned)):
            return None, None
        return cleaned, None
