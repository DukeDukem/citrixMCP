"""
Fast CALL teleprompter: customer utterance → short German talk-track for the agent.

Latency order:
1) OpenAI (OPENAI_API_KEY / config openai_api_key) — gpt-4o-mini
2) Groq (GROQ_API_KEY)
3) Ollama local (OLLAMA_HOST, model llama3.2 or cfg)
4) Instant local templates (no network) — always available fallback
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional

_SKILL = Path(__file__).resolve().parent
_REPO = _SKILL.parent.parent.parent

_SYSTEM = """Du bist ein Teleprompter für einen o2 Care Telefon-Agenten (Lukas) in Deutschland.
Aufgabe: Gib NUR den Text, den der Agent JETZT laut zum Kunden sagen soll.
Regeln:
- Deutsch, freundlich, klar, max 2–4 kurze Sätze oder Bullet-Zeilen.
- Keine internen Systeme nennen (kein Sabio, TIM, Sprinklr, Wissensbasis, Queue-Namen).
- Keine erfundenen Zusagen (kein „wir prüfen intern und melden uns“, keine Ticket-/Gutschrift-Versprechen), außer der Agent soll explizit sagen, dass er den Kunden kurz in die Warteschleife legt.
- Wenn keine klare Lösung da ist: empathisch bleiben, Anliegen kurz spiegeln, eine gezielte Rückfrage ODER anbieten, den Kunden kurz zu halten („Einen Moment bitte, ich schaue das kurz nach.“).
- Mein o2 / o2.de nur nennen, wenn es zum Thema passt.
- Keine Anrede „Guten Tag Name“ wiederholen, kein E-Mail-Schluss, keine Fallnummer.
- Output: nur Sprechtext, keine Meta-Kommentare."""


def _load_repo_config() -> dict[str, Any]:
    p = _REPO / "config.json"
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _norm(s: str) -> str:
    s = (s or "").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        s = s.replace(a, b)
    return s


def _template_talk_track(customer: str) -> str:
    """Zero-latency friendly talk-track when no LLM is configured."""
    t = _norm(customer)
    hold = "Einen Moment bitte, ich lege Sie kurz in die Warteschleife und schaue das nach."

    if any(k in t for k in ("rechnung", "betrag", "abbuch", "lastschrift", "zahlung", "mahnung", "gutschrift")):
        return (
            "Vielen Dank, dass Sie mir das so genau erklären — ich verstehe, dass die Rechnung Sie ärgert.\n"
            "Damit ich das richtig einordnen kann: Geht es um den aktuellen Betrag oder um eine ältere Abbuchung?\n"
            f"{hold}"
        )
    if any(k in t for k in ("kuendig", "kündig", "widerruf", "storno", "vertrag beend")):
        return (
            "Alles klar, danke — ich habe verstanden, dass es um Ihre Kündigung bzw. Vertragsbeendigung geht.\n"
            "Nennen Sie mir bitte noch das gewünschte Enddatum, falls Sie eines im Kopf haben.\n"
            f"{hold}"
        )
    if any(k in t for k in ("netz", "empfang", "stoer", "störung", "kein internet", "langsam", "lte", "5g", "wlan")):
        return (
            "Das tut mir leid, dass die Verbindung gerade nicht zuverlässig ist.\n"
            "Sind Sie gerade zu Hause oder unterwegs — und betrifft es Telefonie, Internet, oder beides?\n"
            f"{hold}"
        )
    if any(k in t for k in ("handy", "geraet", "gerät", "display", "akku", "defekt", "reparatur", "myhandy")):
        return (
            "Verstehe, danke für die Schilderung zum Gerät.\n"
            "Seit wann tritt das Problem auf, und haben Sie schon einen Neustart versucht?\n"
            f"{hold}"
        )
    if any(k in t for k in ("tarif", "option", "buchung", "vvl", "angebot", "zu teuer", "datenvolumen")):
        return (
            "Danke, ich habe mitbekommen, dass es um Ihren Tarif bzw. eine Option geht.\n"
            "Möchten Sie vor allem eine Erklärung zur Buchung, oder sollen wir schauen, was aktuell sinnvoll möglich ist?\n"
            f"{hold}"
        )
    if any(k in t for k in ("pin", "puk", "passwort", "login", "zugang", "mein o2", "app")):
        return (
            "Alles klar — Zugang bzw. Anmeldung ist oft schnell lösbar.\n"
            "Können Sie mir sagen, ob die Fehlermeldung in der App, auf o2.de oder am Gerät erscheint?\n"
            "Viele Zugangswege finden Sie auch unter Mein o2; wenn Sie möchten, gehe ich die Schritte kurz mit Ihnen durch."
        )
    if any(k in t for k in ("umzug", "adresse", "namensaenderung", "namensänderung", "iban", "bank")):
        return (
            "Danke, ich habe verstanden, dass Stammdaten geändert werden sollen.\n"
            "Aus Sicherheitsgründen brauchen wir dafür oft den Weg über Mein o2 — ich sage Ihnen gleich den passenden Schritt.\n"
            f"{hold}"
        )
    if len(customer.strip()) < 40:
        return (
            "Ich bin bei Ihnen — erzählen Sie gerne noch ein wenig mehr zum genauen Anliegen,\n"
            "dann kann ich Ihnen direkt die nächste sinnvolle Option nennen."
        )
    # Generic vague-but-warm
    snippet = customer.strip().replace("\n", " ")
    if len(snippet) > 90:
        snippet = snippet[:87] + "…"
    return (
        f"Danke, ich habe Sie so verstanden: {snippet}\n"
        "Damit ich Ihnen weiterhelfen kann: Was ist für Sie jetzt der wichtigste nächste Schritt?\n"
        f"{hold}"
    )


def _openai_chat(customer: str, cfg: dict[str, Any]) -> Optional[str]:
    key = (os.environ.get("OPENAI_API_KEY") or cfg.get("openai_api_key") or "").strip()
    if not key:
        return None
    model = cfg.get("teleprompter_openai_model") or "gpt-4o-mini"
    body = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": f"Kunde sagt gerade (Transkription):\n\"\"\"{customer.strip()}\"\"\"\n\nTeleprompter-Text für den Agenten:",
            },
        ],
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        return text or None
    except Exception:
        return None


def _groq_chat(customer: str, cfg: dict[str, Any]) -> Optional[str]:
    key = (os.environ.get("GROQ_API_KEY") or cfg.get("groq_api_key") or "").strip()
    if not key:
        return None
    model = cfg.get("teleprompter_groq_model") or "llama-3.1-8b-instant"
    body = {
        "model": model,
        "temperature": 0.4,
        "max_tokens": 180,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": f"Kunde sagt gerade:\n\"\"\"{customer.strip()}\"\"\"\n\nTeleprompter:",
            },
        ],
    }
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip() or None
    except Exception:
        return None


def _ollama_chat(customer: str, cfg: dict[str, Any]) -> Optional[str]:
    host = (os.environ.get("OLLAMA_HOST") or cfg.get("ollama_host") or "http://127.0.0.1:11434").rstrip(
        "/"
    )
    model = cfg.get("teleprompter_ollama_model") or "llama3.2"
    body = {
        "model": model,
        "stream": False,
        "options": {"temperature": 0.4, "num_predict": 180},
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {
                "role": "user",
                "content": f"Kunde sagt:\n\"\"\"{customer.strip()}\"\"\"\n\nTeleprompter:",
            },
        ],
    }
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return (data.get("message") or {}).get("content", "").strip() or None
    except Exception:
        return None


def generate_talk_track(
    customer_text: str,
    *,
    prefer: str | None = None,
    capture_cfg: dict[str, Any] | None = None,
) -> tuple[str, str]:
    """
    Returns (talk_track, backend_name).
    backend_name: openai | groq | ollama | template
    """
    customer_text = (customer_text or "").strip()
    if not customer_text:
        return (
            "Ich bin noch bei Ihnen — sagen Sie gerne weiter, worum es genau geht.",
            "template",
        )

    cfg = {**_load_repo_config(), **(capture_cfg or {})}
    order = prefer or cfg.get("teleprompter_backend") or "auto"

    backends = []
    if order == "template":
        backends = ["template"]
    elif order == "openai":
        backends = ["openai", "template"]
    elif order == "groq":
        backends = ["groq", "template"]
    elif order == "ollama":
        backends = ["ollama", "template"]
    else:
        backends = ["openai", "groq", "ollama", "template"]

    for b in backends:
        if b == "openai":
            t = _openai_chat(customer_text, cfg)
            if t:
                return t, "openai"
        elif b == "groq":
            t = _groq_chat(customer_text, cfg)
            if t:
                return t, "groq"
        elif b == "ollama":
            t = _ollama_chat(customer_text, cfg)
            if t:
                return t, "ollama"
        elif b == "template":
            return _template_talk_track(customer_text), "template"

    return _template_talk_track(customer_text), "template"
