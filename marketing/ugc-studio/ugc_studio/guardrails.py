"""Compliance guardrails — the brand's honesty rules, enforced in code.

Keystone's entire moat is being the *trustworthy* option in a fraud-ridden
market ("আমরা লুকাই না — আমরা শেখাই"). So the studio refuses to render content
that would make it look like the agencies it attacks:

  1. No fabricated testimonials presented as a real, named student.
  2. No banned claims ("100% visa", "guaranteed", "98% success", "1500 universities").
  3. No specific taka grant/return figures until the P&L is locked (open founder decision).
  4. A synthetic presenter/voice must carry the on-screen AI-disclosure tag.
  5. Anything that would show a real student needs the consent flag set.

`check(script)` returns (errors, warnings). Errors block the render; warnings
are printed. This mirrors the "hard guardrails" in marketing/README.md.
"""
from __future__ import annotations

import re

from .brandkit import BrandKit
from .script import Script

# Case-insensitive banned-claim patterns (Bangla + English).
BANNED_PATTERNS = [
    (r"১০০%|100\s*%|শতভাগ", "absolute-guarantee claim (no one can guarantee a visa)"),
    (r"গ্যারান্টি|guarantee|guaranteed|নিশ্চিত\s*ভিসা", "visa guarantee"),
    (r"৯[৮৯]%|9[89]\s*%", "unverifiable success-rate claim (reads as fraud)"),
    (r"১৫০০|1500|১,৫০০", "the '1500 universities' claim — drop it (Strategy guardrail)"),
    (r"\bescrow\b|এস্ক্রো", "say 'security deposit in a separate business account', not escrow"),
]

# Specific-amount grant/return figures are blocked until the P&L is locked.
GRANT_MONEY_PATTERN = re.compile(
    r"(গ্রান্ট|grant|ফেরত|রিবেট|rebate|স্টাইপেন্ড|stipend|scholarship|বৃত্তি)"
)
# a taka amount in either order: "৳ 5000" / "টাকা 5000" OR "5000 টাকা"
TAKA_AMOUNT_PATTERN = re.compile(
    r"(৳\s*[০-৯0-9]|(?:টাকা|taka|tk)\s*[০-৯0-9]|[০-৯0-9][০-৯0-9,]*\s*(?:৳|টাকা|taka|tk))",
    re.IGNORECASE)


def _all_text(script: Script) -> str:
    parts = [script.hook_bn, script.cta_bn, script.caption_post_bn, script.title]
    for sc in script.scenes:
        parts.append(sc.caption_bn)
        parts.append(sc.voiceover_bn)
    return "\n".join(p for p in parts if p)


def check(script: Script, brand: BrandKit) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = _all_text(script)
    low = text.lower()

    errors.extend(script.validate_shape())

    for pattern, why in BANNED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            errors.append(f"{script.id}: banned claim — {why}")

    # grant + a taka amount in the same script → block until P&L locked
    if GRANT_MONEY_PATTERN.search(text) and TAKA_AMOUNT_PATTERN.search(text):
        errors.append(
            f"{script.id}: names a money-return/grant AND a taka figure — "
            f"do not publish amounts until per-student P&L is locked "
            f"(marketing/README.md open decision #1). Say 'money comes back', not an amount.")

    # fabricated testimonial guard
    if not brand.disclosure.get("allow_fake_testimonial", False):
        if re.search(r"testimonial|টেস্টিমোনিয়াল|আমি.*(ভিসা পেয়েছি|চলে এসেছি)", low) \
                and script.ai_presenter and not script.needs_consent:
            errors.append(
                f"{script.id}: looks like a fabricated student testimonial via an AI presenter. "
                f"Not allowed — use a consented real student (set needs_consent), or reframe "
                f"as a clearly-labelled AI *explainer*, not a fake customer.")

    # disclosure requirement for synthetic presenters
    if script.ai_presenter and brand.disclosure.get("ai_presenter_tag_bn"):
        warnings.append(
            f"{script.id}: AI presenter → the AI-disclosure tag will be burned onto the video.")

    # consent gate
    if script.needs_consent:
        warnings.append(
            f"{script.id}: needs a signed student consent on file before publishing (shows a real person).")

    # every video should carry the No-Visa-No-Fee footer somewhere
    if brand.footer_bn and brand.footer_bn[:8] not in text and not script.caption_post_bn:
        warnings.append(f"{script.id}: no explicit No-Visa-No-Fee line — the renderer will add the footer.")

    return errors, warnings
