# Posting calendar — WhatsApp status + FB weekly rhythm (Strategy §3)

## Daily WhatsApp status — 7-day rotation (post 9–10 AM)
| Day | Status (Bangla) |
|---|---|
| Mon | 🎓 কোরিয়ার বিশ্ববিদ্যালয়ে ভর্তি চলছে! আসন সীমিত — আজই যোগাযোগ করুন। |
| Tue | 📋 আজকের টিপ: কোরিয়ার ভিসার জন্য ব্যাংক স্টেটমেন্টে কত লাগে? আঞ্চলিক বিশ্ববিদ্যালয়ে অনেক কম। |
| Wed | 💪 IELTS নেই? EAP-তে IELTS ছাড়াই সুযোগ। থাকলে স্কলারশিপ। |
| Thu | 🚨 সাধারণ ভুল: ডকুমেন্টে স্বাক্ষর/নাম মিল না থাকলে ভিসা রিজেক্ট। আমরা আগেই চেক করি। |
| Fri | 🌟 সাকসেস স্টোরি: আরেকজন কোরিয়ায় ভর্তি নিশ্চিত! (proof post) |
| Sat | 📍 আজ নারসিংদি বাজারে আছি — ফ্রি কাউন্সেলিং। চা খেতে খেতে কথা বলি। |
| Sun | OFF — কমেন্ট/DM-এ রেসপন্স করুন। |

## Facebook Page — weekly plan (1 post/day; Postiz-scheduled)
| Day | Post type (fb_poster.py `--post-type`) | Pillar |
|---|---|---|
| Mon | korea_tip | intake / general |
| Tue | document_guide | check_5_things |
| Wed | ielts | without_ielts |
| Thu | korea_tip / 5_questions carousel | 5_questions |
| Fri | success_story | proof |
| Sat | ielts / why_cheaper | why_cheaper |
| Sun | — | community engagement |

**Weekly hero:** one 8–12 min founder video → `content-repurpose` n8n workflow → 3
Reels + captions across the week. **Every Bangla caption gets a human-QA pass** before
it publishes (base Whisper Bangla WER ~25%+).

## Guardrails (do not violate)
- Post to the **Page** via Postiz/official API. **Never auto-post into Facebook
  groups** — human only (ban risk). Groups are for helpful comments, not blasts.
- No student PII in any post without written consent.
- Never "100% visa guarantee." Never "98% / 1,500 universities."
