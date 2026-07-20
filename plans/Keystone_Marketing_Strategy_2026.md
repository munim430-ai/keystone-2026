# Keystone Education — Sniper-Targeted Marketing Strategy 2026

**Generated from** `plans/Marketing_Automation_Master_Prompt.md`
**Spine:** organic + B2B-first, near-zero-spend · **Paid:** ৳0-up ladder gated on enrolments
**Operator model:** solo/small team (Founder + Marina + Fahim) · fraud-wary tier-2 Bangla market
**Break-even anchor:** 2 enrolled students/month (৳240k)

> **How to read this:** every recommendation names the exact tool and the exact action.
> Where a number is a real business decision the founder must make, it is marked
> **⚑ FOUNDER DECISION** — those are never invented here.

---

## 0. Conflicts resolved first (these gate all public copy)

| # | Conflict | Recommended resolution |
|---|---|---|
| 1 | Public price: ৳120k milestone ladder vs ৳20k + ৳150k = ৳170k (Farhabi doc) | **Publish ONE number: the ৳120,000 flat End-to-End fee, paid after visa via the milestone ladder.** You cannot both advertise ৳120k *and* return ৳150k — the two docs describe different unit economics. Treat the stipend/soft-landing as a separately-branded **"Welcome-Back Grant" funded from tuition commission**, not a fee hike to ৳170k. **⚑ FOUNDER DECISION:** confirm the real per-student P&L (fee minus grant minus ~৳40k variable) before any campaign quotes the grant publicly. |
| 2 | "98% success / 1,500+ universities" (Marina offer page) vs strategy doc's "drop guarantee claims" | **Drop both.** They pattern-match to the exact fraud the brand attacks. Replace with verifiable claims only: "every university IEQAS-certified — check it yourself," "ApplyBoard Recruitment Partner," "founder: 9 years in Korea." **Action:** edit `marina-offer-en/docs/index.md` + `Marina-Keystone-Opportunity-EN.md` before they are used in ads. |
| 3 | "Escrow" language vs legal audit (no licensed trust structure) | **Stop saying "escrow."** Say **"security deposit held in a separate business account"** — and open that business account first (client funds are currently in a personal MTB account = the single biggest legal risk). Until the account exists, do not market any money-holding promise. |

---

## 1. Growza build-vs-buy verdict

Growza sells a "360 digital marketing" retainer (ad creative, content, posting, CRM, lead-gen, WhatsApp automation, SEO, funnels). Research finding: **~90% of it is commodity plumbing you already own the stack for.** The only scarce skill is **paid-media buying** — and even that is now driveable by prompt.

| Growza service | Verdict | In-house replacement / reason |
|---|---|---|
| CRM & lead management | **Insource** | **NocoDB** — your planned system of record |
| Sales automation / follow-up | **Insource** | **n8n** — wire the *stubbed* WhatsApp scheduler here |
| WhatsApp automation | **Insource** | **Evolution API** (official-style; never an unofficial client) |
| Shared inbox / live chat | **Insource** | **Chatwoot** (+ native web forms) |
| Social posting/scheduling | **Insource** | **Postiz** (+ Postiz MCP), 30+ networks, official APIs |
| Ad creative (images) | **Insource** | **FastSD CPU** backgrounds + Bangla text overlaid in an editor |
| Reels/shorts + subtitles | **Insource** | **OpenShorts** + **faster-whisper** (Bangla-tuned model, human-QA) |
| Email marketing / nurture | **Insource** | **n8n** sequences |
| Landing pages / forms | **Insource** | **HeyForm/OpnForm** → n8n → NocoDB |
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
| **Facebook groups** | "Help first, sell second." Answer real questions in Narsingdi/Gazipur/HSC/IELTS/Korea groups; never spam. First 3 days read-only per group. | 5 helpful comments/day | Marina (human — no auto-posting into groups; ban risk) | Leads captured → Chatwoot/NocoDB manually; **no group scraping** |
| **Facebook Page** | Value posts (tips, proof, whistleblower series) | 1/day (3 "hero" + 4 repurposed) | `fb_poster.py` after tokens set | **Postiz** schedules; FastSD CPU images |
| **WhatsApp status** | 7-day rotation (Mon intake → Tue bank tip → Wed IELTS → Thu mistake → Fri success → Sat "in Narsingdi Bazar today, free counselling" → Sun off) | daily 9–10 AM | Marina | pre-built in NocoDB content table |
| **WhatsApp 1:1** | Qualify + nurture leads | on inbound + day0/2/5/7 | `wa_bot_marina.js` | **Evolution API + n8n** (fix stubbed scheduler) |
| **YouTube/Reels** | 1 long counselling video → many shorts | 1 long + 3 shorts/week | Founder voice, Marina record | **OpenShorts + faster-whisper (Bangla)** |
| **College seminars** | "Trojan Horse" 30-min: "How to Study in Korea Without Breaking the Bank" | 1–2/week (27 Narsingdi colleges) | Marina + campus reps (৳2k/attendee-lead, ৳10k/enrolled) | QR → HeyForm → NocoDB |
| **Referral program** | ৳10k per referred *enrolled* student | always-on | every enrolled student + family | NocoDB referral field; n8n payout reminder |
| **B2B IELTS centers** | ৳5–10k per referred enrolled student (see §6) | 15 calls/day | Marina/Farhabi/Antu candidate | 859-CSV → NocoDB → n8n follow-up |
| **Google Business + local SEO** | Own "study in Korea Narsingdi/Gazipur" | set-and-maintain | Founder | Screaming Frog MCP audit; Umami on site |
| **Guerrilla/local** | 50 posters, 200 bus/rickshaw stickers, coaching-center mithai visits, shopkeeper info-hubs | launch bursts | Marina | none (offline) — track source in NocoDB |

