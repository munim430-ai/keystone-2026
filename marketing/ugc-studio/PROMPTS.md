# 20 ready-to-use 10-second Bangla UGC prompts

Complete, copy-paste prompts for 10-second Keystone Reels — mapped to a buyer
persona, an angle, and a tool. The machine-readable versions live in
`scripts.yaml`; render any of them with `python -m ugc_studio.cli render --id <id>`.

Three ways to use each prompt:
- **A) This studio (CPU, $0):** already encoded in `scripts.yaml` — just render.
- **B) Avatar/voice (GPU):** feed the *voiceover* line to IndicF5/Sarvam, the photo
  to SadTalker/Wav2Lip.
- **C) Generated b-roll (rented GPU/Replicate):** use the *b-roll prompt* given for
  the aspirational ones.

Every video auto-carries: `কোনো ভিসা, কোনো ফি। ভিসা না হলে এক টাকাও নেই।` +
`📍 নারসিংদি বাজার · গাজীপুর · 📞 ০১৩২৮-২২৪৬০০` + `যাচাই করুন: studyinkorea.go.kr`.

> Guardrails block "১০০%/গ্যারান্টি/৯৮%", "1500 universities", "escrow", any taka
> grant amount, and fake testimonials. Run `ugc-studio lint` before publishing.

---

## STUDENT (Facebook/Reels — adventure, no-IELTS)

**1. `s01-without-ielts` — No-IELTS hook** *(faceless kinetic captions)*
> Hook: **IELTS নাই? কোরিয়া তবুও সম্ভব।**
> Script: "IELTS নাই বলে থেমে আছেন? → কোরিয়ার EAP প্রোগ্রামে IELTS ছাড়াই ভর্তি হওয়া যায়। → IELTS থাকলে টিউশন মওকুফের সুযোগও আছে। → প্রোফাইল পাঠান — কোন পথটা আপনার, বলে দিই।"
> b-roll prompt: *"vertical 9:16, a hopeful Bangladeshi student closing a laptop showing a Korean university page, warm light, 3s"*

**2. `s02-day-in-life` — Day-in-the-life** *(b-roll montage)*
> Hook: **সকাল ৭টা, সিউল।**
> Script: "সকাল: ক্লাস। → বিকেল: পার্ট-টাইম কাজ, সপ্তাহে ২০ ঘণ্টা বৈধ। → রাত: বন্ধুদের সাথে, নিজের খরচ নিজে। → এটা স্বপ্ন না — একটা প্ল্যান।"
> b-roll prompt: *"cinematic vertical 9:16 montage — a Bangladeshi student in a Seoul campus at sunrise, a part-time café shift, evening with friends, hopeful, 3 clips of 3s"*

**3. `s03-myth-vs-fact` — Myth vs fact** *(belief flip)*
> Hook: **কোরিয়া নিয়ে সবচেয়ে বড় ভুল ধারণা।**
> Script: "মিথ: কোরিয়া মানে শুধু বড়লোকের ছেলেমেয়ে। → সত্য: টিয়ার-২ শহরের HSC পাশ স্টুডেন্টরাই বেশি যাচ্ছে। → দরকার সঠিক গাইডলাইন — আর সৎ একটা এজেন্সি।"

**4. `s04-checklist` — Document checklist** *(save-worthy, faceless)*
> Hook: **কোরিয়া D-2 ভিসার ডকুমেন্ট চেকলিস্ট।**
> Script: "৫টি জিনিস আজই গোছান → পাসপোর্ট · সার্টিফিকেট · ব্যাংক স্টেটমেন্ট → SOP · স্পনসরের কাগজ → একটাও ভুল হলে ৬ মাস পিছিয়ে যাবেন।"

**5. `s05-before-after` — Before vs after** *(transformation)*
> Hook: **এক বছরে জীবনটা বদলে যেতে পারে।**
> Script: "আগে: HSC পাশ, কী করবো জানি না। → এখন: কোরিয়ার ইউনিভার্সিটিতে, নিজের খরচ নিজে। → পার্থক্য শুধু একটা সিদ্ধান্ত — আর সঠিক গাইড।"

