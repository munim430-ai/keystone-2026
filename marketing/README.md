# Keystone Marketing Machine

The in-house implementation of `plans/Keystone_Marketing_Strategy_2026.md` — an
organic + B2B-first marketing system that replaces ~90% of a full-service agency on a
CPU-only VPS at $0 license cost. Brand spine: **আমরা লুকাই না — আমরা শেখাই
(We don't hide — we teach).**

## What's here
```
marketing/
  README.md                     # this file
  deploy/
    docker-compose.yml          # NocoDB + n8n + Postiz + Umami + Chatwoot
    .env.example                # every token/secret to fill (real .env is gitignored)
    RUNBOOK.md                  # day-1 fixes → week-1 stack, step by step
  nocodb/
    schema.md                   # Students / B2B_Partners / Content / Referrals tables
    seed_b2b_from_csv.py        # load the 859-center list (verified: 859 rows)
  n8n/
    whatsapp-followup.json      # Fix B — drain the day0/2/5/7 queue hourly
    lead-intake.json            # form/Meta-Lead-Ads → NocoDB → enqueue follow-ups
    b2b-followup-cadence.json   # daily "who's gone quiet >7d" call list
    content-repurpose.json      # 1 long video → 3 reels + captions → Postiz
  content/
    whistleblower-pillars.md    # 6 ready-to-post Bangla content pillars
    posting-calendar.md         # 7-day WhatsApp rotation + FB weekly plan
  b2b/
    ielts-center-kit.md         # offer one-pager + 3-touch sequence + coverage gap
  ugc-studio/                   # AI UGC video studio → source Reels for content-repurpose → Postiz
    README.md · UGC_STRATEGY.md · TOOLS.md · PROMPTS.md · scripts.yaml (20 prompts)
```

## AI UGC video (ugc-studio/)

`ugc-studio/` turns short Bangla scripts into publish-ready 9:16 Reels. The CPU
path runs today ($0, no GPU, no keys): brand chrome + Ken-Burns + burned-in Bangla
captions + the No-Visa-No-Fee footer + a verifiable `studyinkorea.go.kr` line, plus
a ready-to-post caption for Postiz. Optional GPU adapters add a cloned Bangla voice
(AI4Bharat IndicF5), a **labelled** AI presenter (SadTalker/Wav2Lip), and rented
b-roll. Ships 20 ready prompts across all four buyer personas. Compliance guardrails
block fake testimonials, "100% visa"/"98%" claims, and unlocked taka grant figures.
Start at `ugc-studio/README.md`.
Plus, at repo root:
- `bots/followup_scheduler.js` — **Fix B**, the real day0/2/5/7 sender (Evolution API). Verified end-to-end.
- `bots/wa_bot_marina.js` — now enqueues follow-ups instead of the old `console.log` stub.
- `bots/fb_poster.py` — **Fix A**: set `HF_API_TOKEN` + `FB_PAGE_TOKEN` and it posts.

## Start here
Follow `deploy/RUNBOOK.md`. Do the two ~2-hour fixes first (they pay off immediately),
then bring up the stack in week 1.

## Founder decisions still open (⚑ do not auto-resolve)
1. **Per-student P&L / the public grant numbers** — you cannot advertise ৳120k *and*
   return ৳150k. Lock the real economics before any post quotes a grant amount.
2. **Open a separate business account** before marketing any money-holding promise;
   say "security deposit in a separate business account," never "escrow."
3. **Home-district B2B list** — the 859-center CSV has **0 Narsingdi/Gazipur** centers;
   build that list via `gosom/google-maps-scraper` (see `b2b/ielts-center-kit.md`).

## Hard guardrails (baked into every workflow)
- WhatsApp only via **Evolution API**; FB/IG posting only via **Postiz** official APIs. No unofficial clients (ban risk).
- Maps-scraping for **B2B institutes only**; never scrape student PII or Facebook groups.
- **Human-QA every Bangla caption** before publish (base Whisper Bangla WER ~25%+).
- No AI gives visa/bank advice. No "100% visa," no "98% / 1,500 universities" claims.