---

## 4. Content engine — "1 long asset → many posts"

**Weekly rhythm:** Founder records **one 8–12 min counselling video** (e.g. "কোরিয়ায় IELTS ছাড়া ভর্তি — সম্পূর্ণ গাইড"). That single asset feeds the week.

**n8n workflow — `content-repurpose`:**
```
[Manual/Watch-folder trigger: new long video]
   → [faster-whisper node]  (Bangla-tuned: BanglaSpeech2Text) → transcript + timestamps
   → [Human-QA gate]        (Marina fixes Bangla caption errors — ~25%+ WER, mandatory)
   → [LLM node]             → 3 short scripts + 1 FB caption + 1 WhatsApp status + hashtags
   → [FFmpeg node]          → cut 3× 9:16 clips (OpenShorts)
   → [Subtitle burn]        → burn corrected Bangla captions
   → [FastSD CPU]           → 1 branded background for the FB hero image (text overlaid in editor)
   → [Postiz MCP]           → schedule: FB Page, Reels, YouTube Shorts (staggered)
   → [NocoDB]               → log post + source-video id for analytics
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
   [n8n webhook]  ──►  [NocoDB: Students table]  (create record, stage = Lead, source tagged)
        │
        ▼
   [Evolution API + n8n]  ── WhatsApp qualify (6-step: qualification, HSC year, DOB, country, IELTS, budget)
        │                    + day0 / day2 / day5 / day7 nurture  ⟵ FIX the stubbed scheduler
        ▼
   [Chatwoot]  ── human handoff to Marina (shared inbox; full lead record attached)
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
Every hop names its tool. The **two things that must exist before this runs:** (a) the WhatsApp follow-up cron (n8n), (b) NocoDB replacing the Google Sheet as system of record.

---

## 6. B2B / IELTS-center engine (the 859-center CSV)

The `data/IELTS_Partners_Tier2.csv` (859 rows: `Center Name, Location (District), WhatsApp/Mobile, Source URL`) is your fastest path to 2/month — one IELTS center can refer several students.

**Work-the-list playbook:**
1. **Load into NocoDB** as a `B2B_Partners` table; add columns: `Priority` (home districts first: Narsingdi, Gazipur, Mymensingh, Tangail, Kishoreganj), `Status` (new/contacted/interested/signed/dead), `Owner`, `Last_contact`, `Referrals`, `Commission_due`.
2. **Enrich only via `gosom/google-maps-scraper`** (B2B public data, rate-limited) — never scrape individuals.
3. **Sequence** (reuse the ৳5k-referral script):
   - Touch 1 (WhatsApp): *"আসসালামু আলাইকুম, আমি কিস্টোন এডুকেশন থেকে। আপনার স্টুডেন্টদের কেউ কোরিয়ায় পড়তে চাইলে আমরা প্রসেস করি — রেফার করলে প্রতি ভর্তি স্টুডেন্টে ৫,০০০–১০,০০০ টাকা কমিশন। কোনো রিস্ক নেই।"*
   - Touch 2 (call, +2 days): offer a free 20-min seminar at their center.
   - Touch 3 (+5 days): send the one-page commission sheet + a proof post.
4. **n8n cadence:** auto-reminder to `Owner` when `Last_contact` > 7 days and `Status` ∈ {contacted, interested}.
5. **Target:** 15 dials/day → 300/month → even 3% signing = ~9 active referrers.

---

## 7. Paid-ads spend ladder (৳0 → up, milestone-gated)

Paid is amplification, never the engine. Each rung unlocks on a **single KPI**, run via the official Meta/Google Ads MCPs; creative comes from the content engine (§4).

| Rung | Precondition (unlock KPI) | Monthly spend | What runs | Creative source |
|---|---|---|---|---|
| **0 — Organic only** | default | ৳0 | Nothing paid | — |
| **1 — Retargeting** | ≥2 enrolled/month for **2 consecutive months** | ~৳10–15k | Meta retargeting to website + form + video viewers (warm only) | best-performing organic Reel |
| **2 — Lookalike prospecting** | Rung-1 cost-per-enrolled < ৳15k | ~৳25–40k | Meta Lead Ads to lookalikes of enrolled students; Google Search on "কোরিয়া স্টুডেন্ট ভিসা" | proven §4 assets |
| **3 — Scale + specialist** | Rung-2 stays profitable 2 months | flexible | add a freelance media-buyer; Google Ads MCP for search scaling | dedicated shoots |

**⚑ FOUNDER DECISION:** the exact cost-per-enrolled ceiling. Rule of thumb: paid is only sane while cost-per-enrolled < the ৳10k referral cost isn't beaten — i.e. keep paid *below* your organic/referral efficiency or don't scale it.

---

## 8. 90-day rollout (maps to the Aug–Oct calendar)

**Do the two ~2-hour fixes first — they unblock everything:**
- **Fix A:** set `HF_API_TOKEN` + `FB_PAGE_TOKEN` in `bots/fb_poster.py` → auto-posting works.
- **Fix B:** wire the `wa_bot_marina.js` day0/2/5/7 follow-up into an **n8n cron** (replace the `console.log` stub) → no lead goes cold.

| Week | Marketing action | Automation to stand up (priority order) |
|---|---|---|
| **Aug W1** | Google Business (Gazipur+Narsingdi); "Keystone Narsingdi is open"; join 20 groups | **Fix A + Fix B**; deploy **NocoDB**, import the Google Sheet |
| **Aug W2** | Call 50 IELTS centers from the CSV; book 3 college seminars; launch "Rate Your Agency" | Load 859-CSV → NocoDB `B2B_Partners`; n8n B2B follow-up cadence |
| **Aug W3** | First seminar; "5 Questions" series part 1 | Deploy **Postiz** + connect FB Page; **HeyForm** inquiry form → n8n → NocoDB |
| **Aug W4** | Second seminar; first proof post; sign first B2B center | Stand up **content-repurpose** n8n workflow (§4); **Umami** on the site |
| **Sep W5** | Launch "Document Audit ৳2,000" + "Why Keystone is cheaper" | OpenShorts + Bangla-whisper reels pipeline live |
| **Sep W6** | "Fraud Victim Recovery" campaign; DM 1-star reviewers | Chatwoot shared inbox (Marina + founder) |
| **Sep W7** | First video testimonial; recruit 1 campus rep | NocoDB referral tracking + n8n payout reminder |
| **Sep W8** | Third seminar; announce referral program | Weekly KPI dashboard in NocoDB (§9) |
| **Oct W9–12** | "Without IELTS" push; Mymensingh expansion; October-intake urgency | Only if ≥2/month held: prep **Rung-1 retargeting** (Meta Ads MCP) |

---

## 9. Metrics & analytics

**Funnel KPIs (all in NocoDB, one row per lead), tied to break-even:**
`Leads → Qualified → Counselling booked → Enrolled` — target ratios 240 → 12 → (close 25%) → 3/month.

| Metric | Source | Target |
|---|---|---|
| Leads/week by channel | NocoDB `source` field | rising; know your best channel |
| Qualified rate | n8n qualification flow | ≥5% |
| Counselling→enrolled | Marina updates stage | ≥25% |
| Enrolled/month | NocoDB | **≥2 (survival)** |
| Cost per enrolled | spend ÷ enrolled | < ৳10k (below referral cost) |
| Website visitors → form starts | **Umami** + HeyForm | improving |

**Weekly review ritual (Sunday, 30 min):** open the NocoDB dashboard + Umami; read leads-by-source, qualified rate, enrolments; decide next week's content focus and which channel to double down on. One number rules the week: **enrolments-to-date vs the 2/month line.**

---

## 10. Risk & compliance register

| Risk | Mitigation |
|---|---|
| **WhatsApp/FB account ban** (unofficial automation) | WhatsApp only via **Evolution API**; FB/IG posting only via **official APIs (Postiz)**; never auto-post into groups (human only) |
| **Student-PII / privacy / ToS** | No scraping of students or FB groups. Acquire via inbound (content + official Meta Lead Ads + forms). Maps-scraper for **B2B institutes only**, rate-limited |
| **Personal-bank-account / "escrow" legal exposure** | Open a **separate business account** before any money-holding promise; say "security deposit in a separate business account," never "escrow"; stop commingling client funds |
| **Brand-safety on claims** | Drop "98%/1,500 universities"; never promise a visa outcome; verifiable claims only (IEQAS, ApplyBoard, 9-years-Korea) |
| **Bangla caption errors** | Mandatory human-QA gate on every auto-generated Bangla caption/subtitle (base Whisper WER 25%+) |
| **AI giving visa/bank advice** | Human-only for visa and bank-balance guidance — no bot, no RAG (already killed for liability) |
| **Grant math unproven** | ⚑ Confirm per-student P&L before marketing the Welcome-Back Grant publicly (Conflict #1) |

---

### The one-line strategy
**Win the suspicious market by being the agency that teaches suspicion** — publish the price, prove every university, return money to the student, and run the whole machine in-house so your ৳60k structural cost advantage becomes a trust advantage. Organic + B2B first; paid only after 2/month is real.
