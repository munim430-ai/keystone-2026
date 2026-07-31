"""Bangla text utilities for TTS-friendly output."""
from __future__ import annotations

import re

_BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

# keep: Bangla block, ASCII letters/digits, Bangla digits, common punctuation
_STRIP_RE = re.compile(
    r"[^ঀ-৿0-9A-Za-z\s০-৯।,.!?;:%\-–—'\"()৳+]"
)
_MD_RE = re.compile(r"[*_`#>\[\]{}|~]")


def to_bn_digits(text: str) -> str:
    return text.translate(_BN_DIGITS)


def sanitize_for_tts(text: str) -> str:
    """Strip markdown/emoji artifacts the LLM might emit; keep spoken Bangla."""
    text = _MD_RE.sub(" ", text)
    text = _STRIP_RE.sub(" ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return to_bn_digits(text)


_SENTENCE_RE = re.compile(r"[^।.!?]+[।.!?]?")


def split_sentences(text: str, max_len: int = 220) -> list[str]:
    """Split into sentences for incremental TTS; hard-wrap very long ones."""
    out: list[str] = []
    for m in _SENTENCE_RE.finditer(text):
        s = m.group().strip()
        if not s:
            continue
        while len(s) > max_len:
            cut = s.rfind(",", 0, max_len)
            cut = cut if cut > 40 else max_len
            out.append(s[:cut].strip())
            s = s[cut:].strip()
        if s:
            out.append(s)
    return out


_ONES = ["শূন্য", "এক", "দুই", "তিন", "চার", "পাঁচ", "ছয়", "সাত", "আট", "নয়"]


def bn_money(amount: int) -> str:
    """Small helper for round amounts used in the pitch (5000 -> পাঁচ হাজার)."""
    if amount % 1000 == 0 and 0 < amount // 1000 < 10:
        return f"{_ONES[amount // 1000]} হাজার"
    if amount % 100000 == 0 and 0 < amount // 100000 < 10:
        return f"{_ONES[amount // 100000]} লাখ"
    return to_bn_digits(f"{amount:,}")
