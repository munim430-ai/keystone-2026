# Voice Configuration & Cloning (Deliverable 4)

How the agent gets its enthusiasm, and how to upgrade to a cloned human voice
in Phase 2.

---

## The four enthusiasm layers

**Layer 1 — LLM prompt.** The persona (`brain/persona.py`) instructs the model
to write short, punchy, code-switched Bangla with natural markers ("শুনেন না",
"আচ্ছা আচ্ছা", "হাহাহা"), empathy phrases, and one question per turn. Output is
sanitized (`bn.py`) so no markdown/emoji ever reaches the voice.

**Layer 2 — TTS prosody per stage** (`brain/state_machine.py`, `PROSODY`).
Each conversation stage maps to Sarvam Bulbul pace/pitch/loudness:

| Stage | pace | pitch | loudness | feel |
|-------|------|-------|----------|------|
| Greeting | 1.05 | +0.15 | 1.25 | warm |
| **Hook** | **1.18** | **+0.25** | **1.4** | excited — highest energy |
| Qualify | 1.0 | +0.10 | 1.2 | curious |
| Pitch | 1.0 | 0 | 1.25 | confident |
| Objection | 0.92 | −0.10 | 1.1 | slow, empathetic |
| Close | 1.05 | +0.15 | 1.25 | warm |
| Wrapup | 1.0 | +0.10 | 1.2 | friendly |

**Layer 3 — pre-generated clips** (`pregen.py`). Greetings, fillers, silence
prompts, goodbyes, and high-value lines ("ওয়াও স্যার, দারুন সুযোগ!") are
synthesized once at their ideal prosody and cached to disk
(`assets/audio_cache/`). At dial time these are instant and always identical —
zero latency, zero repeated cost. The cache is content-addressed by
text+prosody+voice, so changing the voice or wording regenerates automatically.

**Layer 4 — voice cloning (this doc).** Replace the generic TTS voice with a
consistent, human, brand voice.

## Audio preprocessing

Outbound audio is peak-normalized with headroom (`audio.normalize`) so levels
are consistent across clips and providers. Everything is 8 kHz mono mu-law to
match Twilio exactly — no resampling artifacts on the wire.

---

## Phase 2: F5-TTS voice cloning on 4 GB VRAM

Goal: one recognizable Keystone voice (the operator, or a hired Bangla voice
actor) instead of a stock TTS speaker — better brand consistency and warmth.

**Why F5-TTS:** high-quality zero-/few-shot cloning that runs in ~4 GB VRAM,
which is exactly what Laptop 1 has. It's used offline to *pre-generate* audio,
not in the real-time loop, so latency isn't a concern.

### Recording the reference

- 30–60 s of clean Bangla speech from your chosen voice, warm and energetic.
- Quiet room, decent mic, 24 kHz+ WAV, no music/echo.
- Ideally include a few of the actual phrases (greeting, hook) for best match.
- Save to `voice_clone/reference.wav` (gitignored).

### Two ways to use it

1. **Batch pre-generation (recommended, safest).** Clone-synthesize the entire
   canned-phrase set + common sentence fragments offline into
   `assets/audio_cache/`. The live call then serves cloned audio for anything
   cached and falls back to Sarvam for novel sentences. Best quality where it
   matters most (the opening 30 seconds) with no runtime GPU dependency.

2. **Full runtime TTS provider.** Implement a `tts/f5_local.py` exposing the
   same `TTS.synth(text, prosody) -> mulaw_bytes` interface, running F5-TTS
   locally. Wire it into `tts/__init__.make_tts`. Only do this once you've
   benchmarked that your laptop hits the < 500 ms TTS budget — otherwise keep
   it batch-only.

### Sketch

```python
# offline, not in the call loop
from f5_tts.api import F5TTS                     # pip install f5-tts
model = F5TTS()                                  # loads to GPU (~4 GB)
wav = model.infer(ref_file="voice_clone/reference.wav",
                  ref_text="…transcript of the reference…",
                  gen_text="আসসালামু আলাইকুম! আমি মায়া, কিস্টোন এডুকেশন থেকে বলছি।")
# → resample to 8 kHz, mu-law encode (audio.pcm16_to_ulaw), write into the cache
#   at the same key make_tts uses, so the live path picks it up transparently.
```

### Guardrails

- **Consent.** Only clone a voice you own or have explicit written permission
  to use. Don't clone a real person to impersonate them.
- Keep the AI-disclosure rule regardless of how human the voice sounds — a
  better voice raises the honesty bar, it doesn't lower it.
- `voice_clone/*.wav` and `*.pt` are gitignored — never commit voice data.

This phase is **optional**. The stock Bulbul voice with Layers 1–3 is enough to
pass the Test-1 human-ness bar; clone when you want brand polish.
