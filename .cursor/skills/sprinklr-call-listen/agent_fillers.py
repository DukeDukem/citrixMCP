"""
Ignore agent time-buying / filler speech so it does not pollute customer STT
or fire teleprompter turns.

Examples the agent may say while waiting for teleprompter:
  Alles klar. / Verstehe ich. / Mal schauen was ich da für Sie tun kann.
  Random short clarifying questions to buy time.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Optional


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.lower()
    for a, b in (
        ("ä", "ae"),
        ("ö", "oe"),
        ("ü", "ue"),
        ("ß", "ss"),
        ("fuer", "fur"),
        ("dar fur", "da fur"),
        ("dar fuer", "da fur"),
    ):
        s = s.replace(a, b)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Exact-ish short fillers (whole utterance or leading clause)
_DEFAULT_FILLERS = (
    "alles klar",
    "alles klar ja",
    "verstehe",
    "verstehe ich",
    "ich verstehe",
    "ja verstehe",
    "okay",
    "ok",
    "gut",
    "genau",
    "ja genau",
    "mhm",
    "aha",
    "moment",
    "moment bitte",
    "einen moment",
    "einen moment bitte",
    "sekunde",
    "eine sekunde",
    "kurz einen moment",
    "mal schauen",
    "mal sehen",
    "schauen wir mal",
    "mal schauen was ich da fur sie tun kann",
    "mal schauen was ich fur sie tun kann",
    "lassen sie mich kurz schauen",
    "ich schaue das kurz nach",
    "ich schau das kurz nach",
    "ich lege sie kurz in die warteschleife",
    "einen moment ich schaue das nach",
    "das schaue ich nach",
    "bleib sie kurz dran",
    "bleiben sie kurz dran",
    "ja",
    "ja ja",
    "okay gut",
)

# Soft patterns: short agent "stupid/time-buy" questions (keep customer long answers)
_TIMEBUY_QUESTION = re.compile(
    r"(?i)^\s*("
    r"koennen sie das nochmal kurz sagen|"
    r"koennen sie das wiederholen|"
    r"wie meinen sie das|"
    r"seit wann ist das so|"
    r"haben sie die kundennummer zur hand|"
    r"sind sie privat oder geschaeftskunde|"
    r"einen moment bitte|"
    r"darf ich sie kurz halten|"
    r"darf ich nachschauen"
    r").{0,40}\??\s*$"
)


def _fillers_from_cfg(cfg: dict[str, Any] | None) -> list[str]:
    extra = (cfg or {}).get("agent_timebuy_phrases") or []
    out = list(_DEFAULT_FILLERS)
    for x in extra:
        n = _norm(str(x))
        if n and n not in out:
            out.append(n)
    return out


def is_agent_timebuy(text: str, cfg: dict[str, Any] | None = None) -> bool:
    """True if this STT chunk is basically only agent filler / time-buy."""
    raw = (text or "").strip()
    if not raw:
        return True
    n = _norm(raw)
    if not n:
        return True

    max_chars = int((cfg or {}).get("agent_timebuy_max_chars", 90))
    fillers = _fillers_from_cfg(cfg)

    # Whole-utterance match
    for f in fillers:
        if n == f or n.rstrip(" .") == f:
            return True
        # Very short utterance that starts and ends as filler
        if len(n) <= max_chars and (n.startswith(f + " ") or n.endswith(" " + f)):
            # only if mostly filler (little extra content)
            if len(n) <= len(f) + 25:
                return True

    if len(n) <= max_chars and _TIMEBUY_QUESTION.match(raw):
        return True

    # Short utterances that are mostly filler tokens
    if len(n) <= 50:
        for f in fillers:
            if f in n and len(n) <= len(f) + 15:
                return True

    return False


def strip_leading_timebuy(text: str, cfg: dict[str, Any] | None = None) -> str:
    """Remove leading filler clauses from a mixed chunk; keep customer tail."""
    raw = (text or "").strip()
    if not raw:
        return ""
    if is_agent_timebuy(raw, cfg):
        return ""

    # Split on sentence-ish boundaries and drop leading filler sentences
    parts = re.split(r"(?<=[.!?])\s+|\n+", raw)
    fillers = _fillers_from_cfg(cfg)
    kept: list[str] = []
    dropping = True
    for p in parts:
        pn = _norm(p)
        if dropping and (
            any(pn == f or pn.startswith(f + " ") and len(pn) <= len(f) + 20 for f in fillers)
            or (len(pn) <= 90 and _TIMEBUY_QUESTION.match(p))
        ):
            continue
        dropping = False
        kept.append(p)
    return " ".join(kept).strip()


def filter_customer_speech(
    text: str, cfg: dict[str, Any] | None = None
) -> tuple[Optional[str], Optional[str]]:
    """
    Returns (kept_customer_text_or_None, log_event_or_None).
    """
    raw = (text or "").strip()
    if not raw:
        return None, None
    if is_agent_timebuy(raw, cfg):
        return None, f"GATE_SKIP (agent time-buy): {raw[:80]}"
    cleaned = strip_leading_timebuy(raw, cfg)
    if not cleaned:
        return None, f"GATE_SKIP (agent time-buy stripped): {raw[:80]}"
    if is_agent_timebuy(cleaned, cfg):
        return None, f"GATE_SKIP (agent time-buy): {cleaned[:80]}"
    return cleaned, None
