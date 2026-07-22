# AI UGC toolchain — GitHub tools, verified (2026-07)

Same honesty rule as `plans/open-source-stack-research.md`: recommend only what
this 2–3-person team can actually run, be explicit about the **4GB-VRAM limit**,
and flag the traps. Star counts/status checked live 2026-07-21.

**The single most important finding:** the tool everyone reaches for — **Coqui
XTTS-v2 — does NOT support Bengali** (17 languages, `bn` not among them), and the
original `coqui-ai/TTS` repo is archived. If you clone XTTS for Bangla you will
waste a day. The real open-source Bangla answer is **AI4Bharat** (below).

---

## Category 1 — AI voice (Bangla TTS / voice cloning)

| Tool | Repo | Bangla? | Runs on | Verdict |
|------|------|---------|---------|---------|
| **AI4Bharat IndicF5** | github.com/AI4Bharat/IndicF5 | ✅ native | GPU (4GB ok, batch) | ✅ **PICK for a cloned brand voice.** F5-TTS family; clone one "Keystone voice" from a 20s reference clip, reuse it across video *and* the phone agent. |
| **AI4Bharat Indic Parler-TTS** | hf.co/ai4bharat/indic-parler-tts | ✅ native | GPU | ✅ **PICK for controllable emotion.** Describe the voice in words ("young woman, warm, energetic") — no reference clip needed. Great for varying enthusiasm per script. |
| **Meta MMS-TTS (ben)** | hf.co/facebook/mms-tts-ben | ✅ | **CPU ok** | ✅ Lightweight fallback — robotic but zero-GPU, fully offline. |
| **Sarvam Bulbul** | api.sarvam.ai (cloud) | ✅ best | any (API) | ✅ **Easiest + best quality.** Paid per-char, no GPU. Already wired into the voice-agent, so the brand voice matches the phone calls. |
| ~~Coqui XTTS-v2~~ | ~~coqui-ai/TTS~~ | ❌ **no bn** | — | ❌ **Do not use for Bangla.** Archived repo; maintained fork is `idiap/coqui-ai-TTS` but still no Bengali. |

> 1-line use case: *Clone one warm Bangla "Keystone voice" with IndicF5 and use it
> for every Reel voiceover and every phone call — one recognizable brand voice.*
> Sample IndicF5 prompt (ref-audio + text): `ref="maya_ref.wav"`,
> `text="আসসালামু আলাইকুম! IELTS ছাড়াই কোরিয়ায় পড়া যায় — কীভাবে, বলছি।"`

## Category 2 — AI avatar / talking head

| Tool | Repo | Runs on | Verdict |
|------|------|---------|---------|
| **Wav2Lip** | github.com/Rudrabha/Wav2Lip | ~4GB VRAM ✅ | ✅ **The only one comfortable on your 4GB laptop.** Lip-only (no head motion), lower realism — fine for a brand-mascot presenter over a static Keystone frame. |
| **SadTalker** | github.com/OpenTalker/SadTalker | ~6–8GB (borderline 4GB) | ✅ **PICK if you can rent a GPU.** One photo + audio → head motion + lip sync. Best "single still → presenter" workflow. |
| **MuseTalk 1.5** | github.com/TMElyralab/MuseTalk | 8GB+ | ⚠️ 2026 best quality, real-time — but needs a driving video and more VRAM. Rent an hourly GPU for a batch, don't buy hardware. |

> 1-line use case: *Turn the founder's brand photo into a labelled AI presenter that
> explains "Korea in 3 steps" — never a fake student.*
> Sample: `python inference.py --face keystone_presenter.png --audio step3.wav` (Wav2Lip).

⚠️ **Honesty rule (enforced in `ugc_studio/guardrails.py`):** an avatar may only
drive an `ai_presenter` script, which burns an on-screen "🤖 এই ভিডিওর উপস্থাপক
একটি AI" tag. **Never** generate a synthetic person and present them as a real,
named student — for an anti-fraud brand that is the one move that detonates trust.

## Category 3 — Text-to-video / b-roll

| Tool | Repo | Runs on | Verdict |
|------|------|---------|---------|
| **AnimateDiff** | github.com/guoyww/AnimateDiff | 8–12GB VRAM | ⚠️ Apache-2.0, oldest arch. Won't run on 4GB. |
| **LTX-Video** | github.com/Lightricks/LTX-Video | 8GB+ (fp8) | ✅ Fastest local option if you get a bigger GPU. |
| **Wan 2.1/2.2** | github.com/Wan-Video/Wan2.1 | 12GB+ (small variants) | ✅ Best mid-tier quality; Apache-2.0. |
| Hosted (Replicate/Fal) | replicate.com | cloud | ✅ **PRACTICAL PICK.** On 4GB VRAM, generated b-roll is the one category to **rent, not run** — pay per clip, no install. |

> **Verdict for Keystone:** you do **not** need generated b-roll to start. Real,
> verifiable footage (screen-recording `studyinkorea.go.kr`, an admit letter, the
> Narsingdi office, stock Korea clips) out-converts generated dreamscapes for a
> *trust* brand, and it's free. Reach for text-to-video only for aspirational
> "day-in-Korea" montages, and rent the GPU when you do.
> Sample prompt: *"cinematic vertical 9:16, a Bangladeshi student walking through a
> snowy Seoul university campus at golden hour, backpack, hopeful, 3 seconds"*.

## Category 4 — Editing / automation glue

| Tool | Repo / where | Verdict |
|------|--------------|---------|
| **This studio (`ugc_studio`)** | here | ✅ Assembles captions + Ken Burns + audio → 9:16 mp4 on **CPU**, today. Built on Pillow + ffmpeg. |
| **ffmpeg** | ffmpeg.org | ✅ The actual muxing/encoding engine. `apt install ffmpeg`. |
| **Whisper (faster-whisper)** | github.com/SYSTRAN/faster-whisper | ✅ Auto-caption a talking video (Bangla WER ~25%+, so **human-QA every caption** — same rule as marketing/README.md). |
| **Postiz** | github.com/gitroomhq/postiz-app | ✅ Already in `marketing/deploy` — schedules the finished Reel to FB/IG via official APIs. The studio writes a `.caption.txt` ready for it. |
| **n8n `content-repurpose`** | `marketing/n8n/content-repurpose.json` | ✅ Already here — 1 long video → 3 reels + captions → Postiz. The studio feeds source clips into it. |
| ~~MoviePy~~ | | ⚠️ Fine, but we render via Pillow+ffmpeg directly to avoid its version churn. Installed as a convenience only. |

---

## Where this fits the existing stack

```
ugc_studio (CPU: captions+KenBurns+voice → 9:16 mp4 + caption.txt)
        │            ▲ optional: IndicF5 voice · SadTalker avatar · rented b-roll
        ▼
n8n content-repurpose ──► Postiz ──► Facebook / Instagram / YouTube Shorts
        ▲
NocoDB `Content` table (schedule, status)   ·   human-QA gate before publish
```

Nothing new to deploy for the **CPU path** — it runs from this folder. The GPU
pieces (IndicF5/avatar) live on the founder's laptop and are optional upgrades.
