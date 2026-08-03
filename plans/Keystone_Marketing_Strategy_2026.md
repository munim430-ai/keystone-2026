# Keystone Education — Sniper-Targeted Marketing Strategy 2026

**Generated from** `plans/Marketing_Automation_Master_Prompt.md`
**Spine:** organic + B2B-first, near-zero-spend · **Paid:** ৳0-up ladder gated on enrolments
**Operator model:** solo/small team (Founder + Fahim) · fraud-wary tier-2 Bangla market
**Break-even anchor:** 2 enrolled students/month (৳240k)

> **How to read this:** every recommendation names the exact tool and the exact action.
> Where a number is a real business decision the founder must make, it is marked
> **⚑ FOUNDER DECISION** — those are never invented here.

---

## 0. Conflicts resolved first (these gate all public copy)

| # | Conflict | Recommended resolution |
|---|---|---|
| 1 | Public price: ৳120k milestone ladder vs ৳20k + ৳150k = ৳170k (Farhabi doc) | **Publish ONE number: the ৳120,000 flat End-to-End fee, paid after visa via the milestone ladder.** You cannot both advertise ৳120k *and* return ৳150k — the two docs describe different unit economics. Treat the stipend/soft-landing as a separately-branded **"Welcome-Back Grant" funded from tuition commission**, not a fee hike to ৳170k. **⚑ FOUNDER DECISION:** confirm the real per-student P&L (fee minus grant minus ~৳40k variable) before any campaign quotes the grant publicly. |
| 2 | "98% success / 1,500+ universities" vs strategy doc's "drop guarantee claims" | **Drop both.** They pattern-match to the exact fraud the brand attacks. Replace with verifiable claims only: "every university IEQAS-certified — check it yourself," "ApplyBoard Recruitment Partner," "founder: 9 years in Korea." |
| 3 | "Escrow" language vs legal audit (no licensed trust structure) | **Stop saying "escrow."** Say **"security deposit held in a separate business account"** — and open that business account first (client funds are currently in a personal MTB account = the single biggest legal risk). Until the account exists, do not market any money-holding promise. |

---

## 1. Growza build-vs-buy verdict

Growza sells a "360 digital marketing" retainer (ad creative, content, posting, CRM, lead-gen, WhatsApp automation, SEO, funnels). Research finding: **~90% of it is commodity plumbing you already own the stack for.** The only scarce skill is **paid-media buying** — and even that is now driveable by prompt.

| Growza service | Verdict | In-house replacement / reason |
|---|---|---|
| CRM & lead management | **Insource** | **Nationwide B2B CRM** — your primary system of record |
| Sales automation / follow-up | **Insource** | **n8n** — wire the follow-up scheduler here |
| WhatsApp automation | **Insource** | **Evolution API** (official-style; never an unofficial client) |
| Shared inbox / live chat | **Insource** | **Chatwoot** (+ native web forms) |
| Social posting/scheduling | **Insource** | **Postiz** (+ Postiz MCP), 30+ networks, official APIs |
| Ad creative (images) | **Insource** | **FastSD CPU** backgrounds + Bangla text overlaid in an editor |
| Reels/shorts + subtitles | **Insource** | **OpenShorts** + **faster-whisper** (Bangla-tuned model, human-QA) |
| Email marketing / nurture | **Insource** | **n8n** sequences |
| Landing pages / forms | **Insource** | **HeyForm/OpnForm** → n8n → NocoDB / CRM |
| SEO (local) | **Insource (light)** | Google Business Profile + Screaming Frog MCP (≤500 URLs free) |
| **Paid-media buying (Meta/Google campaign structure, audience testing, budget optimization)** | **Keep specialist — but defer** | The one genuinely scarce skill. Drive it later via **official Meta Ads MCP + Google Ads MCP**; hire a freelance media-buyer only when you're past 2 enrolments/month. |

**Recommendation: Do not hire Growza now.** You are pre-product-market-fit on volume (0.25 → 2 students/month is a *trust and pipeline* problem, not an ad-budget problem), and a paid-ads agency's output pattern-matches to the "slick Dhaka agency" your brand is built against. Spend the next 90 days standing up the in-house stack (near-zero cost) and only revisit a **single freelance media-buyer** — not a full retainer — once organic + B2B proves 2/month. If you ever engage Growza, scope it to **paid-media buying only**, never the plumbing you already own.

