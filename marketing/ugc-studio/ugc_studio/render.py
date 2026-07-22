"""CPU-only video renderer: Script -> 9:16 .mp4. No GPU, no API keys.

Pipeline per scene:
  background (brand colour or brand photo, Ken-Burns zoom) → gradient scrim →
  brand chrome (logo, handle) → caption panel + wrapped Bangla text →
  footer (No-Visa-No-Fee + contact + verify) → optional AI-disclosure tag.

Frames are written as PNGs and muxed by ffmpeg. Audio (a voiceover .wav from a
TTS provider, or a music bed) is mixed in if provided; otherwise the clip is
silent and ready for a voiceover in the editor.
"""
from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from .brandkit import BrandKit
from .captions import (H, W, draw_mixed_center, draw_multiline, font,
                       gradient_scrim, _hex, rounded_panel, strip_emoji, wrap)
from .script import Scene, Script

FPS = 24


def _load_cover(path: str) -> Image.Image:
    """Load an image and crop-cover to a slightly-larger canvas for Ken Burns."""
    img = Image.open(path).convert("RGBA")
    scale = max(W * 1.15 / img.width, H * 1.15 / img.height)
    img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    return img


def _solid(color: tuple[int, int, int]) -> Image.Image:
    # subtle vertical brand gradient instead of a flat fill
    base = Image.new("RGBA", (W, H), (*color, 255))
    top = Image.new("RGBA", (W, H), (min(color[0] + 30, 255),
                                     min(color[1] + 30, 255),
                                     min(color[2] + 30, 255), 255))
    mask = Image.new("L", (1, H))
    for y in range(H):
        mask.putpixel((0, y), int(120 * (1 - y / H)))
    base.paste(top, (0, 0), mask.resize((W, H)))
    return base


def _resolve_background(scene: Scene, brand: BrandKit) -> tuple[str, Image.Image | None]:
    """Return (kind, image). kind is 'photo' or 'color'."""
    bg = scene.background
    # explicit file path?
    if Path(bg).exists():
        return "photo", _load_cover(bg)
    # brand asset key?
    asset = brand.asset(bg)
    if asset:
        return "photo", _load_cover(asset)
    # brand colour key?
    if bg in brand.colors:
        return "color", _solid(_hex(brand.color(bg)))
    # a raw hex?
    if bg.startswith("#"):
        return "color", _solid(_hex(bg))
    return "color", _solid(_hex(brand.color("brand_blue", "#1b3a8b")))


def _ken_burns(src: Image.Image, t: float, dur: float) -> Image.Image:
    """Crop a W×H window from the oversized source, drifting/zooming over time."""
    prog = t / max(dur, 0.01)
    zoom = 1.0 + 0.06 * prog                     # slow push-in
    cw, ch = int(W / zoom), int(H / zoom)
    max_x = max(0, src.width - cw)
    max_y = max(0, src.height - ch)
    x = int(max_x * (0.5 + 0.15 * math.sin(prog * math.pi)))
    y = int(max_y * (0.35 + 0.10 * prog))
    win = src.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)
    return win.convert("RGBA")


def _logo(brand: BrandKit) -> Image.Image | None:
    p = brand.asset("logo")
    if not p:
        return None
    logo = Image.open(p).convert("RGBA")
    lw = 190
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    return logo


def _draw_frame(scene: Scene, brand: BrandKit, t: float, script: Script,
                logo: Image.Image | None) -> Image.Image:
    kind, bg = _resolve_background(scene, brand)
    frame = _ken_burns(bg, t, scene.seconds) if kind == "photo" else bg.copy()
    gradient_scrim(frame, top_alpha=30, bottom_alpha=170)

    draw = ImageDraw.Draw(frame)
    fb = brand.fonts["bengali_bold"]
    fr = brand.fonts["bengali_regular"]
    flat = brand.fonts["latin"]

    # top chrome: logo + handle (handle is Latin → Latin font)
    if logo is not None:
        frame.alpha_composite(logo, (54, 70))
    draw.text((W - 54, 96), brand.handle, font=font(flat, 32),
              fill=(255, 255, 255), anchor="rm", stroke_width=2, stroke_fill=(0, 0, 0))

    # caption block (lower third), on a rounded panel
    cap_size = 96 if scene.emphasis else 74
    cap_color = _hex(brand.color("gold")) if scene.emphasis else (255, 255, 255)
    fcap = font(fb, cap_size)
    lines = wrap(scene.caption_bn, fcap, W - 200)
    line_h = int(cap_size * 1.25)
    block_h = line_h * len(lines)
    cap_top = H - 560 - block_h
    rounded_panel(frame, (60, cap_top - 46, W - 60, cap_top + block_h + 40),
                  radius=40, fill=_hex(brand.color("panel", "#0f1830")), opacity=190)
    draw_multiline(draw, (W // 2, cap_top), lines, fcap, cap_color,
                   anchor="ma", stroke=3, stroke_fill=(0, 0, 0))

    # footer: No-Visa-No-Fee (pure Bangla) + contact + verify (both mixed-script)
    fy = H - 300
    draw_multiline(draw, (W // 2, fy), wrap(strip_emoji(brand.footer_bn), font(fb, 44), W - 140),
                   font(fb, 44), _hex(brand.color("gold")), anchor="ma",
                   stroke=3, stroke_fill=(0, 0, 0))
    draw_mixed_center(draw, W // 2, H - 176, brand.contact_bn, font(fr, 34), font(flat, 30),
                      (255, 255, 255), stroke=2)
    draw_mixed_center(draw, W // 2, H - 120, brand.verify_bn, font(fr, 32), font(flat, 30),
                      (210, 225, 255), stroke=2)

    # AI-disclosure tag (only for synthetic-presenter scripts) — Bangla, emoji stripped
    if script.ai_presenter and brand.disclosure.get("ai_presenter_tag_bn"):
        tag = strip_emoji(brand.disclosure["ai_presenter_tag_bn"])
        draw_multiline(draw, (W // 2, 150), wrap(tag, font(fr, 30), W - 160),
                       font(fr, 30), (255, 255, 255), anchor="ma",
                       stroke=2, stroke_fill=(0, 0, 0))
    return frame


def render(script: Script, brand: BrandKit, out_path: str,
           audio_path: str | None = None, fps: int = FPS) -> dict:
    """Render the script to out_path (.mp4). Returns render metadata."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg not found on PATH")
    logo = _logo(brand)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    tmp = Path(tempfile.mkdtemp(prefix="ugc_"))
    frame_idx = 0
    try:
        for scene in script.scenes:
            n = max(1, int(round(scene.seconds * fps)))
            for i in range(n):
                t = i / fps
                fr = _draw_frame(scene, brand, t, script, logo).convert("RGB")
                fr.save(tmp / f"f{frame_idx:05d}.png")
                frame_idx += 1

        cmd = ["ffmpeg", "-y", "-framerate", str(fps),
               "-i", str(tmp / "f%05d.png")]
        if audio_path and Path(audio_path).exists():
            cmd += ["-i", audio_path, "-c:a", "aac", "-b:a", "128k", "-shortest"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                "-movflags", "+faststart", str(out)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {proc.stderr[-800:]}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    size = out.stat().st_size if out.exists() else 0
    return {
        "output": str(out),
        "frames": frame_idx,
        "seconds": script.total_seconds,
        "fps": fps,
        "bytes": size,
        "has_audio": bool(audio_path and Path(audio_path).exists()),
    }
