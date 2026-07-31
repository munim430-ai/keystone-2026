"""Bangla caption rendering with PIL: word-wrap, panels, brand chrome.

Bengali needs a shaping-aware font (Noto Sans Bengali). PIL's basic layout
handles Bengali conjuncts acceptably for short captions at large sizes, which
is exactly the UGC use case (a few big words, not paragraphs).
"""
from __future__ import annotations

import re
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920  # 9:16 vertical

# Bengali Unicode block; everything else (Latin, URL, digits-ASCII, "·", ":")
# is drawn with a Latin-capable font so it doesn't tofu.
_BENGALI = re.compile(r"[ঀ-৿]")

# Emoji / symbol ranges that our burned-in fonts can't render — strip them from
# on-screen text (they stay in the social caption file, where the platform renders them).
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002190-\U000021FF"
    "\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F\U0001F1E6-\U0001F1FF]"
)


def strip_emoji(text: str) -> str:
    return re.sub(r"\s+", " ", _EMOJI.sub("", text)).strip()


@lru_cache(maxsize=64)
def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def _runs(text: str):
    """Split text into (segment, is_bengali) runs for per-script font choice."""
    out = []
    cur, cur_bn = "", None
    for ch in text:
        bn = bool(_BENGALI.match(ch))
        if ch == " " and cur:          # keep spaces with the current run
            cur += ch
            continue
        if cur_bn is None or bn == cur_bn:
            cur += ch
            cur_bn = bn
        else:
            out.append((cur, cur_bn))
            cur, cur_bn = ch, bn
    if cur:
        out.append((cur, cur_bn))
    return out


def draw_mixed_center(draw, center_x, y, text, bn_font, latin_font, fill,
                      stroke=0, stroke_fill=(0, 0, 0)):
    """Draw a single centered line that mixes Bengali and Latin/URL text."""
    text = strip_emoji(text)
    runs = _runs(text)
    widths = [(bn_font if bn else latin_font).getlength(seg) for seg, bn in runs]
    total = sum(widths)
    x = center_x - total / 2
    for (seg, bn), w in zip(runs, widths):
        f = bn_font if bn else latin_font
        draw.text((x, y), seg, font=f, fill=fill, anchor="lm",
                  stroke_width=stroke, stroke_fill=stroke_fill)
        x += w


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def wrap(text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    """Greedy word-wrap by pixel width (works for Bangla space-separated words)."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = (cur + " " + w).strip()
        if fnt.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_multiline(draw: ImageDraw.ImageDraw, xy, lines, fnt, fill,
                   line_gap=1.25, anchor="ma", stroke=0, stroke_fill=(0, 0, 0)):
    x, y = xy
    lh = int(fnt.size * line_gap)
    for i, ln in enumerate(lines):
        draw.text((x, y + i * lh), ln, font=fnt, fill=fill, anchor=anchor,
                  stroke_width=stroke, stroke_fill=stroke_fill)
    return y + len(lines) * lh


def rounded_panel(img: Image.Image, box, radius=36, fill=(15, 24, 48), opacity=205):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.rounded_rectangle(box, radius=radius, fill=(*fill, opacity))
    img.alpha_composite(overlay)


def gradient_scrim(img: Image.Image, top_alpha=40, bottom_alpha=190):
    """Dark gradient bottom-up so captions stay legible over any photo."""
    grad = Image.new("L", (1, H), 0)
    for y in range(H):
        t = y / H
        grad.putpixel((0, y), int(top_alpha + (bottom_alpha - top_alpha) * (t ** 1.6)))
    alpha = grad.resize((W, H))
    black = Image.new("RGBA", (W, H), (5, 8, 18, 0))
    black.putalpha(alpha)
    img.alpha_composite(black)
