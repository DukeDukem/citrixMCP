# Open German ASR resources (importable)

Survey for Care teleprompter / `faster-whisper` (Sep 2026).  
**Goal:** better DE, accents, dialects, messy speech — without building a private mega-corpus first.

---

## Drop-in models (easiest — try before training)

| Resource | Why useful | Status in this repo |
|----------|------------|---------------------|
| **GalaktischeGurke/primeline-whisper-large-v3-german-ct2** | German-tuned Whisper large-v3, already CT2 | **ACTIVE default** (auto-download) |
| Stock Whisper `turbo` / `medium` | Fast fallback, MIT | Fallback if CT2 missing |
| Swiss-German CT2 | Dialects | Optional; often gated |

Install/verify:

```powershell
uv run python .cursor/skills/sprinklr-call-listen/install_german_stt.py
```

---

## Open training / fine-tune datasets (if you train later)

| Dataset | Size (order) | Fits Care? | License | Link |
|---------|--------------|------------|---------|------|
| **Mozilla Common Voice German** | ~1400+ h validated (CV 26) | Best free general DE; many accents/ages | **CC0** | [Mozilla Data Collective – CV DE](https://mozilladatacollective.com/), [commonvoice.mozilla.org](https://commonvoice.mozilla.org/) |
| **VoxPopuli DE** | ~282 h transcribed EP speech | Formal/political speech; not Care slang | **CC0** (data) | [facebook/voxpopuli](https://huggingface.co/datasets/facebook/voxpopuli) |
| **Multilingual LibriSpeech (MLS) DE** | Large read speech | Clean read DE; weak on phone/broken DE | CC-BY | Hugging Face `facebook/multilingual_librispeech` |
| **SwissDial / Swiss Parliaments / ArchiMob** | Dialect-heavy | If CH dialects matter | Check each card | Used by Swiss-German Whisper cards above |

**Fine-tune recipes (don’t invent from scratch):**

- Mozilla blueprint: [Fine-tune ASR with Common Voice](https://blueprints.mozilla.ai/all-blueprints/finetune-an-asr-model-using-common-voice-data)  
- LoRA Whisper DE example: [hasanhalacli/whisper-german-finetuning](https://github.com/hasanhalacli/whisper-german-finetuning)  
- NVIDIA NeMo Common Voice notebook (linked from NeMo tutorials)

---

## What helps *your* Care case (honest fit)

| Need | Best open resource | Gap |
|------|--------------------|-----|
| Better Standard German phone audio | Common Voice DE + larger Whisper / primeline DE | CV is often mic/read, not VOIP headset |
| Accent / L2 German | Common Voice diversity + your few hard calls as **eval** | No big “broken Care German” public set |
| Digit-by-digit Kundennummer | Almost nothing public | Needs your clips + constrained digit decoder |
| Swiss dialect | Swiss-German Whisper CT2 | Overkill if callers are mostly DE/AT |

**VoxPopuli English L2 accent subset** (~29 h) is for **accented English**, not German — skip for Care DE.

---

## Recommended order for this repo

1. **Try import:** primeline / flozi German CT2 **or** bump `stt_model` to `medium` (no training).  
2. **Eval:** 5–10 redacted hard calls (digit spelling, refund rant) — measure WER yourself.  
3. **Only if still weak:** LoRA fine-tune on Common Voice DE **plus** your small private set.  
4. **Don’t** download terabytes “just in case” — Common Voice DE alone is already huge.

---

## Privacy

Never commit real customer recordings or full Kundennummern into git. Keep private eval/fine-tune audio outside the repo or redacted.
