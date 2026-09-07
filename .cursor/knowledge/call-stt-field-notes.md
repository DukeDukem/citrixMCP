# CALL STT / teleprompter — field notes (Sep 2026)

Practical lessons from live Care calls. Not a training corpus — failure modes to design around.

## Status

**Parked 2026-09-07** — `capture_path.json` `enabled=false`. Do not arm teleprompter in live Care until a better model is chosen. Base (HyperX loopback + turbo DE) kept for reactivation.

---

## Case note (Fall ~#57323090 era, 2026-09-07)

**What actually happened (agent handling — not STT):**

1. Customer: expected **refund** on a **payment option that was already cancelled**.
2. Agent searched for the account; customer **spelled Kundennummer digit-by-digit**.
3. Lookup **failed** — agent told customer the number could not be found.
4. Transfer to **Billings** so a colleague can **create a ticket** (Kundennummer no longer exists / not findable).

**STT / teleprompter:** LIVE transcript was **mostly gibberish** for this call despite loopback pickup and German language lock.

**Takeaway:** Hearing *some* audio ≠ usable transcript. Do **not** trust STT for identifiers or as the sole case summary when speech is accented / broken / digit-spelled.

---

## Failure modes that matter for “future training” (really: product design)

| Situation | What STT does badly | Better approach |
|-----------|---------------------|-----------------|
| **Digit-by-digit Kundennummer / IBAN / MSISDN** | Hallucinates wrong digits, merges/splits numbers | Agent types from ear; STT optional “spelling mode” later; never auto-fill Salcus from STT |
| **Non-native / broken German** | Gibberish or English drift | Keep `language=de` + domain prompt; treat LIVE as hint only |
| **Quiet / noisy loopback** | Noise → invented phrases | `loopback_min_peak` volume gate; raise if gibberish on silence |
| **Refund / cancelled payment product** | Topic words may appear; details often wrong | Agent + Sprinklr/Billings path; BRIEF from human override |

**You do not need a massive labeled speech dataset** for Care teleprompter v1. You need:

1. Honest UX: LIVE = approximate; agent confirms critical facts.
2. Optional later: **number-spelling detector** (regex / constrained decoder for digit sequences) — small feature, not full ASR retrain.
3. Optional later: few **prompt examples** of “Kunde buchstabiert Kundennummer …” in teleprompter system text.
4. Only if still insufficient: fine-tune or switch model size (`small` → `medium`) — still not a giant in-house corpus.

---

## Handling reminder (Billings / no Kundennummer)

When account cannot be found after customer spells the number:

- Tell customer clearly the number is not found in systems available to Care.
- Transfer **Billings** (or matrix Ziel) for ticket / refund path — do not invent a Kundennummer from STT.
- Case Tracker / LF: voice channel; do not invent Salcus from teleprompter digits.

---

## Config knobs already in repo

- `capture_path.json` → `stt_language=de`, `stt_initial_prompt`, `loopback_min_peak`, `windows_loopback`
- Teleprompter: interpret messy DE STT; clear Standarddeutsch SAY THIS
- Never use STT output as exclusive source for Kundennummer / IBAN / refund amounts