---

## 2. Per-persona message matrix (address all four in every campaign)

| Buyer | Core fear | Channel | Hook (Bangla → English) | Proof that converts |
|---|---|---|---|---|
| **Student (18–24)** | "Will I be stuck jobless in BD forever?" | Facebook, Reels, WhatsApp | **"IELTS ছাড়াও কোরিয়ায় পড়া যায় — আর পার্ট-টাইম কাজ করে খরচ তোলা যায়।"** ("You can study in Korea even without IELTS — and cover costs with part-time work.") | A real student Reel: campus + part-time job + "ভিসা হওয়ার পর ফি" |
| **Father (pays)** | Fraud — "will this agent take my money and vanish?" | Face-to-face, price posts, WhatsApp | **"কোনো ভিসা, কোনো ফি। ভিসা না হলে এক টাকাও নেই — লিখিত।"** ("No visa, no fee — in writing.") | Published flat ৳120k fee with **ZERO hidden fees**; bank/bKash receipt for every taka |
| **Mother (decider)** | Safety — "who looks after my child over there?" | Facebook, WhatsApp video, office visit | **"আপনার সন্তান যেখানে যাচ্ছে, আমাদের ফাউন্ডার সেখানে ৯ বছর ছিলেন।"** ("Where your child is going, our founder lived 9 years.") | Founder's Korea photos/story + the Welcome-Back Grant + soft-landing pack |
| **Uncle abroad (financier)** | Legitimacy — "is this a real, checkable business?" | Website, WhatsApp doc, video call | **"আমরা লুকাই না — আমরা শেখাই। নিজেই studyinkorea.go.kr-এ যাচাই করুন।"** ("We don't hide — we teach. Verify it yourself on studyinkorea.go.kr.") | Walk-in office address + ApplyBoard Partner badge + IEQAS-entry screenshot per university |

**Rule:** a single post can lead with one persona but must carry a second's proof in the caption (e.g. student-facing Reel + father-facing "No Visa No Fee" line pinned).

---

## 3. Channel plan (organic + B2B spine)

Reuse the existing scripts and the 7-day WhatsApp rotation — **upgrade, don't replace.**

| Channel | Play | Cadence | Who / what | Automation wired in |
|---|---|---|---|---|
| **Facebook groups** | "Help first, sell second." Answer real questions in Narsingdi/Gazipur/HSC/IELTS/Korea groups; never spam. First 3 days read-only per group. | 5 helpful comments/day | Founder (human — no auto-posting into groups; ban risk) | Leads captured → Chatwoot/CRM manually; **no group scraping** |
| **Facebook Page** | Value posts (tips, proof, whistleblower series) | 1/day (3 "hero" + 4 repurposed) | `fb_poster.py` after tokens set | **Postiz** schedules; FastSD CPU images |
| **WhatsApp status** | 7-day rotation (Mon intake → Tue bank tip → Wed IELTS → Thu mistake → Fri success → Sat "in Narsingdi Bazar today, free counselling" → Sun off) | daily 9–10 AM | Founder | pre-built in content table |
| **WhatsApp 1:1** | Qualify + nurture leads | on inbound + day0/2/5/7 | WhatsApp bot | **Evolution API + n8n** |
| **YouTube/Reels** | 1 long counselling video → many shorts | 1 long + 3 shorts/week | Founder voice | **OpenShorts + faster-whisper (Bangla)** |
| **College seminars** | "Trojan Horse" 30-min: "How to Study in Korea Without Breaking the Bank" | 1–2/week (27 Narsingdi colleges) | Founder + campus reps (৳2k/attendee-lead, ৳10k/enrolled) | QR → Form → CRM |
| **Referral program** | ৳10k per referred *enrolled* student | always-on | every enrolled student + family | CRM referral field; n8n payout reminder |
| **B2B IELTS centers** | ৳5–10k per referred enrolled student (see §6) | 15 calls/day | Founder | CRM 856+ dataset → CRM → n8n follow-up |
| **Google Business + local SEO** | Own "study in Korea Narsingdi/Gazipur" | set-and-maintain | Founder | Screaming Frog MCP audit; Umami on site |
| **Guerrilla/local** | 50 posters, 200 bus/rickshaw stickers, coaching-center mithai visits, shopkeeper info-hubs | launch bursts | Founder | none (offline) — track source in CRM |