## FATHER (price, ROI, transparency)

**6. `f01-price-transparency` — Radical price transparency**
> Hook: **মোট খরচ কত? সোজা উত্তর দিই।**
> Script: "অন্যরা বলে 'পরে জানাবো'। → আমরা বলি: এক ফি, কোনো লুকানো খরচ নেই। → আর পুরো ফি — ভিসা হওয়ার পরে। → কারণ আমরা লুকাই না — আমরা শেখাই।"

**7. `f02-why-cheaper` — Why cheaper, not a scam**
> Hook: **এত কম কেন? সন্দেহ হচ্ছে?**
> Script: "ঢাকার দামি অফিসের ভাড়া নেই — আমরা আপনার শহরে। → ডকুমেন্ট চেকিং অটোমেশনে — তাই খরচ কম। → সস্তা মানে দুর্বল নয় — সস্তা মানে দক্ষ।"

**8. `f03-5-questions` — 5 questions to ask any agency**
> Hook: **টাকা দেওয়ার আগে এই ৫টা প্রশ্ন করুন।**
> Script: "১. সরকারিভাবে নিবন্ধিত? → ২. ইউনিভার্সিটি চুক্তি দেখাতে পারবেন? → ৩. মোট খরচ কত — লুকানো ফি সহ? → ৪. ভিসা রিজেক্ট হলে? ৫. আগের স্টুডেন্টের সাথে কথা?"
> (Cite Financial Express, May 2026. Name no competitor.)

**9. `f04-roi` — Cost or investment?**
> Hook: **এটা খরচ না — বিনিয়োগ।**
> Script: "কোরিয়ায় বৈধ পার্ট-টাইম: সপ্তাহে ২০ ঘণ্টা। → ছেলে-মেয়ে নিজের খরচ নিজে চালাতে পারে। → সঠিক ইউনিভার্সিটি বাছাই — সেটাই আসল কাজ।"

## MOTHER (safety, care, contact)

**10. `m01-safety` — A mother's first worry** *(no taka figures — guardrail)*
> Hook: **সন্তান বিদেশে — নিরাপদ থাকবে তো?**
> Script: "মায়ের প্রথম চিন্তা: ও ঠিক থাকবে তো? → পৌঁছানোর দিন সফট-ল্যান্ডিং সাপোর্ট। → প্রথম মাসগুলোতে পাশে থাকি। → টাকা ফেরতও আসে — বিস্তারিত অফিসে।"

**11. `m02-local-face` — Right here in Narsingdi** *(Marina, consent required)*
> Hook: **ঢাকা নয় — আপনার নারসিংদিতেই।**
> Script: "দূরের অচেনা অফিস নয়। → নারসিংদি বাজারে আমাদের অফিস — গিয়ে দেখুন। → লোকাল মানুষ, লোকাল নাম্বার, সামনাসামনি কথা।"

**12. `m03-contact` — Someone to look after my child**
> Hook: **কোরিয়ায় কেউ কি ওকে দেখবে?**
> Script: "পৌঁছেই একা হয়ে যাবে না। → সিম, ট্রান্সপোর্ট কার্ড, থাকার ব্যবস্থা — গোছানো। → প্রশ্ন থাকলে যেকোনো সময় WhatsApp।"

## UNCLE / financier (legitimacy, proof)

**13. `u01-verify-yourself` — Don't believe us, verify** *(screen-rec studyinkorea.go.kr)*
> Hook: **আমাদের কথা বিশ্বাস করবেন না।**
> Script: "আমাদের কথা বিশ্বাস করবেন না। → সরকারি সাইটে নিজে যাচাই করুন। → ইউনিভার্সিটি IEQAS সার্টিফায়েড কিনা — studyinkorea.go.kr"
> **This is the format that replaces a fake testimonial.**

