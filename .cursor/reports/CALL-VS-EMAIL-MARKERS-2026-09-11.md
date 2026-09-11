# CALL vs EMAIL — visual markers (2026-09-11)

Reference cases:
- **CALL:** **Fall #57937085**, **#57934518**, **#57938822** — *Unbekannter Kunde*
- **EMAIL sidetray:** **Fall #57675993** — *Natalia Nuzhna* (`BrandEmailCircleClr`)

Screenshots saved in Cursor assets (2026-09-11 session).

---

## Sidetray pre-open (post-arm, before click)

Container: `[data-entityid="CollapsedPreviewsList"]`  
Item: `button[data-testid="collapsed-case-item"]`

| Channel | Badge icon | Script stdout |
|---------|------------|---------------|
| **CALL** | `svg[data-icon-name="BrandVoiceCircleClr"]` (green voice circle) | `SIDETRAY_CHANNEL: CALL` → `SIDETRAY_CALL_SKIP_CLICK` → `SIDETRAY_CALL_AUTO_OPEN` (no click) |
| **EMAIL** | `svg[data-icon-name="BrandEmailCircleClr"]` (blue envelope circle) | `SIDETRAY_CHANNEL: EMAIL` → `CASE_ITEM_AUTO_CLICKED` → **`SIDETRAY_EMAIL_PROCESSING_IMMEDIATE`** → extract → agent auto 7-step + Auto-LF |

**EMAIL example (Fall #57675993):** `button[data-testid="collapsed-case-item"]` with `aria-label="Fall Nr. 57675993 von Natalia Nuzhna"`, avatar + blue `BrandEmailCircleClr` badge; item height often ~8.6rem (CALL ~6rem). Script uses DOM locators inside `[data-entityid="CollapsedPreviewsList"]`, not pixel coordinates.

Poll interval ~0.25s from arm trigger (no fixed 4s delay). Optional `SIDETRAY_EMPTY` when tray clears between cases. Sidetray watch always runs; **EMAIL icons are clicked**; **CALL icons are not**.

---

## Decisive CALL signals (script `_detect_case_channel_once`)

These are wired in `email_automation.py` post-open poll:

| Signal | Example / selector hint |
|--------|-------------------------|
| **No-reply bar** | `Sie können auf das Gespräch nicht antworten.` |
| **Anruf •** timeline label | Under every event: `Anruf • 3min` |
| **Eingehender Anruf** | With phone number |
| **Anruf angenommen** | Green phone bubble |
| **In Warteschlange übertragen** | Queue name e.g. `WQ_IBV_O2_CARE_I@H` |
| **Anruf wurde getrennt** | Red phone bubble |
| **Wartestellung** / hold events | Yellow/grey hold bubbles |
| **Blindübertragung abgeschlossen** | After blind transfer |
| **Live timer** on case header | `00:02:28` next to Fall # |
| **Voice toolbar** | Handset + waveform icons top-right |
| **Voice sidebar** | Mic, pause, red hang-up |

**Absent on CALL:** substantial `[data-testid="html-message-content"]` body, **Von:** / **Betreff:** email headers, `Nachricht verfassen` usable reply box.

---

## EMAIL signals (contrast)

| Signal | CALL case | EMAIL case |
|--------|-----------|------------|
| `html-message-content` body | Missing or trivial | Substantial text (80+ chars typical) |
| Von / Betreff | No | Yes |
| Timeline | Anruf events only | Email thread with message containers |
| Reply composer | Blocked / absent | **Nachricht verfassen** active |

---

## Script output

| Channel | Stdout markers |
|---------|----------------|
| **CALL** | `CHANNEL: CALL`, `CHANNEL_CALL_DETECTED`, `CALL_LF_GATE` |
| **EMAIL** | `CHANNEL: EMAIL`, `CUSTOMER EMAIL`, `RE_TEXT_ONLY_GATE` |

Rule: `.cursor/rules/sprinklr-call-vs-email.mdc`
