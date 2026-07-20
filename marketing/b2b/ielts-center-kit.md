# B2B IELTS-center kit (Strategy §6)

The 859-center list (`data/IELTS_Partners_Tier2.csv`) is the fastest path to the
2-enrolled/month survival line — one center can refer several students at
৳5,000–10,000 per *enrolled* student, zero risk to them.

## ⚑ Coverage gap (act on this first)
The CSV has **0 centers in Narsingdi or Gazipur** (the home offices). It is strongest
in **Mymensingh (33), Kishoreganj (27), Tangail (13)** and nationwide. So:
1. **Build the home-district list** with `gosom/google-maps-scraper` (queries: "IELTS
   center Narsingdi", "spoken English Narsingdi", "study abroad Gazipur"). Import at
   **Priority 1** — these you can visit in person, which signs fastest.
2. Work the CSV's **nearby districts (Priority 2)** by WhatsApp + call.
3. National rows (Priority 3) = WhatsApp-only, lower effort.
4. Two malformed CSV rows carry stray characters (`한국어 학원` / stray quotes) — clean on import.

## The offer (one-pager to send)
> **কিস্টোন এডুকেশন — রেফারেল পার্টনারশিপ**
> আপনার সেন্টারের যে স্টুডেন্টরা বিদেশে পড়তে চায়, তাদের কোরিয়া/মালয়েশিয়া প্রসেসিং আমরা করি।
> • প্রতি **ভর্তি হওয়া** স্টুডেন্টে **৫,০০০–১০,০০০ টাকা** কমিশন।
> • আপনার কোনো খরচ বা রিস্ক নেই — স্টুডেন্ট ভিসা পেলে তবেই পেমেন্ট।
> • স্টুডেন্টের জন্য: কোনো ভিসা, কোনো ফি। ফাউন্ডার কোরিয়ায় ৯ বছর ছিলেন।
> 📞 01328-224600 · নিজেই যাচাই করুন: studyinkorea.go.kr

## The 3-touch sequence (reuse across the list)
- **Touch 1 — WhatsApp:** "আসসালামু আলাইকুম, আমি কিস্টোন এডুকেশন থেকে। আপনার স্টুডেন্টদের কেউ কোরিয়ায় পড়তে চাইলে আমরা প্রসেস করি — রেফার করলে প্রতি ভর্তি স্টুডেন্টে ৫,০০০–১০,০০০ টাকা কমিশন। কোনো রিস্ক নেই।"
- **Touch 2 — call (+2 days):** offer a free 20-min seminar for their students at the center.
- **Touch 3 — WhatsApp (+5 days):** send this one-pager + one proof post; ask to sign.

## Tracking (NocoDB `B2B_Partners`)
Update `Status` (new → contacted → interested → signed → dead), `Last_contact`,
`Owner`, `Referrals`, `Commission_due_bdt`. The `b2b-followup-cadence` n8n workflow
WhatsApps you the daily call-list of any contacted/interested center gone quiet >7 days.

## Targets
15 dials/day → ~300/month → even 3% signing ≈ 9 active referrers. One active referrer
sending 1 enrolled student/month = the survival line by itself.
