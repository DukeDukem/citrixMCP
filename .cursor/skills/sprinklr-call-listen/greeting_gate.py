"""
Post-greeting gate: keep customer speech after the agent o2 welcome line.

Typical agent open:
  "Willkommen bei o2, Lukas ist mein Name, was kann ich für Sie tun?"

Until that (or timeout), STT lines are discarded so the brief is the customer rant.
"""
from __future__ import annotations

import re
import time
import unicodedata
from typing import Any, Optional


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    # Fold common STT misspellings / missing umlauts
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


# Fragments of the standard Lukas / o2 greeting (match ≥2 → gate opens)
_DEFAULT_FRAGMENTS = (
    "willkommen bei o2",
    "willkommen beim o2",
    "lukas ist mein name",
    "mein name ist lukas",
    "was kann ich fur sie tun",
    "was kann ich fuer sie tun",
    "was kann ich tun",
)

# Strip leftover greeting from a mixed chunk after gate opens
_GREETING_STRIP = re.compile(
    r"(?i)willkommen\s+bei(?:m)?\s+o2[^.]{0,80}?"
    r"(?:lukas\s+ist\s+mein\s+name|mein\s+name\s+ist\s+lukas)?[^.]{0,40}?"
    r"(?:was\s+kann\s+ich\s+f(?:u|ue)r\s+sie\s+tun)?[.?!]?\s*"
)


class CustomerPhaseGate:
    """Drop STT until agent greeting heard (or timeout), then keep customer text."""

    def __init__(self, cfg: dict[str, Any] | None = None) -> None:
        cfg = cfg or {}
        self.enabled = bool(cfg.get("post_greeting_only", True))
        self.timeout_s = float(cfg.get("gate_timeout_s", 25))
        self.min_chars = int(cfg.get("min_customer_chars", 8))
        self.match_min = int(cfg.get("greeting_match_min", 2))
        frags = cfg.get("agent_greeting_fragments") or list(_DEFAULT_FRAGMENTS)
        self.fragments = [_norm(f) for f in frags if f]
        self.open = not self.enabled  # if disabled, always open
        self.t0 = time.time()
        self._heard: set[str] = set()
        self.opened_reason: Optional[str] = None

    def _greeting_hit(self, normed: str) -> bool:
        """True if *this* utterance looks like the agent greeting."""
        hits_now = 0
        for frag in self.fragments:
            if frag and frag in normed:
                self._heard.add(frag)
                hits_now += 1
        if hits_now >= self.match_min:
            return True
        if len(self._heard) >= self.match_min and hits_now >= 1:
            # Partial re-hear of greeting while accumulating
            return True
        # Strong single-line: willkommen + lukas (+ o2 or was kann ich)
        if "willkommen" in normed and "lukas" in normed and (
            "was kann ich" in normed or "o2" in normed
        ):
            return True
        return False

    def _is_mostly_greeting(self, normed: str) -> bool:
        """True if utterance is basically only the welcome line (not customer rant)."""
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
        # Also cut everything up to end of "was kann ich … tun"
        n = _norm(t)
        if self._is_mostly_greeting(n):
            return ""
        # If greeting + customer in one chunk, drop leading welcome clause
        m = re.search(
            r"(?i)(?:willkommen|lukas\s+ist\s+mein\s+name|was\s+kann\s+ich\s+f(?:u|ue)r\s+sie\s+tun)[^.?!]*[.?!]\s*",
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
            return text, None

        # Timeout: remote-only streams may never contain the agent mic
        if not self.open and (time.time() - self.t0) >= self.timeout_s:
            self.open = True
            self.opened_reason = "timeout"
            return (
                text if len(text) >= self.min_chars else None,
                "CUSTOMER_PHASE_OPEN reason=timeout (greeting not heard — likely remote-only audio)",
            )

        normed = _norm(text)

        if not self.open:
            if self._greeting_hit(normed):
                self.open = True
                self.opened_reason = "greeting"
                rest = self._strip_greeting(text)
                if rest and len(rest) >= self.min_chars and not self._is_mostly_greeting(_norm(rest)):
                    return rest, "CUSTOMER_PHASE_OPEN reason=greeting"
                return None, "CUSTOMER_PHASE_OPEN reason=greeting (waiting for customer speech)"
            return None, f"GATE_SKIP (pre-greeting): {text[:80]}"

        # Customer phase — drop pure greeting echoes only
        cleaned = self._strip_greeting(text)
        if not cleaned or len(cleaned) < self.min_chars:
            return None, None
        if self._is_mostly_greeting(_norm(cleaned)):
            return None, None
        return cleaned, None
