# 🔴 Keystone Education Consultancy 2026 — Master Plan

**Founder:** Hasibul Munim  
**Runway:** 2–3 months  
**Status:** SURVIVAL MODE — 60-Day War Plan Active  
**Repo:** https://github.com/munim430-ai/keystone-2026

---

## 📁 Repository Structure

| File | Purpose | Who Uses It |
|---|---|---|
| `competitor-intel-report.md` | Full competitor teardown + 8 attack vectors + 8 zero-spend marketing tactics | Founder |
| `keystone-master-plan-2026.md` | The 15-part master business plan (comprehensive) | Founder |
| `keystone-reality-plan-2026.md` | **Survival edition** — forces Korea-first, stops all product builds | Founder |
| `60-day-war-plan.md` | The execution plan. Daily calendar. Laziness antidote. Accountability system. | Founder + Marina |
| `founder-daily-checklist.md` | **Printable daily checklist** — tape to your wall | Founder |
| `marina-daily-checklist.md` | **Printable daily checklist** — Marina's first 30 days | Marina |
| `scripts/ielts_scraper.py` | Scrape IELTS institutes across 64 Bangladesh districts | Founder/Fahim |
| `scripts/fb_poster.py` | AI-powered Facebook auto-poster (Hugging Face SDXL) | Founder/Fahim |
| `scripts/marina_dashboard.gs` | Google Apps Script — Marina's dashboard in Google Sheets | Founder |
| `scripts/lead_tracker_template.csv` | Ready-to-use lead tracker | Founder + Marina |
| `scripts/b2b_outreach_templates.md` | Phone scripts, SMS, college seminar pitch (Bangla + English) | Marina |
| `scripts/marina_first_week_checklist.md` | Day-by-day first week guide for Marina | Marina |
| `bots/wa_bot_marina.js` | WhatsApp bot enhancement for Marina branch | Fahim |
| `voice-agent/` | **Autonomous Bangla AI sales caller** — phones the 859-center B2B list, pitches the referral partnership, captures WhatsApp leads. Runs demo-safe with zero keys. | Founder |
| `orchestrator/` | **CEO orchestrator** — one draft-first dispatcher that turns a messy student upload into a folder, audit verdict, university match, and a Bangla missing-doc draft awaiting your approval. Wires the existing audit-system, scraper, and bots. $0, no keys. | Founder |

---

## 🧭 CEO Orchestrator (the one place it all connects)

`orchestrator/` is the thin dispatcher that wires the finished pieces —
`audit-system/`, the manifests, the IELTS scraper, the bots — into a single
**draft-first, Bangla-first** pipeline. A messy upload becomes a student folder,
a 3-state audit verdict, a ranked university match, and a warm Bangla
missing-document message **held for your approval**. It coordinates ephemeral
sub-agents (audit, matcher, instruct, scraper, content) but **never sends, posts,
or spends** — the only outbound paths are human-approved queues. Runs $0 and
offline with no API keys. A survival-clock banner shows enrolled-vs-kill-date on
every run. Start at `orchestrator/README.md` (`make demo`).

---

## 🎧 Voice Agent (the AI sales team)

`voice-agent/` is a self-contained system that solves the "no one is calling"
bottleneck: a Bangla-speaking AI that calls coaching centers via Twilio,
handles objections, captures WhatsApp numbers, and logs everything to a
dashboard — with business-hours limits, a daily cap, a kill switch, and a
hard rule that it never denies being an AI.

It ships in **demo mode** (mock STT/LLM/TTS, no real calls) so it can be
rehearsed for free, then flipped live once the 5-phase testing protocol
passes. Start at `voice-agent/README.md`.

```bash
cd voice-agent && pip install -r requirements.txt
cp .env.example .env
python -m keystone_voice.cli init-db
python -m keystone_voice.cli import-centers
python -m keystone_voice.cli console      # rehearse the brain, free
```

---

## 🚀 Quick Start (Do This Now)

### 1. Read the Survival Plan
**Start here:** `keystone-reality-plan-2026.md` — this is the only plan that matters right now.

### 2. Print Your Checklist
**Founder:** Print `founder-daily-checklist.md` — tape it to your phone/computer.  
**Marina:** Print `marina-daily-checklist.md` — keep it on her desk.

### 3. Set Up the Dashboard
1. Create new Google Sheet: "Keystone — Marina Dashboard"
2. Extensions → Apps Script
3. Paste `scripts/marina_dashboard.gs`
4. Run `initializeDashboard()`

### 4. Get Your Tokens (Tonight)
- **Hugging Face:** https://huggingface.co/settings/tokens (free, no credit card)
- **Facebook:** Refresh Page Access Token (expires every 60 days)

### 5. Make Your First 10 Calls (Tomorrow)
Use `60-day-war-plan.md` → "The First 10 Calls" section. No excuses.

---


## 🎨 Official Brand Assets

All future documents, apps, websites, and materials MUST use these official assets:

| Asset | File | Use For |
|---|---|---|
| **Logo** | `assets/keystone_logo_official.png` | Website, social media, documents, posters, business cards |
| **Founder Photo** | `assets/ceo_photo_hasibul_munim.png` | About page, company profile, B2B proposals, LinkedIn |
| **Passport** | `assets/passport_hasibul_munim.jpg` | Adventus/ApplyBoard onboarding, legal verification |
| **NID** | `assets/nid_hasibul_munim.jpg` | Trade licence, bank account, government filings |
| **TIN** | `assets/tin_certificate_hasibul_munim.jpg` | Tax compliance, corporate proposals |

**Read the full guide:** `BRAND_ASSET_GUIDE.md`

**🚫 NEVER use unofficial logos, old photos, or post legal documents on social media.**

## 🎯 The One Rule

> **No coding. No building. No new products. Until 2 students/month is steady.**

Every hour spent on software is an hour stolen from sales. Sales = survival. Software = luxury.

---

## 📞 Accountability

- **Founder:** 10 calls/day, Saturday–Thursday
- **Marina:** 5 calls/day + 1 post/day, starting Aug 1
- **Kill Criteria:** See `60-day-war-plan.md` → Kill Criteria section

---

*Compiled: 18 July 2026 | Next review: 31 August 2026*