**14. `u02-fee-after-visa` — No visa, no fee amplified**
> Hook: **আগে টাকা চাইলে — সাবধান।**
> Script: "অনেকে আগে ১ লাখ নেয়, তারপর উধাও। → আমরা পুরো ফি নিই ভিসার পরে। → ভিসা না হলে এক টাকাও নয়।"

**15. `u03-fraud-recovery` — Fraud-victim recovery**
> Hook: **আগের এজেন্সি টাকা নিয়ে কিছু করেনি?**
> Script: "লাখ টাকা দিয়ে ফাইল আটকে আছে? → আপনার ফাইল আমরা ফ্রি অডিট করে দেব। → বাঁচানো গেলে বাঁচাই — না গেলে সৎ কথা বলি।"

**16. `u04-proof-post` — Per-enrolment proof** *(admit letter + IEQAS, consent required)*
> Hook: **আরেকজন স্টুডেন্টের অ্যাডমিশন নিশ্চিত।**
> Script: "আরেকজন কোরিয়ার ইউনিভার্সিটিতে ভর্তি নিশ্চিত। → নিচে অ্যাডমিট লেটার + IEQAS স্ক্রিনশট। → নাম শুধু অনুমতি নিয়ে — প্রমাণ সবসময়।"

## AI-PRESENTER format (clearly labelled — honest UGC)

**17. `p01-ai-explainer` — AI presenter: Korea in 3 steps** *(talking head, GPU)*
> Hook: **কোরিয়া যাওয়ার পুরো প্রসেস — ৩ ধাপে।**
> Script: "ধাপ ১: প্রোফাইল + ইউনিভার্সিটি বাছাই। → ধাপ ২: ডকুমেন্ট + অ্যাডমিশন। → ধাপ ৩: ভিসা — তারপরই আমাদের ফি।"
> Avatar+voice: SadTalker(founder photo) + IndicF5. On-screen AI tag auto-added.

**18. `p02-ai-faq` — AI presenter: common questions** *(talking head, GPU)*
> Hook: **সবচেয়ে বেশি যে ৩টা প্রশ্ন পাই।**
> Script: "IELTS লাগবেই? — না, EAP আছে। → টাকা কখন? — ভিসার পরে। → ভিসা শিওর বলে দেন? — কেউ পারে না, সৎভাবে বলি।"

## B2B (IELTS-center owners, colleges — pairs with the voice-agent)

**19. `b01-ielts-partner` — Partnership offer to center owners**
> Hook: **IELTS সেন্টার চালান? এক্সট্রা ইনকাম।**
> Script: "আপনার স্টুডেন্টরা বিদেশমুখী। → প্রতি এনরোল হওয়া স্টুডেন্টে কমিশন। → কোনো আপফ্রন্ট ফি নেই — পেমেন্ট এনরোলমেন্টের পরে।"

**20. `b02-seminar` — Free college seminar hook**
> Hook: **কলেজে ফ্রি সেমিনার — 'IELTS ছাড়াই কোরিয়া'।**
> Script: "আপনার কলেজে ফ্রি ৩০ মিনিটের সেমিনার। → কোনো বিক্রি নয় — শুধু গাইডলাইন। → আমরা সব ম্যাটেরিয়াল নিয়ে আসি।"

---

### Reusable prompt template (for any LLM drafting new scripts)

```
You are Keystone Education's Bangla UGC scriptwriter. Brand spine:
"আমরা লুকাই না — আমরা শেখাই". Write a 10-second Reel (3–4 scenes, one Bangla
caption per scene, ~2.5s each) targeting the [STUDENT/FATHER/MOTHER/UNCLE] buyer,
angle = [ANGLE]. Rules: warm tier-2 Bangla; one idea per scene; end on a CTA;
NEVER claim "100%/গ্যারান্টি/৯৮%" or "1500 universities"; never invent a taka
grant amount; never fake a named student. Output as a scripts.yaml block.
```