---

## 4. Content engine — "1 long asset → many posts"

**Weekly rhythm:** Founder records **one 8–12 min counselling video** (e.g. "কোরিয়ায় IELTS ছাড়া ভর্তি — সম্পূর্ণ গাইড"). That single asset feeds the week.

**n8n workflow — `content-repurpose`:**
```
[Manual/Watch-folder trigger: new long video]
   → [faster-whisper node]  (Bangla-tuned: BanglaSpeech2Text) → transcript + timestamps
   → [Human-QA gate]        (Founder fixes Bangla caption errors — ~25%+ WER, mandatory)
   → [LLM node]             → 3 short scripts + 1 FB caption + 1 WhatsApp status + hashtags
   → [FFmpeg node]          → cut 3× 9:16 clips (OpenShorts)
   → [Subtitle burn]        → burn corrected Bangla captions
   → [FastSD CPU]           → 1 branded background for the FB hero image (text overlaid in editor)
   → [Postiz MCP]           → schedule: FB Page, Reels, YouTube Shorts (staggered)
   → [CRM/NocoDB]           → log post + source-video id for analytics
```

**Whistleblower content pillars (rotate; this IS the brand):**
1. **"5 Questions Every Student Must Ask Their Agency"** — carousel + Reel (registered? partnership agreement? total cost? what if visa rejected? talk to a past student?). Cite Financial Express; name no competitor.
2. **"Rate Your Agency" poll** — anonymous; DM every 1-star reviewer a free file-recovery offer (the Recovery Play segment).
3. **"এই ৫টি জিনিস যাচাই করুন — যেকোনো এজেন্সিতে"** poster — office + FB.
4. **Per-enrolment proof post** — admit letter + that university's IEQAS entry screenshot ("verify it yourself").
5. **"Why Keystone is cheaper (not a scam)"** — the out-economics explainer (no Dhaka rent / automation / fee-after-visa / local business).
6. **"Without IELTS"** — EAP/KLP pathway explainer (highest-intent student hook).

---

## 5. Lead funnel & automation architecture

```
INBOUND
  Facebook Page/Reels ─┐
  WhatsApp status ─────┤
  College seminar QR ──┼─► HeyForm / Chatwoot web form / (later) Meta Lead Ads
  Google Business ─────┘
        │
        ▼
   [n8n webhook]  ──►  [Nationwide CRM: Students table]  (create record, stage = Lead, source tagged)
        │
        ▼
   [Evolution API + n8n]  ── WhatsApp qualify (6-step: qualification, HSC year, DOB, country, IELTS, budget)
        │                    + day0 / day2 / day5 / day7 nurture
        ▼
   [Chatwoot]  ── human handoff to Founder (shared inbox; full lead record attached)
        │
        ▼
   COUNSELLING  (human; founder approves university match from Korea_Master_University_List)
        │
        ▼
   [audit-system/ gate]  ── documents machine-checked BEFORE submission (READY/NOT READY)
        │
        ▼
   ENROLLED  (milestone ladder billing begins; visa → fly → WeBring-side settlement)
```

---

## 6. B2B / IELTS-center engine (the 856+ center dataset)

The 856-center dataset (across 49 Bangladesh districts) is your fastest path to 2/month — one IELTS center can refer several students.

**Work-the-list playbook:**
1. **Load into CRM** as `B2B_Partners`; track: `District`, `Priority`, `Status`, `Owner`, `Last_contact`, `Referrals`, `Commission_due`.
2. **Sequence** (use the ৳5k–10k referral script):
   - Touch 1 (WhatsApp): *"আসসালামু আলাইকুম, আমি কিস্টোন এডুকেশন থেকে। আপনার স্টুডেন্টদের কেউ কোরিয়ায় পড়তে চাইলে আমরা প্রসেস করি — রেফার করলে প্রতি ভর্তি স্টুডেন্টে ৫,০০০–১০,০০০ টাকা কমিশন। কোনো রিস্ক নেই।"*
   - Touch 2 (call, +2 days): offer a free 20-min seminar at their center.
   - Touch 3 (+5 days): send the one-page commission sheet + a proof post.
