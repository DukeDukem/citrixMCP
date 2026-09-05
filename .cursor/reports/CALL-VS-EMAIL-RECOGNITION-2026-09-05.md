# CALL vs EMAIL recognition — snapshot 2026-09-04/05

**Fall:** `#57114650` — Uwe Kommer  
**Captured:** 2026-09-05 ~11:13 (Citrix Care Console)  
**Screenshot:** `sprinklr-call-overlay-2026-09-05.png`  
**DOM dumps:** `sprinklr-call-overlay-dom-2026-09-05.json`, `sprinklr-call-vs-email-selectors-2026-09-05.json`  
**Rule:** `.cursor/rules/sprinklr-call-vs-email.mdc`

---

## What this case is

This is a **voice CALL**, not an inbound email.

### Visual overlays (call-specific)

1. Bottom status: **Im Gespräch** + call timer  
2. Status lines: Medienauslagerung / **Mikrofon angeschlossen** / VOIP Nailed Up  
3. Floating **Disposition** widget: Case #57114650, o2 Disposition Plan, Disposition Codes, phone icon  

### Timeline

- **Eingehender Anruf…**
- Audio play bars (e.g. 0:09, 3:57)
- **Anruf beendet**, **Aufzeichnung gestartet**, disconnect/TIMEOUT events
- Labels **Anruf** on events

### Case Informationen (DOM)

| Field | Value |
|-------|--------|
| Quelle | **Aura Care Shared** |
| Ziel | Sales Beratung - Mobile Pilot 2 |
| Fallnummer | 57114650 |
| Kundennummer | 8176834 |

### DOM markers

- `bodyHas.EingehenderAnruf` / `AnrufBeendet` / `ImGespraech` = true  
- Call-ish testids: `audio_pres`, `call-button`, `omniMedia`, `mediaItems`, `mediaList-OMNI_TEMPLATE_0`  
- `html-message-content` count = **0**  
- Conversation fan/brand items may still exist, but content is call/media oriented  

---

## How to differentiate later

| | CALL | EMAIL |
|--|------|-------|
| Overlay | Im Gespräch, Disposition, VOIP/mic | Absent |
| Timeline | Eingehender Anruf, Anruf beendet, audio | Email text bodies |
| Quelle | Aura Care Shared (this sample) | Often Care Webform / mail |
| html-message-content | 0 / rare | Present |
| Pipeline | Not email RE/PR unless asked | Normal RE → PR → LF |

---

## LF for CALL cases

| Field | Value |
|-------|--------|
| Kanal | **Voice (Tel.)** (`#channel_voice`, `--channel voice`) |
| Ticketstatus Salcus | **Always** **3-Bot dokumentiert nicht in Salcus** |

Do not log calls as E-Mail Care.
