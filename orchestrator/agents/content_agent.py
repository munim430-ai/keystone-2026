"""ContentAgent — competitor insight → DRAFT Bangla marketing copy.

Produces comparative/whistleblower draft posts into the same approval queue.
Two hard guards: (1) it only ever receives anonymized input (PII firewall),
(2) every draft passes brand-safety (no "100%/98%/1500/escrow"). It never posts
— drafts land as `pending` for the founder, and feed marketing/ugc-studio + Postiz.
"""
from __future__ import annotations

from .. import guardrails
from ..models import Draft
from ..tools import db, llm

_SYSTEM = (
    "তুমি কিস্টোন এডুকেশনের বাংলা মার্কেটিং কপিরাইটার। ব্র্যান্ড স্পাইন: 'আমরা লুকাই না — "
    "আমরা শেখাই'। একটি ছোট, সৎ, তুলনামূলক পোস্ট লেখো। নিয়ম: কোনো '১০০%/৯৮%/গ্যারান্টি/"
    "১৫০০ ইউনিভার্সিটি' দাবি নয়; প্রতিযোগীর নাম নয়; 'কোনো ভিসা, কোনো ফি' লাইন রাখো।")


def _fallback_post(insight: str) -> str:
    return ("টাকা দেওয়ার আগে যেকোনো এজেন্সিকে জিজ্ঞেস করুন — সরকারিভাবে নিবন্ধিত? "
            "ইউনিভার্সিটির চুক্তি দেখাতে পারবেন? মোট খরচ কত? আমরা লুকাই না — আমরা শেখাই।\n"
            "কোনো ভিসা, কোনো ফি। 📞 ০১৩২৮-২২৪৬০০")


def run(insight: str, name_hint: str = "", polish: bool = True) -> dict:
    # PII firewall: whatever context arrives is anonymized before use
    safe_insight = guardrails.anonymize(insight, name_hint)
    guardrails.assert_anonymized(safe_insight, name_hint)

    fallback = _fallback_post(safe_insight)
    body = llm.polish_bn(_SYSTEM, safe_insight, fallback=fallback) if polish else fallback

    # brand-safety: if the model produced a banned claim, drop to safe fallback
    if guardrails.check_claims(body):
        body = fallback
    guardrails.assert_brand_safe(body)

    d = Draft(student="", type="fb_post", body_bn=body,
              subject="Draft post (whistleblower)", meta={"source": "content_agent"})
    db.enqueue_draft(d)
    return {"draft_id": d.id, "status": d.status, "body": body}