3. **Target:** 15 dials/day → 300/month → even 3% signing = ~9 active referrers.

---

## 7. Paid-ads spend ladder (৳0 → up, milestone-gated)

Paid is amplification, never the engine. Each rung unlocks on a **single KPI**, run via the official Meta/Google Ads MCPs; creative comes from the content engine (§4).

| Rung | Precondition (unlock KPI) | Monthly spend | What runs | Creative source |
|---|---|---|---|---|
| **0 — Organic only** | default | ৳0 | Nothing paid | — |
| **1 — Retargeting** | ≥2 enrolled/month for **2 consecutive months** | ~৳10–15k | Meta retargeting to website + form + video viewers (warm only) | best-performing organic Reel |
| **2 — Lookalike prospecting** | Rung-1 cost-per-enrolled < ৳15k | ~৳25–40k | Meta Lead Ads to lookalikes of enrolled students; Google Search on "কোরিয়া স্টুডেন্ট ভিসা" | proven §4 assets |
| **3 — Scale + specialist** | Rung-2 stays profitable 2 months | flexible | add a freelance media-buyer; Google Ads MCP for search scaling | dedicated shoots |

---

## 8. 90-day rollout (maps to the Aug–Oct calendar)

| Week | Marketing action | Automation to stand up (priority order) |
|---|---|---|
| **Aug W1** | Google Business (Gazipur+Narsingdi); "Keystone Narsingdi is open"; join 20 groups | Deploy **Nationwide CRM**, import dataset |
| **Aug W2** | Call 50 IELTS centers from CRM dataset; book 3 college seminars; launch "Rate Your Agency" | Work CRM B2B Partners dataset; n8n B2B follow-up cadence |
| **Aug W3** | First seminar; "5 Questions" series part 1 | Deploy **Postiz** + connect FB Page; **HeyForm** inquiry form → n8n → CRM |
| **Aug W4** | Second seminar; first proof post; sign first B2B center | Stand up **content-repurpose** n8n workflow (§4); **Umami** on the site |
| **Sep W5** | Launch "Document Audit ৳2,000" + "Why Keystone is cheaper" | OpenShorts + Bangla-whisper reels pipeline live |
| **Sep W6** | "Fraud Victim Recovery" campaign; DM 1-star reviewers | Chatwoot shared inbox (Founder) |
| **Sep W7** | First video testimonial; recruit 1 campus rep | CRM referral tracking + payout reminder |
| **Sep W8** | Third seminar; announce referral program | Weekly KPI dashboard in CRM |
| **Oct W9–12** | "Without IELTS" push; October-intake urgency | Only if ≥2/month held: prep **Rung-1 retargeting** (Meta Ads MCP) |

---

## 9. Metrics & analytics

**Funnel KPIs (all in CRM), tied to break-even:**
`Leads → Qualified → Counselling booked → Enrolled` — target ratios 240 → 12 → (close 25%) → 3/month.

| Metric | Source | Target |
|---|---|---|
| Leads/week by channel | CRM `source` field | rising; know your best channel |
| Qualified rate | n8n qualification flow | ≥5% |
| Counselling→enrolled | Founder updates stage | ≥25% |
| Enrolled/month | CRM | **≥2 (survival)** |
| Cost per enrolled | spend ÷ enrolled | < ৳10k (below referral cost) |
| Website visitors → form starts | **Umami** + HeyForm | improving |

---

## 10. Risk & compliance register

| Risk | Mitigation |
|---|---|
| **WhatsApp/FB account ban** | WhatsApp only via **Evolution API**; FB/IG posting only via **official APIs (Postiz)**; never auto-post into groups |
| **Personal-bank-account exposure** | Open a **separate business account** before any money-holding promise |
| **Brand-safety on claims** | Drop "98%/1,500 universities"; never promise a visa outcome; verifiable claims only |
| **Bangla caption errors** | Mandatory human-QA gate on every auto-generated Bangla caption/subtitle |
| **AI giving visa/bank advice** | Human-only for visa and bank-balance guidance |

---

### The one-line strategy
**Win the suspicious market by being the agency that teaches suspicion** — publish the price, prove every university, return money to the student, and run the whole machine in-house so your ৳60k structural cost advantage becomes a trust advantage. Organic + B2B first; paid only after 2/month is real.
