"""Guardrails — the master plan's hard rules, enforced in code, not comments.

These are asserted at runtime and covered by tests. If a future change tries to
give an agent a send/spend tool, or leak a student's name to the marketing
agent, or auto-pass a claim the brand banned, these fail loudly.
"""
from __future__ import annotations

import datetime as dt
import re

# ── 1. Survival clock (keystone-reality-plan-2026.md kill criteria) ──────────
# Dates the founder is racing. The CEO loop prints this so the machine never
# lets him forget the clock.
KILL_DATES = [
    (dt.date(2026, 8, 31), 1, "Zero enrolled by 31 Aug → shut down or pivot to pure B2B"),
    (dt.date(2026, 9, 30), 2, "Fewer than 2 total enrolled by 30 Sep → the market said no"),
    (dt.date(2026, 12, 31), 6, "Fewer than 6 total enrolled by 31 Dec → a hobby, not a business"),
]


def survival_status(enrolled_total: int, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    nxt = next((k for k in KILL_DATES if k[0] >= today), KILL_DATES[-1])
    deadline, need, rule = nxt
    days = (deadline - today).days
    ok = enrolled_total >= need
    return {
        "today": today.isoformat(),
        "enrolled_total": enrolled_total,
        "next_deadline": deadline.isoformat(),
        "days_left": days,
        "need_by_then": need,
        "on_track": ok,
        "rule": rule,
        "banner": (f"SURVIVAL: {enrolled_total} enrolled · "
                   f"need {need} by {deadline.isoformat()} ({days}d) · "
                   f"{'ON TRACK' if ok else '⚠ BEHIND — SELL'}"),
    }


# ── 2. Draft-first: no agent may hold a send/post/spend tool ─────────────────
_FORBIDDEN_TOOL = re.compile(r"(send|post|publish|pay|charge|spend|dial|call_now)", re.I)


def assert_no_send_tools(tool_names) -> None:
    bad = [t for t in tool_names if _FORBIDDEN_TOOL.search(t)]
    if bad:
        raise AssertionError(f"draft-first violation: agent exposed send/spend tools {bad}")


# ── 3. PII firewall: what leaves the student folder is anonymized ────────────
_PHONE = re.compile(r"(\+?880|0)1[0-9\-\s]{8,}")
_PASSPORT = re.compile(r"\b[A-Z]{1,2}\d{6,9}\b")
_NID = re.compile(r"\b\d{10,17}\b")


def anonymize(text: str, name: str = "") -> str:
    """Strip identifiers before text reaches marketing/cross-agent contexts.
    Name → initials, phone/passport/NID → redacted."""
    out = text or ""
    if name:
        initials = "".join(w[0].upper() for w in name.split() if w) or "X"
        out = re.sub(re.escape(name), f"[Student {initials}]", out, flags=re.I)
    out = _PHONE.sub("[phone]", out)
    out = _PASSPORT.sub("[passport]", out)
    out = _NID.sub("[id]", out)
    return out


def assert_anonymized(text: str, name: str = "") -> None:
    if name and re.search(re.escape(name), text, re.I):
        raise AssertionError("PII firewall: student name present in marketing-bound text")
    if _PHONE.search(text) or _PASSPORT.search(text):
        raise AssertionError("PII firewall: phone/passport present in marketing-bound text")


# ── 4. Banned claims (anti-fraud brand honesty) ─────────────────────────────
BANNED_CLAIMS = [
    (re.compile(r"১০০%|100\s*%|শতভাগ|guarantee|গ্যারান্টি"), "no visa/outcome guarantee"),
    (re.compile(r"৯[৮৯]%|9[89]\s*%"), "no unverifiable success-rate claim (drop 98%)"),
    (re.compile(r"১৫০০|1500|1,500"), "drop the '1500 universities' claim"),
    (re.compile(r"\bescrow\b|এস্ক্রো"), "say 'security deposit in a separate business account', not escrow"),
]


def check_claims(text: str) -> list[str]:
    return [why for pat, why in BANNED_CLAIMS if pat.search(text or "")]


def assert_brand_safe(text: str) -> None:
    bad = check_claims(text)
    if bad:
        raise AssertionError(f"brand-safety violation: {bad}")


# ── 5. No AI visa/bank advice — instruction scope is checklist status only ───
_ADVICE = re.compile(
    r"(ভিসা\s*(পাবেন|হবে|নিশ্চিত)|ব্যাংকে\s*কত\s*টাকা\s*রাখ|guaranteed visa|"
    r"you will get the visa|deposit .* amount)", re.I)


def is_document_checklist_scope(text: str) -> bool:
    """True if the text stays within 'which document is missing/needs fixing'
    and does NOT stray into visa-outcome or bank-balance advice (human-only)."""
    return not bool(_ADVICE.search(text or ""))
