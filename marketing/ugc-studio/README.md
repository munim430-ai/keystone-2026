# Keystone UGC Studio 🎬

Turn short Bangla scripts into publish-ready **9:16 Reels** for Keystone's
Korea-study marketing. The CPU path runs **today** — no GPU, no API keys, $0 —
and produces a real `.mp4` + a ready-to-post caption. Optional GPU adapters add a
cloned Bangla voice, a labelled AI presenter, and generated b-roll.

It feeds the marketing stack that already exists here (`marketing/n8n`
`content-repurpose` → **Postiz** → Facebook/Instagram).

- **Strategy & the 5 niche angles:** [UGC_STRATEGY.md](UGC_STRATEGY.md)
- **Verified GitHub tools (with the XTTS-Bengali trap):** [TOOLS.md](TOOLS.md)
- **20 ready prompts (human-readable):** [PROMPTS.md](PROMPTS.md) · (machine: `scripts.yaml`)

---

## Quick start (CPU, no keys)

```bash
cd marketing/ugc-studio
pip install -r requirements.txt          # Pillow, PyYAML, python-dotenv, httpx
# system deps: apt install ffmpeg fonts-noto-core fonts-beng   (Bengali font)

python -m ugc_studio.cli doctor          # check ffmpeg / fonts / brand assets
python -m ugc_studio.cli list            # the 20 scripts + guardrail status
python -m ugc_studio.cli lint            # compliance gate (must be 0 errors)
python -m ugc_studio.cli render --id s01-without-ielts   # → out/s01-without-ielts.mp4
python -m ugc_studio.cli render          # render all 20
```

Each render writes:
- `out/<id>.mp4` — the 9:16 video (brand chrome, Ken-Burns, burned-in Bangla
  captions, No-Visa-No-Fee footer, verify URL).
- `out/<id>.caption.txt` — the social caption + footer + hashtags, ready for Postiz.

## Add a real Bangla voice (optional)

- **Easiest:** set `SARVAM_API_KEY` in `.env` (`UGC_TTS_PROVIDER=sarvam`) — same
  cloud voice as the phone agent, no GPU.
- **Cloned brand voice (GPU box):** install AI4Bharat IndicF5, point
  `UGC_INDICF5_REF_WAV` at a 20s clean Bangla clip. One voice across video + calls.
- **Zero-key offline:** `UGC_TTS_PROVIDER=mms` (Meta MMS, CPU, robotic).

With no TTS set, the video carries a silent audio track — add voiceover in your
editor, or just publish caption-only (many top Bangla Reels are caption-only).

## Add a talking-head presenter (optional, GPU)

Set `UGC_AVATAR_PROVIDER=sadtalker` (or `wav2lip`) and point it at a cloned repo
(see TOOLS.md). Only scripts marked `ai_presenter: true` use it, and the renderer
**burns an on-screen "AI presenter" tag** — because we never fake a real student.

## How it's built

```
ugc_studio/
  brandkit.py     brand colours/fonts/assets/footer  (brandkit.yaml)
  script.py       the Script/Scene model (a UGC video is a small spec)
  guardrails.py   compliance gate: no "100% visa", no fake testimonials, no
                  taka grant amounts until P&L locked, AI-disclosure + consent
  captions.py     Bangla word-wrap + mixed Bangla/Latin (URL!) rendering
  render.py       CPU renderer: stills + Ken Burns + captions + audio → mp4
  tts/            sarvam (cloud) · indicf5 · parler · mms · silent
  avatar/         sadtalker · wav2lip adapters (shell out on GPU box)
  pipeline.py     script → guardrails → voice → visuals → mp4 + caption
  cli.py          doctor · list · lint · render
scripts.yaml      the 20 prompts as render specs
```

## Guardrails are not optional

`lint` (and every `render`) runs `ugc_studio/guardrails.py`, which **blocks**:
- "১০০% / গ্যারান্টি / ৯৮%" and "1500 universities" claims (fraud signals),
- the word "escrow" (say "security deposit in a separate business account"),
- any grant/return named **with a taka amount** (until the P&L is locked —
  `marketing/README.md` open decision #1),
- a fabricated AI testimonial posing as a real student.

And it **requires** an on-screen AI tag for synthetic presenters and a consent
flag for anything showing a real person. This is the brand's honesty, in code.

## Tests

```bash
python -m pytest -q      # guardrails, script/caption, the 20-script invariants
```
